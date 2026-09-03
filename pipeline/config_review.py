from __future__ import annotations

import argparse
import json
import re

from common import CONFIG, read_config, read_json, write_json


def words(value: str) -> list[str]:
    return [item for item in re.split(r"[\s,，、]+", value.strip()) if item]


def apply(comment: str) -> None:
    policy = read_config("policy.json", {})
    topics = read_config("topics.json", {})
    sources = read_json("sources.json", [])
    changed: list[str] = []

    for command, add in (("新增硬排除", True), ("移除硬排除", False)):
        for match in re.finditer(rf"{command}\s*[：:]\s*([^\n]+)", comment, re.I):
            current = list(policy.get("excludedWords", []))
            for value in words(match.group(1)):
                if add and value not in current:
                    current.append(value)
                    changed.append(f"新增硬排除：{value}")
                elif not add and value in current:
                    current.remove(value)
                    changed.append(f"移除硬排除：{value}")
            policy["excludedWords"] = current

    for command, add in (("新增标签", True), ("删除标签", False)):
        for match in re.finditer(rf"{command}\s*[：:]\s*([^\n]+)", comment, re.I):
            current = list(topics.get("order", []))
            for value in words(match.group(1)):
                if add and value not in current:
                    current.append(value)
                    changed.append(f"新增标签：{value}")
                elif not add and value in current:
                    current.remove(value)
                    changed.append(f"删除标签：{value}")
            topics["order"] = current

    for command, enabled in (("启用来源", True), ("停用来源", False)):
        for match in re.finditer(rf"{command}\s*[：:]\s*([^\n]+)", comment, re.I):
            requested = set(words(match.group(1)))
            for source in sources:
                if source.get("id") in requested and source.get("enabled") != enabled:
                    source["enabled"] = enabled
                    changed.append(f"{command}：{source['id']}")

    for match in re.finditer(
        r"设置来源等级\s*[：:]\s*([a-z0-9-]+)\s+([1-5])", comment, re.I
    ):
        source_id, tier_text = match.groups()
        for source in sources:
            if source.get("id", "").lower() == source_id.lower():
                source["tier"] = int(tier_text)
                changed.append(f"设置来源等级：{source['id']} {tier_text}")

    if not changed:
        print("没有识别到有效或有变化的设置命令")
        return
    (CONFIG / "policy.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (CONFIG / "topics.json").write_text(
        json.dumps(topics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_json("sources.json", sources)
    print("\n".join(changed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment", required=True)
    args = parser.parse_args()
    apply(args.comment)
