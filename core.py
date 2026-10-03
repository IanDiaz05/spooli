"""Business logic and algorithms for Spooli."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from .db import get_compatible_spools, get_spool_by_id
except ImportError:
    from db import get_compatible_spools, get_spool_by_id


@dataclass(frozen=True)
class SpoolSelectionResult:
    selected_spool: dict
    alternatives: list[dict]


@dataclass(frozen=True)
class CostBreakdown:
    filament_cost: float
    electricity_cost: float
    total_cost: float


@dataclass(frozen=True)
class RefundResult:
    estimated_grams: float
    actual_consumption: float
    refund_grams: float


def select_spool(
    material: str,
    required_grams: float,
    manual_spool_id: int | None = None,
    db_path: Path | str | None = None,
) -> SpoolSelectionResult:
    """Select a spool for a print job.

    If manual_spool_id is provided, validates it exists and has enough material.
    Otherwise, finds compatible spools and returns the one with the lowest
    sufficient remaining weight (to exhaust old spools first), plus alternatives.
    """
    if required_grams < 0:
        raise ValueError("required_grams cannot be negative")

    if manual_spool_id is not None:
        spool = get_spool_by_id(manual_spool_id, db_path)
        if spool is None:
            raise ValueError(f"spool with id {manual_spool_id} does not exist")
        if spool["material"] != material:
            raise ValueError(
                f"spool {manual_spool_id} material mismatch: "
                f"expected {material}, got {spool['material']}"
            )
        if spool["remaining_weight_g"] < required_grams:
            raise ValueError(
                f"spool {manual_spool_id} has insufficient filament: "
                f"{spool['remaining_weight_g']}g remaining, {required_grams}g required"
            )
        return SpoolSelectionResult(selected_spool=spool, alternatives=[])

    compatible = get_compatible_spools(material, required_grams, db_path)
    if not compatible:
        raise ValueError(
            f"no compatible spools found for material '{material}' "
            f"with at least {required_grams}g remaining"
        )

    selected = compatible[0]
    alternatives = compatible[1:]
    return SpoolSelectionResult(selected_spool=selected, alternatives=alternatives)


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
    electricity_cost = (printer_watts / 1000.0) * (duration_seconds / 3600.0) * kwh_cost
    total_cost = filament_cost + electricity_cost

    return CostBreakdown(
        filament_cost=round(filament_cost, 4),
        electricity_cost=round(electricity_cost, 4),
        total_cost=round(total_cost, 4),
    )


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
        if actual_usage > 100:
            raise ValueError("failure percentage cannot exceed 100")
        actual_consumption = estimated_grams * (actual_usage / 100.0)
    else:
        actual_consumption = actual_usage

    actual_consumption = round(actual_consumption, 2)
    if actual_consumption > estimated_grams:
        raise ValueError("actual consumption cannot exceed estimated grams")

    refund_grams = round(estimated_grams - actual_consumption, 2)

    return RefundResult(
        estimated_grams=estimated_grams,
        actual_consumption=actual_consumption,
        refund_grams=refund_grams,
    )