"""Domain models of Spooli."""

from __future__ import annotations

from dataclasses import dataclass


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
