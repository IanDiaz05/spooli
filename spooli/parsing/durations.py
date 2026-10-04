"""Human-readable duration parsing."""

from __future__ import annotations

import re

from spooli.constants.thresholds import (
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
)

from .patterns import _RE_HHMMSS, _RE_HMS_WORDS

SECONDS_PER_DAY = 86400.0

_RE_DAYS = re.compile(r"(\d+)\s*d", re.IGNORECASE)


def _first_hms_match(text: str):
    for candidate in _RE_HMS_WORDS.finditer(text):
        if any(candidate.groups()):
            return candidate
    return None


def parse_duration_to_seconds(raw_value: str) -> int | None:
    text = raw_value.strip().rstrip(";").strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    try:
        return int(float(text))
    except ValueError:
        pass
    match = _RE_HHMMSS.search(text)
    if match:
        h, m, s = (int(match.group(i)) for i in (1, 2, 3))
        total = int(h * SECONDS_PER_HOUR + m * SECONDS_PER_MINUTE + s)
        days = _RE_DAYS.search(text)
        if days:
            total += int(int(days.group(1)) * SECONDS_PER_DAY)
        return total
    days = _RE_DAYS.search(text)
    days_total = int(int(days.group(1)) * SECONDS_PER_DAY) if days else 0
    probe = text
    if days:
        probe = text[: days.start()] + " " + text[days.end() :]
    match = _first_hms_match(probe)
    if match:
        h = int(match.group(1)) if match.group(1) else 0
        m = int(match.group(2)) if match.group(2) else 0
        s = float(match.group(3)) if match.group(3) else 0.0
        return int(days_total + h * SECONDS_PER_HOUR + m * SECONDS_PER_MINUTE + s)
    if days:
        return int(days_total)
    return None


_parse_duration_to_seconds = parse_duration_to_seconds

__all__ = [
    "_RE_DAYS",
    "_RE_HHMMSS",
    "_RE_HMS_WORDS",
    "_parse_duration_to_seconds",
    "parse_duration_to_seconds",
]
