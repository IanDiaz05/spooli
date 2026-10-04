"""Parsing subpackage entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from spooli.domain.errors import MissingMetadataError, UnsupportedFormatError
from spooli.domain.models import PrintMetadata

from .archive import parse_3mf_path
from .gcode import parse_gcode_path, parse_stream


def parse_file(file_path: Union[str, Path]) -> PrintMetadata:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"file not found: {path}")
    suffixes = [s.lower() for s in path.suffixes]
    joined = "".join(suffixes)
    if joined.endswith(".gcode.3mf") or path.suffix.lower() == ".3mf":
        return parse_3mf_path(path)
    if path.suffix.lower() in (".gcode", ".gco"):
        return parse_gcode_path(path)
    raise UnsupportedFormatError(
        f"unsupported file format: {path.suffix or path.name}"
    )


__all__ = [
    "MissingMetadataError",
    "PrintMetadata",
    "UnsupportedFormatError",
    "parse_3mf_path",
    "parse_file",
    "parse_gcode_path",
    "parse_stream",
]
