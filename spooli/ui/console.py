"""Terminal styling helpers and duration formatting."""

from __future__ import annotations

from spooli.constants import ansi as _ansi
from spooli.constants.thresholds import SECONDS_PER_HOUR, SECONDS_PER_MINUTE


def paint(text: str, *codes: str) -> str:
    """Wrap text in the given ANSI codes."""
    return _ansi.paint(text, *codes)


def heading(text: str) -> str:
    """Format a section heading."""
    return _ansi.paint(text, _ansi.BOLD, _ansi.CYAN)


def success(text: str) -> str:
    """Format a success message."""
    return _ansi.paint(text, _ansi.GREEN)


def warn(text: str) -> str:
    """Format a warning message."""
    return _ansi.paint(text, _ansi.YELLOW)


def error(text: str) -> str:
    """Format an error message."""
    return _ansi.paint(text, _ansi.RED)


def format_duration(total_seconds: int) -> str:
    """Format a duration in seconds as a human-readable string."""
    hours, remainder = divmod(int(total_seconds), int(SECONDS_PER_HOUR))
    minutes, seconds = divmod(remainder, int(SECONDS_PER_MINUTE))
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


__all__ = ["error", "format_duration", "heading", "paint", "success", "warn"]
