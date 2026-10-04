"""Domain subpackage of Spooli."""

from .costing import calculate_costs
from .errors import (
    DomainError,
    InsufficientFilamentError,
    NoCompatibleSpoolError,
    SpoolNotFoundError,
    SpooliError,
)
from .models import CostBreakdown, RefundResult, SpoolSelectionResult
from .ports import SpoolRepository
from .refunds import calculate_refund
from .selection import select_spool

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
