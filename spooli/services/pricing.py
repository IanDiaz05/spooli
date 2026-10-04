"""Snapshot cost resolution shared by history views."""

from __future__ import annotations


def resolve_record_cost(record: dict, fallback_currency: str) -> tuple[float, str]:
    """Resolve the display cost and currency of a print record."""
    try:
        raw = (
            record.get("total_cost")
            if record.get("total_cost") is not None
            else record.get("cost") or 0
        )
        cost = float(raw)
    except (TypeError, ValueError):
        cost = 0.0
    currency = str(record.get("currency_symbol") or fallback_currency).strip()
    if not currency:
        currency = fallback_currency
    return cost, currency


__all__ = ["resolve_record_cost"]
