from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from dateutil.parser import isoparse

from common import DATA, canonical_url, iso_now, normalize_text, read_json, stable_id, title_key, write_json
from glm import API_URL, MODEL, GLMAPIError, api_key, extract_event, verify_api
from policy import route

BEIJING = timezone(timedelta(hours=8))
LINK_WORDS = re.compile(
    r"讲座|报告|论坛|seminar|lecture|talk|colloquium|预告|学术活动|workshop|school",
    re.I,
)
REVIEW_WORDS = re.compile(r"回顾|纪要|侧记|review|活动总结", re.I)
DATE_HINT = re.compile(
    r"20\d{2}|\d{1,2}[月./-]\d{1,2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec",
    re.I,
)
USER_AGENT = "pku-lectures/0.1 (+https://github.com/wangzi2006/pku-lectures)"


def fetch(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(5, 20))
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    return normalize_text(soup.get_text(" "))


def page_images(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    images: list[str] = []
    for image in soup.select("img[src]"):
        source = image.get("src", "")
        context = " ".join(
            [source, image.get("alt", ""), image.get("title", ""), image.get("class", [""])[0]]
        ).lower()
        if any(word in context for word in ("logo", "icon", "avatar", "banner", "qrcode", "二维码")):
            continue
        url = canonical_url(urljoin(page_url, source))
        if url.startswith("http") and url not in images:
            images.append(url)
    return images[:3]


def candidate_links(source: dict[str, Any], html: str, limit: int = 18) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    host = urlsplit(source["url"]).netloc
    scored: list[tuple[int, str]] = []
    for anchor in soup.select("a[href]"):
        label = normalize_text(anchor.get_text(" "))
        url = canonical_url(urljoin(source["url"], anchor.get("href", "")))
        if not url.startswith("http") or urlsplit(url).netloc != host:
            continue
        combined = f"{label} {url}"
        if REVIEW_WORDS.search(combined) and source.get("reviewMining"):
            continue
        score = 2 if LINK_WORDS.search(combined) else 0
        score += 1 if DATE_HINT.search(combined) else 0
        if score == 0 and 8 <= len(label) <= 160 and len(urlsplit(url).path.strip("/")) >= 5:
            score = 1
        if score:
            scored.append((score, url))
    return [url for _, url in sorted(set(scored), reverse=True)[:limit]]


def in_window(item: dict[str, Any], days: int) -> bool:
    try:
        start = isoparse(item["startAt"])
    except (KeyError, TypeError, ValueError):
        return False
    now = datetime.now(BEIJING)
    return now <= start <= now + timedelta(days=days)


def update_usage(input_tokens: int, output_tokens: int) -> None:
    usage = read_json("usage.json", {})
    month = datetime.now(BEIJING).strftime("%Y-%m")
    if usage.get("month") != month:
        usage = {"month": month, "inputTokens": 0, "outputTokens": 0, "estimatedCny": 0}
    usage["inputTokens"] = int(usage.get("inputTokens", 0)) + input_tokens
    usage["outputTokens"] = int(usage.get("outputTokens", 0)) + output_tokens
    input_price = float(os.getenv("AI_INPUT_CNY_PER_MILLION", "0"))
    output_price = float(os.getenv("AI_OUTPUT_CNY_PER_MILLION", "0"))
    usage["estimatedCny"] = round(
        (usage["inputTokens"] * input_price + usage["outputTokens"] * output_price)
        / 1_000_000,
        4,
    )
    usage["lastUpdatedAt"] = iso_now()
    write_json("usage.json", usage)


def budget_allows_ai() -> bool:
    usage = read_json("usage.json", {})
    return float(usage.get("estimatedCny", 0)) < float(os.getenv("AI_HARD_BUDGET_CNY", "45"))


def crawl(days: int, max_review: int) -> None:
    sources = [item for item in read_json("sources.json", []) if item.get("enabled")]
    candidates = read_json("candidates.json", [])
    published = read_json("lectures.json", [])
    known_urls = {canonical_url(item["sourceUrl"]) for item in candidates + published}
    known_events = {
        f"{title_key(item.get('title', ''))}|{item.get('startAt', '')[:10]}"
        for item in candidates + published
    }
    new_items: list[dict[str, Any]] = []
    tokens = {"input": 0, "output": 0}
    api_calls = 0
    max_api_calls = int(os.getenv("MAX_AI_CALLS", str(max(4, min(30, max_review * 3)))))
    consecutive_api_failures = 0

    if not api_key():
        print("未配置 BIGMODEL_API_KEY/ZAI_API_KEY；保留现有候选并跳过 AI 抽取。", flush=True)
        write_review_issue(candidates, max_review)
        return
    if not budget_allows_ai():
        print("已达到 AI 硬预算，跳过抽取。", flush=True)
        write_review_issue(candidates, max_review)
        return

    print(f"校验智谱 API：{API_URL}，模型：{MODEL}", flush=True)
    verify_api()
    print(f"API 校验通过；本次最多分析 {max_api_calls} 个页面。", flush=True)

    for source_index, source in enumerate(sources, start=1):
        if api_calls >= max_api_calls:
            break
        if source.get("kind") == "review-archive":
            continue
        print(f"[{source_index}/{len(sources)}] 抓取来源：{source['name']}", flush=True)
        try:
            listing = fetch(source["url"])
        except requests.RequestException as exc:
            print(f"WARN 来源页 {source['name']}：{exc}", flush=True)
            continue
        for url in candidate_links(source, listing):
            if api_calls >= max_api_calls:
                print(f"已达到本次 API 调用上限 {max_api_calls}，停止分析新页面。", flush=True)
                break
            if url in known_urls or len(new_items) >= max_review * 3:
                continue
            try:
                html = fetch(url)
                text = page_text(html)
                if len(text) < 120 or not (LINK_WORDS.search(text) and DATE_HINT.search(text)):
                    continue
            except requests.RequestException as exc:
                print(f"WARN 页面抓取 {url}：{exc}", flush=True)
                continue

            api_calls += 1
            print(f"  AI 分析 {api_calls}/{max_api_calls}：{url}", flush=True)
            try:
                item, call_usage = extract_event(source["name"], url, text, page_images(html, url))
                tokens["input"] += call_usage["input"]
                tokens["output"] += call_usage["output"]
                consecutive_api_failures = 0
            except GLMAPIError as exc:
                print(f"WARN AI 分析 {url}：{exc}", flush=True)
                if exc.fatal:
                    raise
                consecutive_api_failures += 1
                if consecutive_api_failures >= 3:
                    raise RuntimeError("智谱 API 连续失败 3 次，提前停止以避免长时间等待") from exc
                continue
            if not item.get("isEvent") or not in_window(item, days):
                continue
            event_key = f"{title_key(item.get('title', ''))}|{item.get('startAt', '')[:10]}"
            if event_key in known_events:
                continue
            status, note = route(item, source)
            if status == "rejected":
                continue
            item.update(
                {
                    "id": stable_id("L", f"{url}|{item.get('startAt')}"),
                    "status": status,
                    "sourceName": source["name"],
                    "sourceUrl": url,
                    "verifiedAt": iso_now(),
                    "reviewNotes": note,
                }
            )
            item.pop("isEvent", None)
            new_items.append(item)
            known_urls.add(url)
            known_events.add(event_key)

    update_usage(tokens["input"], tokens["output"])
    merged = sorted(candidates + new_items, key=lambda item: item.get("startAt", ""))
    write_json("candidates.json", merged)
    write_review_issue(merged, max_review)
    print(
        f"完成：分析 {api_calls} 个页面，新增 {len(new_items)} 条，候选共 {len(merged)} 条。",
        flush=True,
    )


def write_review_issue(candidates: list[dict[str, Any]], max_review: int) -> None:
    pending = [item for item in candidates if item.get("status") in {"pending", "maybe"}][:max_review]
    lines = [
        f"## 每日讲座审核 · {datetime.now(BEIJING):%Y-%m-%d}",
        "",
        f"本次最多展示 {max_review} 条。请直接在 Issue 中评论：",
        "",
        "```text",
        "收录：L001 L002",
        "拒绝：L003",
        "待定：L004",
        "```",
        "",
    ]
    for item in pending:
        lines.extend(
            [
                f"### {item['id']} · {item.get('titleZh') or item.get('title')}",
                f"- 时间：{item.get('startAt', '待核验')}",
                f"- 讲者：{item.get('speaker', '待核验')}",
                f"- 地点：{item.get('location', '待核验')}（{item.get('campus', '待核验')}）",
                f"- 标签：{', '.join(item.get('subtopics', []))}",
                f"- 简介：{item.get('summary', '')}",
                f"- 值得听：{item.get('reason', '')}",
                f"- 机器判断：{item.get('reviewNotes', '')}；置信度 {item.get('confidence', '—')}",
                f"- [原始来源]({item.get('sourceUrl')})",
                "",
            ]
        )
    if not pending:
        lines.append("今天没有待审核的新条目。")
    (DATA / "review-issue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--max-review", type=int, default=10)
    args = parser.parse_args()
    crawl(args.days, args.max_review)
