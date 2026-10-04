"""Print summary rendering."""

from __future__ import annotations

from spooli.constants.formats import GRAMS_DECIMALS, MONEY_DECIMALS
from spooli.ui.console import format_duration


def display_summary(metadata, spool: dict, costs, currency: str) -> None:
    """Print the print-job summary."""
    remaining_after = float(spool["remaining_weight_g"]) - float(metadata.grams)
    label_parts = [str(spool.get("brand") or "").strip(), str(spool.get("color") or "").strip()]
    spool_name = " ".join(p for p in label_parts if p) or "Sin nombre"
    print("--- Resumen de impresión ---")
    print(f"Archivo: {metadata.file_name}")
    print(f"Material: {metadata.material}")
    print(f"Peso requerido: {metadata.grams:.{GRAMS_DECIMALS}f} g")
    print(f"Duración estimada: {format_duration(metadata.duration_seconds)}")
    print(f"Bobina asignada: ID {spool['id']} ({spool_name})")
    print(f"Restante en bobina: {float(spool['remaining_weight_g']):.{GRAMS_DECIMALS}f} g")
    print(f"Restante tras impresión: {remaining_after:.{GRAMS_DECIMALS}f} g")
    print(f"Costo filamento: {currency}{costs.filament_cost:.{MONEY_DECIMALS}f}")
    print(f"Costo electricidad: {currency}{costs.electricity_cost:.{MONEY_DECIMALS}f}")
    print(f"Costo total estimado: {currency}{costs.total_cost:.{MONEY_DECIMALS}f}")


__all__ = ["display_summary", "format_duration"]
