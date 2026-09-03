from __future__ import annotations

import argparse
import re

from common import canonical_url, read_json, write_json
from discover_sources import write_issue


def parse_comment(comment: str) -> tuple[set[str], set[str]]:
    accepted = {
        item.upper()
        for match in re.finditer(r"收录来源\s*[：:]\s*([^\n]+)", comment, re.I)
        for item in re.findall(r"S[0-9A-Z]{3,16}", match.group(1), re.I)
    }
    rejected = {
        item.upper()
        for match in re.finditer(r"拒绝来源\s*[：:]\s*([^\n]+)", comment, re.I)
        for item in re.findall(r"S[0-9A-Z]{3,16}", match.group(1), re.I)
    }
    return accepted, rejected


def apply(comment: str) -> None:
    accepted, rejected = parse_comment(comment)
    if not accepted and not rejected:
        print("No source review commands found.")
        return

    suggestions = read_json("source-suggestions.json", [])
    sources = read_json("sources.json", [])
    existing_urls = {canonical_url(item["url"]) for item in sources}
    remaining = []
    changes = []
    for item in suggestions:
        item_id = item["id"].upper()
        if item_id in accepted:
            candidate_url = canonical_url(item["candidateUrl"])
            if candidate_url not in existing_urls:
                source_type = item.get("sourceType", "")
                is_wechat = "公众号" in source_type or "mp.weixin.qq.com" in candidate_url
                sources.append(
                    {
                        "id": item["id"].lower(),
                        "name": item["name"],
                        "url": candidate_url,
                        "kind": "wechat" if is_wechat else "mixed",
                        "tier": 3,
                        "topics": ["待校准"],
                        "enabled": True,
                        "reviewMining": False,
                        **({"transport": "local-collector"} if is_wechat else {}),
                        "notes": (
                            f"由 {item['parentSource']} 推荐并经 Owner 批准。"
                            if item.get("recommendedBy")
                            else f"由 {item['parentSource']} 的讲座回顾反向发现并经人工批准。"
                        ),
                    }
                )
                existing_urls.add(candidate_url)
            changes.append(f"{item['id']} -> accepted")
        elif item_id in rejected:
            changes.append(f"{item['id']} -> rejected")
        else:
            remaining.append(item)

    write_json("sources.json", sources)
    write_json("source-suggestions.json", remaining)
    write_issue(remaining)
    print("\n".join(changes) if changes else "No matching source IDs found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment", required=True)
    args = parser.parse_args()
    apply(args.comment)
