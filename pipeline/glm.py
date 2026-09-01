from __future__ import annotations

import json
import os
from typing import Any

import requests

API_URL = "https://api.z.ai/api/paas/v4/chat/completions"
MODEL = "glm-5.3-flash"

SYSTEM_PROMPT = """你是大学讲座信息抽取器。只根据给定网页内容提取事实，不猜测。
输出一个 JSON 对象，字段如下：
isEvent, title, titleZh, speaker, startAt, endAt, location, campus,
distanceKm, topic, subtopics, flags, summary, reason, registrationUrl,
eventType, isPaid, audience, relevanceScore, qualityScore, undergradScore,
prominenceScore, confidence。
分数均为 0 到 5 的独立判断；不要决定是否发布。
startAt/endAt 必须是带 +08:00 的 ISO 8601；不能确认未来时间则 isEvent=false。
summary 为 100-180 个汉字，reason 为一句话。原题不是中文时保留 title 并给 titleZh。
campus 只能为 校内/校外/线上；audience 只能为 public/pku-students/internal-only/unknown。
topic 优先从 概率/统计/数学/数学物理/理论计算机/计算机与 AI/物理/生命科学/人文社科/通识 选择。
只输出 JSON。"""


def extract_event(
    source_name: str, page_url: str, text: str, image_urls: list[str] | None = None
) -> tuple[dict[str, Any], dict[str, int]]:
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        raise RuntimeError("ZAI_API_KEY is not configured")

    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": f"来源：{source_name}\n网址：{page_url}\n网页正文：\n{text[:24000]}",
        }
    ]
    for image_url in (image_urls or [])[:3]:
        user_content.append({"type": "image_url", "image_url": {"url": image_url}})

    payload = {
        "model": MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_content,
            },
        ],
    }
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage") or {}
    return json.loads(content), {
        "input": int(usage.get("prompt_tokens", 0)),
        "output": int(usage.get("completion_tokens", 0)),
    }
