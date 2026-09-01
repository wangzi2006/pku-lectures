from __future__ import annotations

import json
import os
from typing import Any

import requests

API_URL = os.getenv(
    "BIGMODEL_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions"
)
MODEL = os.getenv("GLM_MODEL", "glm-4.7-flash")
REQUEST_TIMEOUT = (10, 45)

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


class GLMAPIError(RuntimeError):
    def __init__(self, message: str, *, fatal: bool = False) -> None:
        super().__init__(message)
        self.fatal = fatal


def api_key() -> str | None:
    # Keep ZAI_API_KEY for compatibility with the GitHub secret already in use.
    return os.getenv("BIGMODEL_API_KEY") or os.getenv("ZAI_API_KEY")


def _error_message(response: requests.Response) -> str:
    try:
        body = response.json()
        error = body.get("error", body)
        if isinstance(error, dict):
            detail = error.get("message") or error.get("msg") or error.get("code")
        else:
            detail = error
    except ValueError:
        detail = response.text[:300]
    return str(detail or "未知错误").replace("\n", " ").strip()[:300]


def _post(payload: dict[str, Any]) -> dict[str, Any]:
    key = api_key()
    if not key:
        raise GLMAPIError("未配置 BIGMODEL_API_KEY/ZAI_API_KEY", fatal=True)
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise GLMAPIError(f"无法连接智谱 API：{exc}") from exc
    if not response.ok:
        fatal = response.status_code in {400, 401, 403, 404, 429}
        raise GLMAPIError(
            f"智谱 API 返回 HTTP {response.status_code}：{_error_message(response)}",
            fatal=fatal,
        )
    try:
        return response.json()
    except ValueError as exc:
        raise GLMAPIError("智谱 API 返回了非 JSON 响应") from exc


def verify_api() -> None:
    """Fail fast before crawling dozens of pages with a bad key, endpoint, or model."""
    result = _post(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": "只回复 OK"}],
            "thinking": {"type": "disabled"},
            "max_tokens": 8,
            "temperature": 0.1,
            "stream": False,
        }
    )
    if not result.get("choices"):
        raise GLMAPIError("智谱 API 校验响应缺少 choices", fatal=True)


def _parse_json_content(content: Any) -> dict[str, Any]:
    if not isinstance(content, str):
        raise GLMAPIError("模型响应 content 不是文本")
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GLMAPIError(f"模型未返回有效 JSON：{exc}") from exc
    if not isinstance(parsed, dict):
        raise GLMAPIError("模型响应 JSON 不是对象")
    return parsed


def extract_event(
    source_name: str, page_url: str, text: str, image_urls: list[str] | None = None
) -> tuple[dict[str, Any], dict[str, int]]:
    prompt = f"来源：{source_name}\n网址：{page_url}\n网页正文：\n{text[:24000]}"
    enable_images = os.getenv("GLM_ENABLE_IMAGES", "false").lower() == "true"
    user_content: str | list[dict[str, Any]] = prompt
    if enable_images:
        user_content = [{"type": "text", "text": prompt}]
        for image_url in (image_urls or [])[:3]:
            user_content.append({"type": "image_url", "image_url": {"url": image_url}})

    payload = {
        "model": MODEL,
        "temperature": 0.1,
        "thinking": {"type": "disabled"},
        "max_tokens": 1800,
        "stream": False,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_content,
            },
        ],
    }
    result = _post(payload)
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GLMAPIError("智谱 API 响应缺少消息内容") from exc
    usage = result.get("usage") or {}
    return _parse_json_content(content), {
        "input": int(usage.get("prompt_tokens", 0)),
        "output": int(usage.get("completion_tokens", 0)),
    }
