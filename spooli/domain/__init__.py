"""Domain subpackage of Spooli."""

from .costing import calculate_costs
from .errors import (
    DomainError,
    InsufficientFilamentError,
    MissingMetadataError,
    NoCompatibleSpoolError,
    SpoolNotFoundError,
    SpooliError,
    UnsupportedFormatError,
)
from .models import CostBreakdown, PrintMetadata, RefundResult, SpoolSelectionResult
from .ports import SpoolRepository
from .refunds import calculate_refund
from .selection import select_spool

__all__ = [
    "CostBreakdown",
    "DomainError",
    "InsufficientFilamentError",
    "MissingMetadataError",
    "NoCompatibleSpoolError",
    "PrintMetadata",
    "RefundResult",
    "SpooliError",
    "SpoolNotFoundError",
    "SpoolRepository",
    "SpoolSelectionResult",
    "UnsupportedFormatError",
    "calculate_costs",
    "calculate_refund",
    "select_spool",
]
