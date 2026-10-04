"""Backwards-compatible facade over the modular UI and services layers."""

from __future__ import annotations

from spooli.constants.thresholds import LOW_STOCK_RATIO
from spooli.services.currency import run_currency_migration
from spooli.services.pricing import resolve_record_cost
from spooli.ui.console import error, format_duration, heading, paint, success, warn
from spooli.ui.input import confirm, pause, prompt_float, safe_input
from spooli.ui.screens.failed_prints import register_failed_print
from spooli.ui.screens.history import show_history
from spooli.ui.screens.inventory import show_inventory
from spooli.ui.screens.settings import show_settings
from spooli.ui.screens.shell import main_menu
from spooli.ui.screens.spool_form import create_spool_form
from spooli.ui.table import Table, render_table

LOW_STOCK_THRESHOLD = LOW_STOCK_RATIO

__all__ = [
    "LOW_STOCK_THRESHOLD",
    "Table",
    "confirm",
    "create_spool_form",
    "error",
    "format_duration",
    "heading",
    "main_menu",
    "paint",
    "pause",
    "prompt_float",
    "register_failed_print",
    "render_table",
    "resolve_record_cost",
    "run_currency_migration",
    "safe_input",
    "show_history",
    "show_inventory",
    "show_settings",
    "success",
    "warn",
]


if __name__ == "__main__":
    main_menu()
