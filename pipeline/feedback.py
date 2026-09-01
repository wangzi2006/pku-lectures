from __future__ import annotations

import argparse
import re

from common import iso_now, read_json, write_json

LABELS = {
    "讲座标题或网站条目": "lecture",
    "总体收获": "gain",
    "本科生友好度": "undergrad",
    "内容密度": "density",
    "讲者表达": "delivery",
    "与预告描述相符程度": "match",
    "补充评价": "comment",
}
RATING_FIELDS = {"gain", "undergrad", "density", "delivery", "match"}


def sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", body, re.M))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        key = LABELS.get(match.group(1).strip())
        if key:
            result[key] = body[match.end() : end].strip()
    return result


def store(issue: int, author: str, body: str, url: str) -> None:
    values = sections(body)
    if not values.get("lecture"):
        raise SystemExit("Lecture field is missing from feedback issue")
    record = {
        "issue": issue,
        "author": author,
        "issueUrl": url,
        "lecture": values["lecture"],
        "ratings": {},
        "comment": values.get("comment", ""),
        "updatedAt": iso_now(),
    }
    for field in RATING_FIELDS:
        match = re.search(r"\b([1-5])\b", values.get(field, ""))
        if not match:
            raise SystemExit(f"Invalid or missing {field} rating")
        record["ratings"][field] = int(match.group(1))

    feedback = [item for item in read_json("feedback.json", []) if item.get("issue") != issue]
    feedback.append(record)
    feedback.sort(key=lambda item: item["issue"])
    write_json("feedback.json", feedback)
    print(f"Stored feedback from issue #{issue}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    store(args.issue, args.author, args.body, args.url)
