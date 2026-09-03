from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from common import DATA, canonical_url, iso_now, next_numbered_id, normalize_text, read_json, write_json

REVIEW_WORDS = re.compile(r"讲座回顾|活动回顾|学术回顾|纪要|侧记|review", re.I)
ANNOUNCE_WORDS = re.compile(r"预告|报名|讲座|论坛|系列|主办|承办|公众号", re.I)
USER_AGENT = "pku-lectures/0.1 (+https://github.com/wangzi2006/pku-lectures)"


def discover() -> None:
    sources: list[dict[str, Any]] = read_json("sources.json", [])
    suggestions: list[dict[str, Any]] = read_json("source-suggestions.json", [])
    known = {canonical_url(item["url"]) for item in sources}
    known.update(canonical_url(item["candidateUrl"]) for item in suggestions)
    added = 0

    for source in sources:
        if not source.get("enabled") or not source.get("reviewMining"):
            continue
        try:
            response = requests.get(source["url"], headers={"User-Agent": USER_AGENT}, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"WARN review listing {source['name']}: {exc}")
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        host = urlsplit(source["url"]).netloc
        reviews: list[str] = []
        for anchor in soup.select("a[href]"):
            label = normalize_text(anchor.get_text(" "))
            if REVIEW_WORDS.search(label):
                url = canonical_url(urljoin(source["url"], anchor.get("href", "")))
                if urlsplit(url).netloc == host:
                    reviews.append(url)

        for review_url in reviews[:8]:
            try:
                detail = requests.get(review_url, headers={"User-Agent": USER_AGENT}, timeout=30)
                detail.raise_for_status()
            except requests.RequestException:
                continue
            detail_soup = BeautifulSoup(detail.text, "html.parser")
            detail_text = normalize_text(detail_soup.get_text(" "))
            for anchor in detail_soup.select("a[href]"):
                label = normalize_text(anchor.get_text(" "))
                candidate = canonical_url(urljoin(review_url, anchor.get("href", "")))
                if candidate in known or not candidate.startswith("http"):
                    continue
                context = normalize_text(f"{label} {anchor.parent.get_text(' ') if anchor.parent else ''}")
                if not ANNOUNCE_WORDS.search(context):
                    continue
                suggestions.append(
                    {
                        "id": next_numbered_id("S", sources, suggestions),
                        "status": "pending",
                        "name": label or "从讲座回顾发现的预告渠道",
                        "candidateUrl": candidate,
                        "discoveredFrom": review_url,
                        "parentSource": source["name"],
                        "evidence": context[:300],
                        "discoveredAt": iso_now(),
                        "notes": "请核验该链接是否稳定发布未来讲座预告；通过后再加入 sources.json。",
                    }
                )
                known.add(candidate)
                added += 1

    write_json("source-suggestions.json", suggestions)
    write_issue(suggestions)
    print(f"Added {added} source suggestions from lecture reviews.")


def write_issue(suggestions: list[dict[str, Any]]) -> None:
    pending = [item for item in suggestions if item.get("status") == "pending"][:10]
    lines = [
        "## 待审核来源",
        "",
        "这些条目不是未来讲座。它们来自公开推荐或讲座回顾反查，必须由 Owner 核验后才能加入正式来源。",
        "",
        "审核命令：`收录来源：S001` 或 `拒绝来源：S001`。收录后先以第 3 级来源运行，经过校准再提高信任等级。",
        "",
    ]
    for item in pending:
        lines.extend(
            [
                f"### {item['id']} · {item['name']}",
                f"- 候选来源：{item['candidateUrl']}",
                f"- 发现自：[讲座回顾]({item['discoveredFrom']})",
                f"- 推荐者：{item.get('recommendedBy', '自动发现')}",
                f"- 类型：{item.get('sourceType', '官网或预告渠道')}",
                f"- 线索：{item.get('evidence', '')}",
                f"- 建议：{item.get('notes', '')}",
                "",
            ]
        )
    if not pending:
        lines.append("本轮没有发现新的候选来源。")
    (DATA / "source-review-issue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    discover()
