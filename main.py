"""Direct-mode CLI entry point for Spooli."""

from __future__ import annotations

import sys

from spooli.cli import (
    is_first_run,
    main,
    parse_args,
    run_direct_mode,
)
from spooli.cli.summary import display_summary as _display_summary_new
from spooli.ui.console import format_duration
from spooli.ui.screens.onboarding import _onboarding_input, run_onboarding


def display_summary(metadata, spool: dict, costs, currency: str) -> float:
    """Print the print-job summary and return the remaining weight."""
    _display_summary_new(metadata, spool, costs, currency)
    return float(spool["remaining_weight_g"]) - float(metadata.grams)


__all__ = [
    "_onboarding_input",
    "display_summary",
    "format_duration",
    "is_first_run",
    "main",
    "parse_args",
    "run_direct_mode",
    "run_onboarding",
]


if __name__ == "__main__":
    sys.exit(main())
