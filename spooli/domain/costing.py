"""Cost estimation of Spooli."""

from __future__ import annotations

from spooli.constants.formats import MONEY_DECIMALS
from spooli.constants.thresholds import SECONDS_PER_HOUR, WATTS_PER_KW

from .models import CostBreakdown


def calculate_costs(
    grams: float,
    duration_seconds: int,
    spool_price: float,
    spool_initial_weight: float,
    printer_watts: float,
    kwh_cost: float,
) -> CostBreakdown:
    """Calculate estimated costs for a print job.

    Filament cost: (spool_price / spool_initial_weight) * grams
    Electricity cost: (printer_watts / 1000) * (duration_seconds / 3600) * kwh_cost
    """
    if grams < 0:
        raise ValueError("grams cannot be negative")
    if duration_seconds < 0:
        raise ValueError("duration_seconds cannot be negative")
    if spool_price < 0:
        raise ValueError("spool_price cannot be negative")
    if spool_initial_weight <= 0:
        raise ValueError("spool_initial_weight must be greater than 0")
    if printer_watts < 0:
        raise ValueError("printer_watts cannot be negative")
    if kwh_cost < 0:
        raise ValueError("kwh_cost cannot be negative")

    filament_cost = (spool_price / spool_initial_weight) * grams
    electricity_cost = (
        (printer_watts / WATTS_PER_KW)
        * (duration_seconds / SECONDS_PER_HOUR)
        * kwh_cost
    )
    total_cost = filament_cost + electricity_cost

    return CostBreakdown(
        filament_cost=round(filament_cost, MONEY_DECIMALS),
        electricity_cost=round(electricity_cost, MONEY_DECIMALS),
        total_cost=round(total_cost, MONEY_DECIMALS),
    )
