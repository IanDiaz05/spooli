"""Repository abstraction decoupling domain from storage."""

from __future__ import annotations

from typing import Protocol


class SpoolRepository(Protocol):
    """Persistence operations required by spool selection."""

    def get_by_id(self, spool_id: int) -> dict | None:
        """Return a single spool, or None when unknown."""
        ...

    def get_compatible(
        self, material: str, required_grams: float
    ) -> list[dict]:
        """Return spools of a material holding enough filament."""
        ...
