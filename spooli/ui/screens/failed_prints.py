"""Failed print registration screen."""

from __future__ import annotations

from spooli.constants import ansi as _ansi
from spooli.constants.defaults import DEFAULT_HISTORY_LIMIT
from spooli.constants.formats import (
    COL_RECENT_FILE_WIDTH,
    COL_RECENT_GRAMS_WIDTH,
    COL_RECENT_ID_WIDTH,
    FILE_NAME_RECENT_LIMIT,
    GRAMS_DECIMALS,
)
from spooli.constants.messages import MSG_INVALID_NUMBER, MSG_NO_PRINTS_YET
from spooli.domain import refunds as _refunds
from spooli.storage import print_repo
from spooli.ui.input import safe_input
from spooli.ui.table import Table


def register_failed_print() -> dict | None:
    """Register a failed print, refunding unused filament to the spool."""
    print(f"\n{_ansi.paint('=== Registrar Pieza Fallida ===', _ansi.BOLD, _ansi.CYAN)}")
    try:
        prints = print_repo.get_print_history(limit=DEFAULT_HISTORY_LIMIT)
    except Exception as exc:
        print(_ansi.paint(f"Error al obtener el historial: {exc}", _ansi.RED))
        return None

    if not prints:
        print(MSG_NO_PRINTS_YET)
        return None

    print("Impresiones recientes:")
    table = Table(
        ["ID", "Archivo", "Gramos", "Estado"],
        [
            COL_RECENT_ID_WIDTH,
            COL_RECENT_FILE_WIDTH,
            COL_RECENT_GRAMS_WIDTH,
            len("Estado"),
        ],
    )
    print(table.header_line())
    print(table.separator())
    for record in prints:
        file_cell = str(record.get("file_name") or "-")[:FILE_NAME_RECENT_LIMIT]
        grams_used = float(record.get("grams_used") or 0)
        grams_cell = f"{grams_used:.{GRAMS_DECIMALS}f}"
        print(
            table.format_row(
                [str(record.get("id")), file_cell, grams_cell, str(record.get("status"))]
            )
        )

    id_raw = safe_input("Introduce el ID de la impresión fallida: ")
    if id_raw is None:
        return None
    try:
        print_id = int(str(id_raw).strip())
    except ValueError:
        print(_ansi.paint("Error: el ID debe ser un número entero.", _ansi.RED))
        return None

    target = next((p for p in prints if int(p.get("id")) == print_id), None)
    if target is None:
        try:
            wider = print_repo.get_print_history(limit=10000)
            target = next((p for p in wider if int(p.get("id")) == print_id), None)
        except Exception:
            target = None
    if target is None:
        print(_ansi.paint(f"Error: no existe una impresión con ID {print_id}.", _ansi.RED))
        return None

    try:
        estimated = float(target.get("grams_used") or 0)
    except (TypeError, ValueError):
        estimated = 0.0

    print("Método de ajuste:")
    print("  1. Porcentaje de la pieza completado (0-100)")
    print("  2. Gramos reales pesados del desperdicio")
    method_raw = safe_input("Selecciona el método (1/2): ")
    if method_raw is None:
        return None
    method = method_raw.strip()
    if method not in ("1", "2"):
        print(_ansi.paint("Error: debes elegir 1 o 2.", _ansi.RED))
        return None

    is_percent = method == "1"
    if is_percent:
        value_raw = safe_input("Porcentaje completado (0-100): ")
    else:
        value_raw = safe_input("Gramos reales consumidos: ")
    if value_raw is None:
        return None
    try:
        value = float(value_raw.strip().replace(",", "."))
    except ValueError:
        print(_ansi.paint(MSG_INVALID_NUMBER, _ansi.RED))
        return None

    try:
        refund = _refunds.calculate_refund(estimated, value, is_percent=is_percent)
    except Exception as exc:
        print(_ansi.paint(f"Error al calcular la devolución: {exc}", _ansi.RED))
        return None

    try:
        updated = print_repo.update_failed_print(print_id, float(refund.actual_consumption))
    except Exception as exc:
        print(_ansi.paint(f"Error al actualizar la impresión: {exc}", _ansi.RED))
        return None

    print(_ansi.paint(f"Impresión {print_id} marcada como fallida.", _ansi.GREEN))
    print(f"Consumo estimado: {refund.estimated_grams:.{GRAMS_DECIMALS}f} g")
    print(f"Consumo real: {refund.actual_consumption:.{GRAMS_DECIMALS}f} g")
    print(
        "Filamento devuelto a la bobina: "
        f"{refund.refund_grams:.{GRAMS_DECIMALS}f} g"
    )
    return updated


__all__ = ["register_failed_print"]
