from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "config"


def read_json(name: str, default: Any) -> Any:
    path = DATA / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_config(name: str, default: Any) -> Any:
    path = CONFIG / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, value: Any) -> None:
    path = DATA / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def canonical_url(url: str) -> str:
    split = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(split.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in {"from", "scene", "clicktime", "enterid"}
    ]
    return urlunsplit(
        (split.scheme.lower(), split.netloc.lower(), split.path.rstrip("/"), urlencode(query), "")
    )


def stable_id(prefix: str, value: str, length: int = 10) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:length].upper()
    return f"{prefix}{digest}"


def next_numbered_id(prefix: str, *collections: list[dict[str, Any]]) -> str:
    """Return the next short, human-enterable ID such as S001."""
    numbers: list[int] = []
    pattern = re.compile(rf"{re.escape(prefix)}(\d+)", re.I)
    for collection in collections:
        for item in collection:
            identifier = str(item.get("id", ""))
            match = pattern.fullmatch(identifier)
            if match:
                numbers.append(int(match.group(1)))
    return f"{prefix.upper()}{max(numbers, default=0) + 1:03d}"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def title_key(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.lower())
