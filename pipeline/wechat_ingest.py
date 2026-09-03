from __future__ import annotations

import argparse
import re
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from rapidocr import RapidOCR

from common import canonical_url, iso_now, normalize_text, read_json, title_key, write_json
from crawl import (
    BEIJING,
    in_window,
    next_lecture_number,
    normalize_confidence,
    update_usage,
    write_review_issue,
)
from llm import extract_event, verify_api
from policy import apply_region, route

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/131 Safari/537.36"
)
IMAGE_URL = re.compile(r"https?://[^\s)>\"]+", re.I)


def issue_sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", body, re.M))
    values: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        value = body[match.end() : end].strip()
        values[match.group(1).strip()] = "" if value == "_No response_" else value
    return values


def fetch_article(url: str) -> tuple[str, list[str]]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(8, 30))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = ""
    meta = soup.select_one('meta[property="og:title"]')
    if meta:
        title = normalize_text(meta.get("content", ""))
    account = normalize_text((soup.select_one("#js_name") or soup.new_tag("span")).get_text(" "))
    published = normalize_text(
        (soup.select_one("#publish_time") or soup.new_tag("span")).get_text(" ")
    )
    content = soup.select_one("#js_content") or soup
    images: list[str] = []
    for image in content.select("img"):
        candidate = image.get("data-src") or image.get("src") or ""
        candidate = canonical_url(urljoin(url, candidate))
        if candidate.startswith("http") and candidate not in images:
            images.append(candidate)
    for node in content(["script", "style", "noscript", "svg"]):
        node.decompose()
    text = normalize_text(content.get_text(" "))
    metadata = normalize_text(f"文章标题：{title} 公众号：{account} 发布时间：{published}")
    return normalize_text(f"{metadata} {text}"), images[:12]


def issue_image_urls(body: str) -> list[str]:
    urls = []
    for url in IMAGE_URL.findall(body):
        cleaned = url.rstrip(".,，。")
        if any(host in cleaned for host in ("githubusercontent.com", "github.com/user-attachments")):
            urls.append(cleaned)
    return list(dict.fromkeys(urls))


def ocr_images(urls: list[str]) -> str:
    if not urls:
        return ""
    engine = RapidOCR()
    chunks: list[str] = []
    for index, url in enumerate(urls[:12], start=1):
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(8, 30))
            response.raise_for_status()
            suffix = Path(url.split("?", 1)[0]).suffix or ".jpg"
            with tempfile.NamedTemporaryFile(suffix=suffix) as image_file:
                image_file.write(response.content)
                image_file.flush()
                result = engine(image_file.name)
            texts = getattr(result, "txts", None)
            if texts is None and isinstance(result, tuple) and result:
                rows = result[0] or []
                texts = [row[1] for row in rows if len(row) > 1]
            if texts:
                chunks.append(f"图片{index} OCR：{' '.join(str(text) for text in texts)}")
        except Exception as exc:
            print(f"WARN OCR {url}: {exc}", flush=True)
    return normalize_text(" ".join(chunks))


def ingest(body: str, issue_url: str, days: int = 14) -> None:
    values = issue_sections(body)
    submitted_urls = values.get("公众号文章链接", "").split()
    article_url = canonical_url(submitted_urls[0]) if submitted_urls else ""
    if not article_url.startswith("https://mp.weixin.qq.com/"):
        raise SystemExit("请提供 mp.weixin.qq.com 文章链接")
    source_name = values.get("公众号名称") or "公众号文章提交"
    supplied = normalize_text(
        " ".join(
            values.get(key, "")
            for key in ("文章标题和发布日期", "补充文字或说明", "文章截图")
        )
    )
    article_text = ""
    images = issue_image_urls(body)
    try:
        article_text, article_images = fetch_article(article_url)
        images = list(dict.fromkeys(article_images + images))
    except requests.RequestException as exc:
        print(f"WARN 微信正文直接访问失败，将使用提交内容和截图：{exc}", flush=True)
    ocr_text = ocr_images(images)
    analysis_text = normalize_text(f"{supplied} {article_text} {ocr_text}")
    if len(analysis_text) < 40:
        raise SystemExit("无法读取文章正文；请在 Issue 附上文章截图或补充文字")

    sources = read_json("sources.json", [])
    source = next(
        (
            item
            for item in sources
            if item.get("kind") == "wechat"
            and (item.get("name") == source_name or canonical_url(item.get("url", "")) == article_url)
        ),
        {
            "id": "wechat-submission",
            "name": source_name,
            "tier": 3,
            "kind": "wechat",
        },
    )
    verify_api()
    item, usage = extract_event(source_name, article_url, analysis_text, images)
    update_usage(usage["input"], usage["output"])
    item["confidence"] = normalize_confidence(item.get("confidence"))
    apply_region(item, source)
    batch_date = datetime.now(BEIJING).strftime("%Y-%m-%d")
    candidates = read_json("candidates.json", [])
    lectures = read_json("lectures.json", [])
    decisions = read_json("decisions.json", [])
    if not item.get("isEvent") or not in_window(item, days):
        print("文章中没有未来 14 天内可确认的活动", flush=True)
        write_review_issue(candidates, 10, batch_date)
        return
    known_urls = {canonical_url(value.get("sourceUrl", "")) for value in candidates + lectures}
    known_events = {
        f"{title_key(value.get('title', ''))}|{value.get('startAt', '')[:10]}"
        for value in candidates + lectures
    }
    event_key = f"{title_key(item.get('title', ''))}|{item.get('startAt', '')[:10]}"
    if article_url in known_urls or event_key in known_events:
        print("该讲座已经存在", flush=True)
        write_review_issue(candidates, 10, batch_date)
        return
    status, note = route(item, source)
    if status == "rejected":
        print(f"公众号讲座未通过规则预筛：{note}", flush=True)
        write_review_issue(candidates, 10, batch_date)
        return
    item.update(
        {
            "id": f"L{next_lecture_number(candidates, lectures, decisions):03d}",
            "status": status,
            "sourceName": source_name,
            "sourceUrl": article_url,
            "verifiedAt": iso_now(),
            "discoveredAt": iso_now(),
            "discoveredOn": batch_date,
            "reviewNotes": f"{note}；公众号图片 OCR 导入",
            "submissionUrl": issue_url,
        }
    )
    item.pop("isEvent", None)
    candidates.append(item)
    candidates.sort(key=lambda value: value.get("startAt", ""))
    write_json("candidates.json", candidates)
    write_review_issue(candidates, 10, batch_date)
    print(f"新增公众号候选 {item['id']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--body", required=True)
    parser.add_argument("--issue-url", required=True)
    parser.add_argument("--days", type=int, default=14)
    args = parser.parse_args()
    ingest(args.body, args.issue_url, args.days)
