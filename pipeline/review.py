from __future__ import annotations

import argparse
import re

from common import iso_now, read_json, write_json

COMMANDS = {
    "收录": "published",
    "拒绝": "rejected",
    "待定": "maybe",
}


def parse_comment(comment: str) -> dict[str, str]:
    decisions: dict[str, str] = {}
    for command, status in COMMANDS.items():
        for match in re.finditer(rf"{command}\s*[：:]\s*([^\n]+)", comment, re.I):
            for lecture_id in re.findall(r"L[0-9A-F]{3,12}", match.group(1), re.I):
                decisions[lecture_id.upper()] = status
    return decisions


def apply(comment: str) -> None:
    decisions = parse_comment(comment)
    if not decisions:
        print("No review commands found.")
        return

    candidates = read_json("candidates.json", [])
    lectures = read_json("lectures.json", [])
    audit = read_json("decisions.json", [])
    published_ids = {item["id"] for item in lectures}
    remaining = []
    changed = []

    for item in candidates:
        status = decisions.get(item["id"].upper())
        if not status:
            remaining.append(item)
            continue
        item["status"] = status
        changed.append(f"{item['id']} -> {status}")
        audit.append(
            {
                "lectureId": item["id"],
                "decision": status,
                "decidedAt": iso_now(),
                "snapshot": item,
            }
        )
        if status == "published" and item["id"] not in published_ids:
            lectures.append(item)
        elif status == "maybe":
            remaining.append(item)

    lectures.sort(key=lambda item: item.get("startAt", ""))
    write_json("lectures.json", lectures)
    write_json("candidates.json", remaining)
    write_json("decisions.json", audit)
    print("\n".join(changed) if changed else "No matching candidate IDs found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment", required=True)
    args = parser.parse_args()
    apply(args.comment)
