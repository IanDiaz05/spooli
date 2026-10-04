"""Print history screen."""

from __future__ import annotations

from spooli.constants import ansi as _ansi
from spooli.constants.defaults import DEFAULT_HISTORY_LIMIT, DEFAULT_SETTINGS, SettingKey
from spooli.constants.formats import (
    COL_HISTORY_COST_VALUE_WIDTH,
    COL_HISTORY_COST_WIDTH,
    COL_HISTORY_FILE_WIDTH,
    COL_HISTORY_GRAMS_WIDTH,
    COL_HISTORY_SPOOL_WIDTH,
    COL_ID_WIDTH,
    FILE_NAME_HISTORY_LIMIT,
    GRAMS_DECIMALS,
    MONEY_DECIMALS,
)
from spooli.constants.messages import MSG_NO_PRINTS_YET
from spooli.services.pricing import resolve_record_cost
from spooli.storage import print_repo
from spooli.storage import settings_store
from spooli.ui.table import Table


def show_history(limit: int = DEFAULT_HISTORY_LIMIT) -> None:
    """Display recent print jobs with their cost breakdown."""
    print(f"\n{_ansi.paint('=== Historial de Impresiones ===', _ansi.BOLD, _ansi.CYAN)}")
    try:
        prints = print_repo.get_print_history(limit=limit)
    except Exception as exc:
        print(_ansi.paint(f"Error al obtener el historial: {exc}", _ansi.RED))
        return

    if not prints:
        print(MSG_NO_PRINTS_YET)
        return

    fallback_currency = DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
    default_currency = (
        settings_store.get_setting(SettingKey.CURRENCY_SYMBOL.value) or fallback_currency
    ).strip() or fallback_currency
    table = Table(
        ["ID", "Archivo", "Bobina", "Gramos", "Costo", "Estado"],
        [
            COL_ID_WIDTH,
            COL_HISTORY_FILE_WIDTH,
            COL_HISTORY_SPOOL_WIDTH,
            COL_HISTORY_GRAMS_WIDTH,
            COL_HISTORY_COST_WIDTH,
            len("Estado"),
        ],
    )
    header = table.header_line()
    print(header)
    print(table.separator())
    total_cost = 0.0
    total_grams = 0.0
    for record in prints:
        cost, record_currency = resolve_record_cost(record, default_currency)
        try:
            grams = float(record.get("grams_used") or 0)
        except (TypeError, ValueError):
            grams = 0.0
        total_cost += cost
        total_grams += grams
        file_cell = str(record.get("file_name") or "-")[:FILE_NAME_HISTORY_LIMIT]
        cost_cell = f"{record_currency}{cost:<{COL_HISTORY_COST_VALUE_WIDTH}.{MONEY_DECIMALS}f}"
        grams_cell = f"{grams:.{GRAMS_DECIMALS}f}"
        print(
            table.format_row(
                [
                    str(record.get("id")),
                    file_cell,
                    str(record.get("spool_id")),
                    grams_cell,
                    cost_cell,
                    str(record.get("status")),
                ]
            )
        )
    print(table.separator())
    print(f"Total impresiones: {len(prints)}")
    print(f"Filamento total consumido: {total_grams:.{GRAMS_DECIMALS}f} g")
    print(f"Costo total: {default_currency}{total_cost:.{MONEY_DECIMALS}f}")


__all__ = ["show_history"]
