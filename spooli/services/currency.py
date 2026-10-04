"""Currency migration workflow extracted from the settings screen."""

from __future__ import annotations

from spooli.constants.defaults import SettingKey
from spooli.storage.connection import DbPath
from spooli.storage.print_repo import convert_all_records_currency
from spooli.storage.settings_store import set_setting


def run_currency_migration(
    new_currency: str, multiplier: float, path: DbPath = None
) -> dict:
    """Convert stored amounts to a new currency and update the setting."""
    symbol = str(new_currency).strip()
    if not symbol:
        raise ValueError("new_currency must be a non-empty string")
    try:
        factor = float(multiplier)
    except (TypeError, ValueError):
        raise ValueError("multiplier must be a valid number")
    if factor <= 0:
        raise ValueError("multiplier must be greater than 0")
    result = convert_all_records_currency(factor, symbol, path)
    set_setting(SettingKey.CURRENCY_SYMBOL.value, symbol, path)
    return result


__all__ = ["run_currency_migration"]
