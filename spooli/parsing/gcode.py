"""Line-oriented G-code metadata extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from spooli.constants.thresholds import (
    GRAMS_PER_METER_DEFAULT,
    MM_PER_METER,
)
from spooli.domain.errors import MissingMetadataError
from spooli.domain.models import PrintMetadata

from .durations import parse_duration_to_seconds
from .patterns import (
    _RE_CURA_TIME,
    _RE_CURA_USED,
    _RE_LENGTH_M,
    _RE_LENGTH_MM,
    _RE_MATERIAL_EQ,
    _RE_MODEL_TIME,
    _RE_SPLIT_DELIMITERS,
    _RE_SPLIT_WHITESPACE,
    _RE_TIME_EQ_S,
    _RE_TIME_HMS_WORDS,
    _RE_TOTAL_LENGTH_M,
    _RE_TOTAL_LENGTH_MM,
    _RE_TOTAL_WEIGHT_G,
    _RE_WEIGHT_G,
    _RE_WEIGHT_G_EQ,
)


def _sum_number_list(raw: str) -> float | None:
    total = 0.0
    found = False
    for token in _RE_SPLIT_DELIMITERS.split(raw):
        token = token.strip()
        if not token:
            continue
        try:
            total += float(token)
            found = True
        except ValueError:
            continue
    return total if found else None


def _normalize_material(raw: str | None) -> str:
    if not raw:
        return "UNKNOWN"
    token = _RE_SPLIT_DELIMITERS.split(raw.strip().strip("\"'"))[0].strip()
    token = _RE_SPLIT_WHITESPACE.split(token)[0] if token else ""
    return token.upper() if token else "UNKNOWN"


_parse_duration_to_seconds = parse_duration_to_seconds


@dataclass
class _Accumulator:
    grams: float | None = None
    length_mm: float | None = None
    duration_seconds: int | None = None
    material: str | None = None
    extra: dict = field(default_factory=dict)

    def complete(self) -> bool:
        return (
            self.grams is not None
            and self.length_mm is not None
            and self.duration_seconds is not None
            and self.material is not None
        )


def _update_from_line(line: str, acc: _Accumulator) -> None:
    if not line.startswith(";"):
        return

    match = _RE_TOTAL_WEIGHT_G.search(line) or _RE_WEIGHT_G.search(line)
    if match and acc.grams is None:
        value = _sum_number_list(match.group(1))
        if value is not None:
            acc.grams = value

    if acc.grams is None:
        match = _RE_WEIGHT_G_EQ.search(line)
        if match:
            try:
                acc.grams = float(match.group(1))
            except ValueError:
                pass

    match = _RE_TOTAL_LENGTH_MM.search(line) or _RE_LENGTH_MM.search(line)
    if match and acc.length_mm is None:
        value = _sum_number_list(match.group(1))
        if value is not None:
            acc.length_mm = value

    if acc.length_mm is None:
        match = _RE_TOTAL_LENGTH_M.search(line) or _RE_LENGTH_M.search(line)
        if match:
            value = _sum_number_list(match.group(1))
            if value is not None:
                acc.length_mm = value * MM_PER_METER

    if acc.length_mm is None:
        match = _RE_CURA_USED.search(line)
        if match:
            try:
                acc.length_mm = float(match.group(1)) * MM_PER_METER
            except ValueError:
                pass

    if acc.duration_seconds is None:
        match = _RE_CURA_TIME.search(line)
        if match:
            try:
                acc.duration_seconds = int(match.group(1))
            except ValueError:
                pass

    if acc.duration_seconds is None:
        match = _RE_TIME_EQ_S.search(line)
        if match:
            try:
                acc.duration_seconds = int(match.group(1))
            except ValueError:
                pass

    if acc.duration_seconds is None:
        match = _RE_TIME_HMS_WORDS.search(line) or _RE_MODEL_TIME.search(line)
        if match:
            parsed = parse_duration_to_seconds(match.group(1))
            if parsed is not None:
                acc.duration_seconds = parsed

    if acc.material is None:
        match = _RE_MATERIAL_EQ.search(line)
        if match:
            normalized = _normalize_material(match.group(1))
            if normalized != "UNKNOWN":
                acc.material = normalized


def parse_stream(stream: Iterable[str], file_name: str = "") -> PrintMetadata:
    acc = _Accumulator()
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        _update_from_line(line, acc)
        if acc.complete():
            break

    grams = acc.grams
    length_mm = acc.length_mm or 0.0
    if grams is None and acc.length_mm is not None:
        grams = acc.length_mm / MM_PER_METER * GRAMS_PER_METER_DEFAULT
    if grams is None:
        raise MissingMetadataError(
            f"no filament weight or length metadata found in {file_name}"
        )

    return PrintMetadata(
        file_name=file_name,
        material=acc.material or "UNKNOWN",
        filament_used_g=float(grams),
        filament_used_mm=float(length_mm),
        print_duration_seconds=int(acc.duration_seconds or 0),
    )


def _parse_stream(lines: Iterable[str], file_name: str) -> PrintMetadata:
    return parse_stream(lines, file_name)


def parse_gcode_path(file_path: Path) -> PrintMetadata:
    path = Path(file_path)
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return parse_stream(handle, path.name)


def _parse_gcode_path(path: Path) -> PrintMetadata:
    return parse_gcode_path(path)


__all__ = [
    "_Accumulator",
    "_normalize_material",
    "_parse_duration_to_seconds",
    "_parse_gcode_path",
    "_parse_stream",
    "_sum_number_list",
    "_update_from_line",
    "parse_gcode_path",
    "parse_stream",
]
