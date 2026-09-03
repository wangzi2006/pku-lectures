from __future__ import annotations

import re
from typing import Any

from common import read_config

POLICY = read_config("policy.json", {})
REGIONS = read_config("regions.json", {})

EXCLUDED_WORDS = set(POLICY.get("excludedWords", []))
PROBABILITY_WORDS = {word.lower() for word in POLICY.get("probabilityWords", [])}
HUMANITIES_TOPICS = {word.lower() for word in POLICY.get("humanitiesTopics", [])}
HUMANITIES_WORDS = {word.lower() for word in POLICY.get("humanitiesWords", [])}
NONCORE_STEM_TOPICS = {word.lower() for word in POLICY.get("noncoreStemTopics", [])}


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
    humanities = topic in HUMANITIES_TOPICS or any(
        word in text for word in HUMANITIES_WORDS
    )
    noncore_stem = topic in NONCORE_STEM_TOPICS
    external = item.get("campus") == "校外"

    weights = POLICY.get("weights", {})
    bonuses = POLICY.get("bonuses", {})
    score = (
        relevance * float(weights.get("relevance", 0.24))
        + quality * float(weights.get("quality", 0.28))
        + undergrad * float(weights.get("undergrad", 0.2))
        + prominence * float(weights.get("prominence", 0.18))
    )
    score += (6 - min(int(source.get("tier", 3)), 5)) * 0.18
    score += float(bonuses.get("probability", 0.7)) if probability else 0
    score += float(bonuses.get("humanities", 0.55)) if humanities else 0
    score += float(bonuses.get("noncoreStem", -0.45)) if noncore_stem else 0
    score += float(bonuses.get("external", -0.65)) if external else 0
    score *= max(float(POLICY.get("confidenceFloor", 0.45)), confidence)
    return round(score, 3)


def apply_region(item: dict[str, Any], source: dict[str, Any]) -> None:
    location = " ".join(
        str(item.get(key, "")) for key in ("location", "title", "titleZh")
    )
    for rule in REGIONS.get("locationRules", []):
        if re.search(str(rule.get("pattern", "")), location, re.I):
            item["region"] = rule.get("region", "待核验")
            item["campus"] = rule.get("campus", item.get("campus", "校外"))
            return
    default = REGIONS.get("sourceDefaults", {}).get(source.get("id"), {})
    if default:
        item["region"] = default.get("region", "待核验")
        item["campus"] = default.get("campus", item.get("campus", "校外"))
    else:
        item["region"] = item.get("region") or "待核验"


def route(item: dict[str, Any], source: dict[str, Any]) -> tuple[str, str]:
    exclusion = hard_exclusion(item)
    if exclusion:
        return "rejected", exclusion

    score = deterministic_score(item, source)
    item["policyScore"] = score
    is_probability = item.get("topic") == "概率"
    is_external = item.get("campus") == "校外"
    thresholds = POLICY.get("thresholds", {})
    threshold = float(
        thresholds.get("probability", 2.2)
        if is_probability
        else thresholds.get("default", 3.05)
    )
    threshold += float(thresholds.get("externalExtra", 0.55)) if is_external else 0

    if score < threshold:
        return "rejected", f"规则分 {score:.2f} 低于门槛 {threshold:.2f}"
    # The first phase is intentionally review-only. Later this can be relaxed
    # for tier-1, high-confidence, non-exceptional items after calibration.
    return "pending", f"规则分 {score:.2f}，进入人工审核"
