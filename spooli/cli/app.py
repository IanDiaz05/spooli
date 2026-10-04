"""Application entry point."""

from __future__ import annotations

from typing import Optional

from spooli.constants.defaults import SettingKey
from spooli.storage import get_db_path
from spooli.storage.settings_store import get_setting
from spooli.ui.screens.onboarding import run_onboarding
from spooli.ui.screens.shell import main_menu

from .args import parse_args
from .direct_mode import run_direct_mode


def is_first_run() -> bool:
    """Check whether settings or the database are uninitialized."""
    try:
        db_path = get_db_path()
    except Exception:
        return False
    if not db_path.is_file():
        return True
    try:
        value = get_setting(SettingKey.CURRENCY_SYMBOL.value)
    except Exception:
        return True
    return value is None


def main(argv: Optional[list[str]] = None) -> int:
    """Dispatch onboarding, direct mode, or the interactive menu."""
    try:
        args = parse_args(argv)
        if is_first_run():
            run_onboarding()
        if not args.file_path:
            main_menu()
            return 0
        return run_direct_mode(args.file_path, args.spool, args.yes)
    except KeyboardInterrupt:
        print()
        return 0


__all__ = ["is_first_run", "main"]
