"""Spool selection of Spooli."""

from __future__ import annotations

from pathlib import Path

from .errors import (
    InsufficientFilamentError,
    NoCompatibleSpoolError,
    SpoolNotFoundError,
)
from .models import SpoolSelectionResult
from .ports import SpoolRepository


def select_spool(
    material: str,
    required_grams: float,
    spool_id: int | None = None,
    repo: SpoolRepository | None = None,
    manual_spool_id: int | None = None,
    db_path: Path | str | None = None,
) -> SpoolSelectionResult:
    """Select a spool for a print job.

    If a manual spool id is provided, validates it exists and has
    enough material. Otherwise, finds compatible spools and returns
    the one with the lowest sufficient remaining weight, plus
    alternatives.

    ``spool_id`` is the new name; ``manual_spool_id`` is kept as a
    backwards-compatible alias. When ``repo`` is None, storage access
    is delegated to ``spooli.storage``.
    """
    if required_grams < 0:
        raise ValueError("required_grams cannot be negative")

    effective_id = manual_spool_id if manual_spool_id is not None else spool_id

    if effective_id is not None:
        if repo is not None:
            spool = repo.get_by_id(effective_id)
        else:
            from spooli.storage import get_spool_by_id

            spool = get_spool_by_id(effective_id, db_path)
        if spool is None:
            raise SpoolNotFoundError(
                f"spool with id {effective_id} does not exist"
            )
        if spool["material"] != material:
            raise ValueError(
                f"spool {effective_id} material mismatch: "
                f"expected {material}, got {spool['material']}"
            )
        if spool["remaining_weight_g"] < required_grams:
            raise InsufficientFilamentError(
                f"spool {effective_id} has insufficient filament: "
                f"{spool['remaining_weight_g']}g remaining, {required_grams}g required"
            )
        return SpoolSelectionResult(selected_spool=spool, alternatives=[])

    if repo is not None:
        compatible = repo.get_compatible(material, required_grams)
    else:
        from spooli.storage import get_compatible_spools

        compatible = get_compatible_spools(material, required_grams, db_path)
    if not compatible:
        raise NoCompatibleSpoolError(
            f"no compatible spools found for material '{material}' "
            f"with at least {required_grams}g remaining"
        )

    selected = compatible[0]
    alternatives = compatible[1:]
    return SpoolSelectionResult(selected_spool=selected, alternatives=alternatives)
