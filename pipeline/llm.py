from __future__ import annotations

import json
import os
import time
from typing import Any

import requests

PROVIDER = os.getenv("AI_PROVIDER", "deepseek").lower()

if PROVIDER == "deepseek":
    API_URL = os.getenv("AI_API_URL", "https://api.deepseek.com/chat/completions")
    MODEL = os.getenv("AI_MODEL", "deepseek-v4-flash")
    PROVIDER_NAME = "DeepSeek"
elif PROVIDER == "bigmodel":
    API_URL = os.getenv(
        "AI_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    )
    MODEL = os.getenv("AI_MODEL", "glm-4.7-flashx")
    PROVIDER_NAME = "智谱"
else:
    raise RuntimeError(f"不支持的 AI_PROVIDER：{PROVIDER}")

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
示例 JSON：{"isEvent":false,"title":"","titleZh":"","speaker":"","startAt":null,
"endAt":null,"location":"","campus":"线上","distanceKm":null,"topic":"通识",
"subtopics":[],"flags":[],"summary":"","reason":"","registrationUrl":"",
"eventType":"","isPaid":false,"audience":"unknown","relevanceScore":0,
"qualityScore":0,"undergradScore":0,"prominenceScore":0,"confidence":0}。
只输出 JSON。"""


class AIAPIError(RuntimeError):
    def __init__(self, message: str, *, fatal: bool = False) -> None:
        super().__init__(message)
        self.fatal = fatal


def api_key() -> str | None:
    if PROVIDER == "deepseek":
        return os.getenv("DEEPSEEK_API_KEY")
    return os.getenv("BIGMODEL_API_KEY") or os.getenv("ZAI_API_KEY")


def key_name() -> str:
    return "DEEPSEEK_API_KEY" if PROVIDER == "deepseek" else "BIGMODEL_API_KEY/ZAI_API_KEY"


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
        raise AIAPIError(f"未配置 {key_name()}", fatal=True)

    response: requests.Response | None = None
    for attempt in range(3):
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            if attempt == 2:
                raise AIAPIError(f"无法连接 {PROVIDER_NAME} API：{exc}") from exc
            time.sleep(2**attempt)
            continue

        if response.ok:
            break
        if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
            time.sleep(2**attempt)
            continue
        fatal = response.status_code in {400, 401, 402, 403, 404, 429}
        raise AIAPIError(
            f"{PROVIDER_NAME} API 返回 HTTP {response.status_code}：{_error_message(response)}",
            fatal=fatal,
        )

    if response is None or not response.ok:
        raise AIAPIError(f"{PROVIDER_NAME} API 请求失败")
    try:
        return response.json()
    except ValueError as exc:
        raise AIAPIError(f"{PROVIDER_NAME} API 返回了非 JSON 响应") from exc


def verify_api() -> None:
    """Fail fast before crawling dozens of pages with a bad key, endpoint, or model."""
    result = _post(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": "只回复 OK"}],
            "thinking": {"type": "disabled"},
            "max_tokens": 8,
            "stream": False,
        }
    )
    if not result.get("choices"):
        raise AIAPIError(f"{PROVIDER_NAME} API 校验响应缺少 choices", fatal=True)


def _parse_json_content(content: Any) -> dict[str, Any]:
    if not isinstance(content, str) or not content.strip():
        raise AIAPIError("模型响应 content 为空或不是文本")
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIAPIError(f"模型未返回有效 JSON：{exc}") from exc
    if not isinstance(parsed, dict):
        raise AIAPIError("模型响应 JSON 不是对象")
    return parsed


def extract_event(
    source_name: str, page_url: str, text: str, image_urls: list[str] | None = None
) -> tuple[dict[str, Any], dict[str, int]]:
    prompt = f"来源：{source_name}\n网址：{page_url}\n网页正文：\n{text[:24000]}"
    enable_images = os.getenv("AI_ENABLE_IMAGES", "false").lower() == "true"
    user_content: str | list[dict[str, Any]] = prompt
    if enable_images:
        user_content = [{"type": "text", "text": prompt}]
        for image_url in (image_urls or [])[:3]:
            user_content.append({"type": "image_url", "image_url": {"url": image_url}})

    result = _post(
        {
            "model": MODEL,
            "thinking": {"type": "disabled"},
            "max_tokens": 1800,
            "stream": False,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        }
    )
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIAPIError(f"{PROVIDER_NAME} API 响应缺少消息内容") from exc
    usage = result.get("usage") or {}
    return _parse_json_content(content), {
        "input": int(usage.get("prompt_tokens", 0)),
        "output": int(usage.get("completion_tokens", 0)),
    }
