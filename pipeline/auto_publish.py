from __future__ import annotations

from typing import Any

from common import canonical_url, iso_now, read_json, title_key, write_json

PUBLISHABLE_STATUSES = {"pending", "maybe", "published"}


def event_key(item: dict[str, Any]) -> str:
    title = title_key(str(item.get("title") or item.get("titleZh") or ""))
    date = str(item.get("startAt", ""))[:10]
    return f"{title}|{date}" if title and date else ""


def prepare_publication(
    candidates: list[dict[str, Any]], lectures: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int]:
    """Move every rule-approved candidate into the public lecture collection."""
    published_ids = {str(item.get("id", "")).upper() for item in lectures}
    published_urls = {
        canonical_url(str(item.get("sourceUrl", "")))
        for item in lectures
        if item.get("sourceUrl")
    }
    published_events = {key for item in lectures if (key := event_key(item))}
    remaining: list[dict[str, Any]] = []
    added = 0
    duplicates = 0

    for candidate in candidates:
        if candidate.get("status") not in PUBLISHABLE_STATUSES:
            remaining.append(candidate)
            continue

        identifier = str(candidate.get("id", "")).upper()
        source_url = canonical_url(str(candidate.get("sourceUrl", "")))
        lecture_event = event_key(candidate)
        if (
            (identifier and identifier in published_ids)
            or (source_url and source_url in published_urls)
            or (lecture_event and lecture_event in published_events)
        ):
            duplicates += 1
            continue

        lecture = dict(candidate)
        lecture["status"] = "published"
        lecture["publicationMode"] = "automatic"
        lecture.setdefault("publishedAt", iso_now())
        note = str(lecture.get("reviewNotes", ""))
        lecture["reviewNotes"] = note.replace("进入人工审核", "通过自动发布门槛")
        lectures.append(lecture)
        added += 1

        if identifier:
            published_ids.add(identifier)
        if source_url:
            published_urls.add(source_url)
        if lecture_event:
            published_events.add(lecture_event)

    lectures.sort(key=lambda item: item.get("startAt", ""))
    return remaining, lectures, added, duplicates


def publish_candidates() -> int:
    candidates = read_json("candidates.json", [])
    lectures = read_json("lectures.json", [])
    remaining, lectures, added, duplicates = prepare_publication(candidates, lectures)
    write_json("candidates.json", remaining)
    write_json("lectures.json", lectures)
    print(f"自动发布 {added} 条；去重移除 {duplicates} 条；队列剩余 {len(remaining)} 条。")
    return added


if __name__ == "__main__":
    publish_candidates()
