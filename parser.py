"""Metadata extraction engine for .gcode and .3mf files.

Covers PrusaSlicer, OrcaSlicer, Bambu Studio, Cura, and Creality Print
(legacy Cura-based headers and newer Orca-based headers/footers).
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Union

from spooli.constants.thresholds import (
    GRAMS_PER_METER_DEFAULT,
    MM_PER_METER,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
)


@dataclass
class PrintMetadata:
    file_name: str
    material: str = "UNKNOWN"
    grams: float = 0.0
    length_mm: float = 0.0
    duration_seconds: int = 0


class UnsupportedFormatError(ValueError):
    pass


class MissingMetadataError(ValueError):
    pass


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
_RE_HMS_WORDS = re.compile(
    r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m(?:in)?)?\s*(?:(\d+(?:\.\d+)?)\s*s)?",
    re.IGNORECASE,
)
_RE_HHMMSS = re.compile(r"(\d+):(\d{1,2}):(\d{1,2})")
_RE_MATERIAL_EQ = re.compile(
    r";\s*(?:filament_type|filament\s+type|material_type|material)\s*[:=]\s*\"?([^\";\r\n]+)",
    re.IGNORECASE,
)


def _sum_number_list(raw: str) -> float | None:
    total = 0.0
    found = False
    for token in re.split(r"[;,]", raw):
        token = token.strip()
        if not token:
            continue
        try:
            total += float(token)
            found = True
        except ValueError:
            continue
    return total if found else None


def _parse_duration_to_seconds(text: str) -> int | None:
    text = text.strip().rstrip(";").strip()
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
        return int(h * SECONDS_PER_HOUR + m * SECONDS_PER_MINUTE + s)
    match = _RE_HMS_WORDS.search(text)
    if match and any(match.groups()):
        h = int(match.group(1)) if match.group(1) else 0
        m = int(match.group(2)) if match.group(2) else 0
        s = float(match.group(3)) if match.group(3) else 0.0
        return int(h * SECONDS_PER_HOUR + m * SECONDS_PER_MINUTE + s)
    return None


def _normalize_material(raw: str | None) -> str:
    if not raw:
        return "UNKNOWN"
    token = re.split(r"[;,]", raw.strip().strip("\"'"))[0].strip()
    token = re.split(r"\s+", token)[0] if token else ""
    return token.upper() if token else "UNKNOWN"


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
            parsed = _parse_duration_to_seconds(match.group(1))
            if parsed is not None:
                acc.duration_seconds = parsed

    if acc.material is None:
        match = _RE_MATERIAL_EQ.search(line)
        if match:
            normalized = _normalize_material(match.group(1))
            if normalized != "UNKNOWN":
                acc.material = normalized


def _parse_stream(lines: Iterable[str], file_name: str) -> PrintMetadata:
    acc = _Accumulator()
    for raw in lines:
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
        grams=float(grams),
        length_mm=float(length_mm),
        duration_seconds=int(acc.duration_seconds or 0),
    )


def _parse_gcode_path(path: Path) -> PrintMetadata:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return _parse_stream(handle, path.name)


def _find_embedded_gcode(names: list[str]) -> str | None:
    gcode_names = [n for n in names if n.lower().endswith((".gcode", ".gco"))]
    if not gcode_names:
        return None
    for name in gcode_names:
        lowered = name.lower()
        if "metadata/" in lowered or lowered.startswith("metadata"):
            return name
    root_level = [n for n in gcode_names if "/" not in n]
    if root_level:
        return sorted(root_level)[0]
    return sorted(gcode_names, key=len)[0]


def _parse_3mf_path(path: Path) -> PrintMetadata:
    try:
        archive = zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid 3mf archive: {path}") from exc
    with archive:
        target = _find_embedded_gcode(archive.namelist())
        if target is None:
            raise MissingMetadataError(
                f"no embedded .gcode stream found in {path.name}"
            )
        with archive.open(target, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="ignore")
            return _parse_stream(text, path.name)


def parse_file(file_path: Union[str, Path]) -> PrintMetadata:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"file not found: {path}")
    suffixes = [s.lower() for s in path.suffixes]
    joined = "".join(suffixes)
    if joined.endswith(".gcode.3mf") or path.suffix.lower() == ".3mf":
        return _parse_3mf_path(path)
    if path.suffix.lower() in (".gcode", ".gco"):
        return _parse_gcode_path(path)
    raise UnsupportedFormatError(
        f"unsupported file format: {path.suffix or path.name}"
    )
