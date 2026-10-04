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


@dataclass(frozen=True, init=False)
class PrintMetadata:
    """Result of parsing a slicer file.

    Canonical fields use the ``filament_used_*`` / ``print_duration_*``
    naming. Legacy ``grams`` / ``length_mm`` / ``duration_seconds``
    aliases are kept for backwards compatibility.
    """

    file_name: str
    material: str
    filament_used_g: float
    print_duration_seconds: int
    filament_used_mm: float

    def __init__(
        self,
        file_name: str = "",
        material: str = "UNKNOWN",
        filament_used_g: float = 0.0,
        print_duration_seconds: int = 0,
        filament_used_mm: float = 0.0,
        grams: float | None = None,
        length_mm: float | None = None,
        duration_seconds: int | None = None,
    ) -> None:
        if grams is not None:
            filament_used_g = float(grams)
        if length_mm is not None:
            filament_used_mm = float(length_mm)
        if duration_seconds is not None:
            print_duration_seconds = int(duration_seconds)
        object.__setattr__(self, "file_name", file_name)
        object.__setattr__(self, "material", material)
        object.__setattr__(self, "filament_used_g", float(filament_used_g))
        object.__setattr__(
            self, "print_duration_seconds", int(print_duration_seconds)
        )
        object.__setattr__(self, "filament_used_mm", float(filament_used_mm))

    @property
    def grams(self) -> float:
        return self.filament_used_g

    @property
    def length_mm(self) -> float:
        return self.filament_used_mm

    @property
    def duration_seconds(self) -> int:
        return self.print_duration_seconds
