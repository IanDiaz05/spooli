"""Filament refund calculation of Spooli."""

from __future__ import annotations

from spooli.constants.formats import GRAMS_DECIMALS
from spooli.constants.thresholds import PERCENT_MAX

from .models import RefundResult


def calculate_refund(
    estimated_grams: float,
    actual_usage: float,
    is_percent: bool = False,
) -> RefundResult:
    """Calculate filament refund for a failed print.

    If is_percent is True, actual_usage is a failure percentage (0-100)
    representing the proportion of the print that completed.
    If False, actual_usage is the measured weight consumed in grams.

    Returns actual consumption and the grams to refund back to inventory.
    """
    if estimated_grams < 0:
        raise ValueError("estimated_grams cannot be negative")
    if actual_usage < 0:
        raise ValueError("actual_usage cannot be negative")

    if is_percent:
        if actual_usage > PERCENT_MAX:
            raise ValueError("failure percentage cannot exceed 100")
        actual_consumption = estimated_grams * (actual_usage / PERCENT_MAX)
    else:
        actual_consumption = actual_usage

    actual_consumption = round(actual_consumption, GRAMS_DECIMALS)
    if actual_consumption > estimated_grams:
        raise ValueError("actual consumption cannot exceed estimated grams")

    refund_grams = round(estimated_grams - actual_consumption, GRAMS_DECIMALS)

    return RefundResult(
        estimated_grams=estimated_grams,
        actual_consumption=actual_consumption,
        refund_grams=refund_grams,
    )
