"""Spool inventory screen."""

from __future__ import annotations

from spooli.constants import ansi as _ansi
from spooli.constants.formats import (
    COL_BRAND_WIDTH,
    COL_COLOR_WIDTH,
    COL_ID_WIDTH,
    COL_MATERIAL_WIDTH,
    COL_REMAINING_WIDTH,
    PERCENT_DECIMALS,
    WEIGHT_DECIMALS,
)
from spooli.constants.thresholds import LOW_STOCK_RATIO, PERCENT_MAX
from spooli.storage import spool_repo
from spooli.ui.table import Table


def show_inventory() -> None:
    """Display the spool inventory as a formatted table."""
    try:
        spools = spool_repo.get_all_spools()
    except Exception as exc:
        print(_ansi.paint(f"Error al obtener el inventario: {exc}", _ansi.RED))
        return

    print(f"\n{_ansi.paint('=== Inventario de Bobinas ===', _ansi.BOLD, _ansi.CYAN)}")
    if not spools:
        print("No hay bobinas registradas en el inventario.")
        print("Usa la opción 'Registrar Nueva Bobina' para añadir una.")
        return

    table = Table(
        ["ID", "Marca", "Material", "Color", "Restante", "Estado"],
        [
            COL_ID_WIDTH,
            COL_BRAND_WIDTH,
            COL_MATERIAL_WIDTH,
            COL_COLOR_WIDTH,
            COL_REMAINING_WIDTH,
            len("Estado"),
        ],
    )
    header = table.header_line()
    print(header)
    print(table.separator())
    for spool in spools:
        try:
            initial = float(spool.get("initial_weight_g") or 0)
        except (TypeError, ValueError):
            initial = 0
        try:
            remaining = float(spool.get("remaining_weight_g") or 0)
        except (TypeError, ValueError):
            remaining = 0
        percent = (remaining / initial * PERCENT_MAX) if initial > 0 else 0.0
        low = initial > 0 and (remaining / initial) < LOW_STOCK_RATIO
        brand = str(spool.get("brand") or "-")
        material = str(spool.get("material") or "-")
        color = str(spool.get("color") or "-")
        remaining_text = (
            f"{remaining:.{WEIGHT_DECIMALS}f} g ({percent:.{PERCENT_DECIMALS}f}%)"
        )
        state_text = "Disponible" if not low else "Nivel bajo"
        row = table.format_row(
            [
                str(spool.get("id")),
                brand,
                material,
                color,
                remaining_text,
                state_text,
            ]
        )
        if low:
            print(_ansi.paint(row, _ansi.RED))
        else:
            print(row)
    print(f"\nTotal de bobinas: {len(spools)}")


__all__ = ["show_inventory"]
