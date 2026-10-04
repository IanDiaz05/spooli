"""Embedded G-code discovery and parsing for 3MF archives."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Union

from spooli.domain.errors import MissingMetadataError
from spooli.domain.models import PrintMetadata

from .gcode import parse_stream

# Preference order when several G-code streams share one archive:
# metadata/ payload first, then repository root, then shortest path.
EMBEDDED_GCODE_SEARCH_ORDER = ("metadata/", "", "shortest")


def find_embedded_gcode(archive: zipfile.ZipFile) -> str | None:
    return _find_embedded_gcode(archive.namelist())


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


def parse_3mf_path(file_path: Union[str, Path]) -> PrintMetadata:
    path = Path(file_path)
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
            return parse_stream(text, path.name)


def _parse_3mf_path(path: Path) -> PrintMetadata:
    return parse_3mf_path(path)


__all__ = [
    "EMBEDDED_GCODE_SEARCH_ORDER",
    "_find_embedded_gcode",
    "_parse_3mf_path",
    "find_embedded_gcode",
    "parse_3mf_path",
]
