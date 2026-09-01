from __future__ import annotations

import argparse
import re

from common import read_json, write_json


def apply(comment: str) -> None:
    accepted = {
        item.upper()
        for match in re.finditer(r"收录来源\s*[：:]\s*([^\n]+)", comment, re.I)
        for item in re.findall(r"S[0-9A-F]{3,12}", match.group(1), re.I)
    }
    rejected = {
        item.upper()
        for match in re.finditer(r"拒绝来源\s*[：:]\s*([^\n]+)", comment, re.I)
        for item in re.findall(r"S[0-9A-F]{3,12}", match.group(1), re.I)
    }
    if not accepted and not rejected:
        print("No source review commands found.")
        return

    suggestions = read_json("source-suggestions.json", [])
    sources = read_json("sources.json", [])
    existing_urls = {item["url"] for item in sources}
    remaining = []
    changes = []
    for item in suggestions:
        item_id = item["id"].upper()
        if item_id in accepted:
            if item["candidateUrl"] not in existing_urls:
                sources.append(
                    {
                        "id": item["id"].lower(),
                        "name": item["name"],
                        "url": item["candidateUrl"],
                        "kind": "mixed",
                        "tier": 3,
                        "topics": ["待校准"],
                        "enabled": True,
                        "reviewMining": False,
                        "notes": f"由 {item['parentSource']} 的讲座回顾反向发现并经人工批准。",
                    }
                )
                existing_urls.add(item["candidateUrl"])
            changes.append(f"{item['id']} -> accepted")
        elif item_id in rejected:
            changes.append(f"{item['id']} -> rejected")
        else:
            remaining.append(item)

    write_json("sources.json", sources)
    write_json("source-suggestions.json", remaining)
    print("\n".join(changes) if changes else "No matching source IDs found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment", required=True)
    args = parser.parse_args()
    apply(args.comment)
