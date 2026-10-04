"""Interrupt-safe terminal input primitives."""

from __future__ import annotations

from typing import Optional

from spooli.constants import ansi as _ansi
from spooli.constants.formats import YES_TOKENS
from spooli.constants.messages import MSG_INVALID_NUMBER, MSG_OPERATION_CANCELLED, MSG_PRESS_ENTER


def safe_input(prompt: str = "") -> str | None:
    """Prompt the user, returning None on EOF or interrupt."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print(f"\n{_ansi.paint(MSG_OPERATION_CANCELLED, _ansi.YELLOW)}")
        return None


def pause(prompt: str = MSG_PRESS_ENTER) -> None:
    """Wait for the user to press Enter."""
    try:
        input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()


def prompt_float(prompt: str, default: Optional[float] = None) -> Optional[float]:
    """Prompt for a float, accepting Spanish decimal commas."""
    raw = safe_input(prompt)
    if raw is None:
        return None
    text = raw.strip().replace(",", ".")
    if text == "":
        return default
    try:
        return float(text)
    except ValueError:
        print(_ansi.paint(MSG_INVALID_NUMBER, _ansi.RED))
        return None


def confirm(prompt: str, default_yes: bool = False) -> bool:
    """Prompt for a yes/no answer using shared affirmative tokens."""
    raw = safe_input(prompt)
    if raw is None:
        return False
    text = raw.strip().lower()
    if text == "":
        return default_yes
    return text in YES_TOKENS


__all__ = ["confirm", "pause", "prompt_float", "safe_input"]
