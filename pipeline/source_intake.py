from __future__ import annotations

import argparse
import re

from common import canonical_url, iso_now, next_numbered_id, read_json, write_json
from discover_sources import write_issue

LABELS = {
    "来源名称": "name",
    "网站、公众号主页或示例原文": "url",
    "来源类型": "sourceType",
    "这个来源通常发布什么": "evidence",
}


def sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", body, re.M))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        key = LABELS.get(match.group(1).strip())
        if key:
            value = body[match.end() : end].strip()
            result[key] = "" if value == "_No response_" else value
    return result


def store(issue: int, author: str, body: str, issue_url: str) -> None:
    values = sections(body)
    if not values.get("name") or not values.get("url"):
        raise SystemExit("来源名称或链接缺失")
    candidate_url = canonical_url(values["url"].split()[0])
    if not candidate_url.startswith("http"):
        raise SystemExit("来源链接必须以 http:// 或 https:// 开头")

    sources = read_json("sources.json", [])
    if candidate_url in {canonical_url(item["url"]) for item in sources}:
        print("来源已经在正式目录中")
        return

    suggestions = [
        item
        for item in read_json("source-suggestions.json", [])
        if item.get("submissionIssue") != issue
    ]
    suggestion = {
        "id": next_numbered_id("S", sources, suggestions),
        "status": "pending",
        "name": values["name"],
        "candidateUrl": candidate_url,
        "sourceType": values.get("sourceType", "其他"),
        "discoveredFrom": issue_url,
        "parentSource": f"GitHub 推荐（{author}）",
        "recommendedBy": author,
        "submissionIssue": issue,
        "evidence": values.get("evidence", ""),
        "discoveredAt": iso_now(),
        "notes": "由社区或 Owner 推荐；须由仓库 Owner 明确批准后加入。",
    }
    suggestions.append(suggestion)
    suggestions.sort(key=lambda item: item.get("discoveredAt", ""))
    write_json("source-suggestions.json", suggestions)
    write_issue(suggestions)
    print(f"Stored source suggestion {suggestion['id']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    store(args.issue, args.author, args.body, args.url)
