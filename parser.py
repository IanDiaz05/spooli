"""Metadata extraction engine for .gcode and .3mf files.

Backwards-compatible facade over :mod:`spooli.parsing`.

Covers PrusaSlicer, OrcaSlicer, Bambu Studio, Cura, and Creality Print
(legacy Cura-based headers and newer Orca-based headers/footers).
"""

from __future__ import annotations

from spooli.constants.thresholds import (
    GRAMS_PER_METER_DEFAULT,
    MM_PER_METER,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
)
from spooli.domain.errors import MissingMetadataError, UnsupportedFormatError
from spooli.domain.models import PrintMetadata
from spooli.parsing import parse_file
from spooli.parsing.archive import (
    EMBEDDED_GCODE_SEARCH_ORDER,
    _find_embedded_gcode,
    _parse_3mf_path,
    find_embedded_gcode,
    parse_3mf_path,
)
from spooli.parsing.durations import (
    _parse_duration_to_seconds,
    parse_duration_to_seconds,
)
from spooli.parsing.gcode import (
    _Accumulator,
    _normalize_material,
    _parse_gcode_path,
    _parse_stream,
    _sum_number_list,
    _update_from_line,
    parse_gcode_path,
    parse_stream,
)
from spooli.parsing.patterns import (
    _RE_CURA_TIME,
    _RE_CURA_USED,
    _RE_HHMMSS,
    _RE_HMS_WORDS,
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

__all__ = [
    "EMBEDDED_GCODE_SEARCH_ORDER",
    "GRAMS_PER_METER_DEFAULT",
    "MM_PER_METER",
    "MissingMetadataError",
    "PrintMetadata",
    "SECONDS_PER_HOUR",
    "SECONDS_PER_MINUTE",
    "UnsupportedFormatError",
    "_Accumulator",
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
    "_find_embedded_gcode",
    "_normalize_material",
    "_parse_3mf_path",
    "_parse_duration_to_seconds",
    "_parse_gcode_path",
    "_parse_stream",
    "_sum_number_list",
    "_update_from_line",
    "find_embedded_gcode",
    "parse_3mf_path",
    "parse_duration_to_seconds",
    "parse_file",
    "parse_gcode_path",
    "parse_stream",
]
