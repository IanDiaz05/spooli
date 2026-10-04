"""Slicer comment patterns for the parsing engine."""

from __future__ import annotations

import re

_RE_WEIGHT_G = re.compile(
    r"filament\s+used\s*\[g\]\s*[:=]\s*([0-9][0-9.,\s;]*)", re.IGNORECASE
)
_RE_TOTAL_WEIGHT_G = re.compile(
    r"total\s+filament\s+used\s*\[g\]\s*[:=]\s*([0-9][0-9.,\s;]*)",
    re.IGNORECASE,
)
_RE_WEIGHT_G_EQ = re.compile(
    r"filament\s+weight\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)\s*g", re.IGNORECASE
)
_RE_LENGTH_MM = re.compile(
    r"filament\s+used\s*\[mm\]\s*[:=]\s*([0-9][0-9.,\s;]*)", re.IGNORECASE
)
_RE_LENGTH_M = re.compile(
    r"filament\s+used\s*\[m\]\s*[:=]\s*([0-9][0-9.,\s;]*)", re.IGNORECASE
)
_RE_TOTAL_LENGTH_MM = re.compile(
    r"total\s+filament\s+used\s*\[mm\]\s*[:=]\s*([0-9][0-9.,\s;]*)",
    re.IGNORECASE,
)
_RE_TOTAL_LENGTH_M = re.compile(
    r"total\s+filament\s+used\s*\[m\]\s*[:=]\s*([0-9][0-9.,\s;]*)",
    re.IGNORECASE,
)
_RE_CURA_USED = re.compile(
    r";\s*Filament\s+used\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*m", re.IGNORECASE
)
_RE_CURA_TIME = re.compile(r";\s*TIME\s*:\s*([0-9]+)", re.IGNORECASE)
_RE_TIME_EQ_S = re.compile(
    r"estimated\s+printing\s+time.*?=\s*([0-9]+)\s*s\s*$", re.IGNORECASE
)
_RE_TIME_HMS_WORDS = re.compile(
    r"estimated\s+printing\s+time.*?=\s*(.+)$", re.IGNORECASE
)
_RE_MODEL_TIME = re.compile(
    r"model\s+printing\s+time\s*[:=]\s*(.+)$", re.IGNORECASE
)
_RE_MATERIAL_EQ = re.compile(
    r";\s*(?:filament_type|filament\s+type|material_type|material)\s*[:=]\s*\"?([^\";\r\n]+)",
    re.IGNORECASE,
)
_RE_HMS_WORDS = re.compile(
    r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+(?:\.\d+)?)\s*s)?",
    re.IGNORECASE,
)
_RE_HHMMSS = re.compile(r"(\d+):(\d{1,2}):(\d{1,2})")

_RE_SPLIT_DELIMITERS = re.compile(r"[;,]")
_RE_SPLIT_WHITESPACE = re.compile(r"\s+")

__all__ = [
    "_RE_CURA_TIME",
    "_RE_CURA_USED",
    "_RE_HHMMSS",
    "_RE_HMS_WORDS",
    "_RE_LENGTH_M",
    "_RE_LENGTH_MM",
    "_RE_MATERIAL_EQ",
    "_RE_MODEL_TIME",
    "_RE_SPLIT_DELIMITERS",
    "_RE_SPLIT_WHITESPACE",
    "_RE_TIME_EQ_S",
    "_RE_TIME_HMS_WORDS",
    "_RE_TOTAL_LENGTH_M",
    "_RE_TOTAL_LENGTH_MM",
    "_RE_TOTAL_WEIGHT_G",
    "_RE_WEIGHT_G",
    "_RE_WEIGHT_G_EQ",
]
