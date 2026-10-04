"""Business logic and algorithms for Spooli.

Backwards-compatible facade over :mod:`spooli.domain`.
"""

from __future__ import annotations

from spooli.domain import (
    CostBreakdown,
    DomainError,
    InsufficientFilamentError,
    NoCompatibleSpoolError,
    RefundResult,
    SpooliError,
    SpoolNotFoundError,
    SpoolRepository,
    SpoolSelectionResult,
    calculate_costs,
    calculate_refund,
    select_spool,
)

__all__ = [
    "CostBreakdown",
    "DomainError",
    "InsufficientFilamentError",
    "NoCompatibleSpoolError",
    "RefundResult",
    "SpooliError",
    "SpoolNotFoundError",
    "SpoolRepository",
    "SpoolSelectionResult",
    "calculate_costs",
    "calculate_refund",
    "select_spool",
]
