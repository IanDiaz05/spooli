"""ANSI styling codes and color policy for the Spooli terminal UI."""

import os
import sys

# Raw SGR sequences backing every public color constant.
_RAW_CYAN = "\033[36m"
_RAW_GREEN = "\033[32m"
_RAW_YELLOW = "\033[33m"
_RAW_RED = "\033[31m"
_RAW_BOLD = "\033[1m"
_RAW_RESET = "\033[0m"


def color_enabled() -> bool:
    """Return True when ANSI styling may be written to stdout.

    Styling is disabled when the NO_COLOR environment variable is
    present or when stdout is not an interactive terminal.
    """
    if "NO_COLOR" in os.environ:
        return False
    isatty = getattr(sys.stdout, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty())
    except Exception:
        # Defensive: unusual stream objects may raise on inspection.
        return False


def _style(sequence: str) -> str:
    # Public codes are resolved once, when this module is imported.
    return sequence if color_enabled() else ""


CYAN = _style(_RAW_CYAN)
GREEN = _style(_RAW_GREEN)
YELLOW = _style(_RAW_YELLOW)
RED = _style(_RAW_RED)
BOLD = _style(_RAW_BOLD)
RESET = _style(_RAW_RESET)


def paint(text: str, *codes: str) -> str:
    """Wrap text in the given ANSI codes, resetting the style afterwards.

    Returns the text unchanged when color is disabled or when no
    effective code is supplied.
    """
    if not color_enabled():
        return text
    prefix = "".join(code for code in codes if code)
    if not prefix:
        return text
    return f"{prefix}{text}{_RAW_RESET}"
