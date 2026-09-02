from __future__ import annotations

from typing import Any

EXCLUDED_WORDS = {
    "招生",
    "招聘",
    "宣讲会",
    "竞赛",
    "社团招新",
    "付费",
    "课程通知",
    "培训班",
}

PROBABILITY_WORDS = {
    "概率",
    "随机",
    "stochastic",
    "probability",
    "martingale",
    "马尔可夫",
}

HUMANITIES_TOPICS = {"人文社科", "通识", "文学", "历史", "哲学", "艺术", "法学", "社会科学"}
HUMANITIES_WORDS = {
    "文学",
    "历史",
    "哲学",
    "艺术",
    "考古",
    "语言学",
    "社会学",
    "人类学",
    "政治学",
    "法学",
    "文化",
    "文明",
}
NONCORE_STEM_TOPICS = {"物理", "生命科学", "医学", "化学", "工程", "计算机与 ai"}


def hard_exclusion(item: dict[str, Any]) -> str | None:
    text = " ".join(
        str(item.get(key, "")) for key in ("title", "titleZh", "summary", "eventType")
    ).lower()
    matched = sorted(word for word in EXCLUDED_WORDS if word.lower() in text)
    if matched:
        return f"命中排除词：{', '.join(matched)}"
    if item.get("isPaid") is True:
        return "付费活动"
    if item.get("audience") == "internal-only":
        return "仅限内部人员"
    return None


def deterministic_score(item: dict[str, Any], source: dict[str, Any]) -> float:
    """AI only supplies independent dimensions; this function owns weights."""
    relevance = float(item.get("relevanceScore", 0))
    quality = float(item.get("qualityScore", 0))
    undergrad = float(item.get("undergradScore", 0))
    prominence = float(item.get("prominenceScore", 0))
    confidence = max(0.0, min(1.0, float(item.get("confidence", 0))))
    text = " ".join(str(item.get(key, "")) for key in ("title", "titleZh", "summary")).lower()
    probability = any(word in text for word in PROBABILITY_WORDS)
    topic = str(item.get("topic", "")).strip().lower()
    humanities = topic in {value.lower() for value in HUMANITIES_TOPICS} or any(
        word in text for word in HUMANITIES_WORDS
    )
    noncore_stem = topic in NONCORE_STEM_TOPICS
    external = item.get("campus") == "校外"

    score = relevance * 0.24 + quality * 0.28 + undergrad * 0.2 + prominence * 0.18
    score += (6 - min(int(source.get("tier", 3)), 5)) * 0.18
    score += 0.7 if probability else 0
    score += 0.55 if humanities else 0
    score -= 0.45 if noncore_stem else 0
    score -= 0.65 if external else 0
    score *= max(0.45, confidence)
    return round(score, 3)


def route(item: dict[str, Any], source: dict[str, Any]) -> tuple[str, str]:
    exclusion = hard_exclusion(item)
    if exclusion:
        return "rejected", exclusion

    score = deterministic_score(item, source)
    item["policyScore"] = score
    is_probability = item.get("topic") == "概率"
    is_external = item.get("campus") == "校外"
    threshold = 2.2 if is_probability else 3.05
    threshold += 0.55 if is_external else 0

    if score < threshold:
        return "rejected", f"规则分 {score:.2f} 低于门槛 {threshold:.2f}"
    # The first phase is intentionally review-only. Later this can be relaxed
    # for tier-1, high-confidence, non-exceptional items after calibration.
    return "pending", f"规则分 {score:.2f}，进入人工审核"
