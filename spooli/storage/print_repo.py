"""Persistence operations over the print jobs."""

import sqlite3

from spooli.constants.defaults import (
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_SETTINGS,
    SettingKey,
)
from spooli.constants.formats import MONEY_FORMAT

from .connection import DbPath, connection_scope
from .schema import PRINTS_TABLE, SNAPSHOT_COLUMNS, missing_columns


def _resolve_currency(conn: sqlite3.Connection, currency_symbol: str | None) -> str:
    """Return the requested symbol, or the one stored in the settings."""
    if currency_symbol is not None and str(currency_symbol).strip():
        return str(currency_symbol)
    fallback = DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (SettingKey.CURRENCY_SYMBOL.value,),
        ).fetchone()
    except sqlite3.Error:
        return fallback
    return row["value"] if row and row["value"] else fallback


def _build_history_record(row: sqlite3.Row) -> dict:
    """Add the display amount to a stored print job."""
    record = dict(row)
    symbol = record.get("currency_symbol")
    if symbol is None or not str(symbol).strip():
        record["currency_symbol"] = DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
    try:
        amount = float(
            record.get("total_cost")
            if record.get("total_cost") is not None
            else record.get("cost") or 0
        )
    except (TypeError, ValueError):
        amount = 0.0
    record["display_cost"] = f"{record['currency_symbol']}{amount:{MONEY_FORMAT}}"
    return record


def record_print_job(
    spool_id: int,
    file_name: str,
    grams_used: float,
    duration_seconds: int = 0,
    cost: float = 0.0,
    status: str = "completed",
    path: DbPath = None,
    filament_cost: float | None = None,
    electricity_cost: float | None = None,
    total_cost: float | None = None,
    currency_symbol: str | None = None,
) -> int:
    """Store a print job and deduct its filament in a single transaction."""
    if not file_name or not file_name.strip():
        raise ValueError("file_name must be a non-empty string")
    if grams_used <= 0:
        raise ValueError("grams_used must be greater than 0")
    if duration_seconds < 0:
        raise ValueError("duration_seconds cannot be negative")
    if cost < 0:
        raise ValueError("cost cannot be negative")

    # Resolve snapshot costs, keeping backwards compatibility with cost.
    resolved_total = float(total_cost) if total_cost is not None else float(cost)
    if resolved_total < 0:
        raise ValueError("total_cost cannot be negative")
    resolved_filament = (
        float(filament_cost) if filament_cost is not None else resolved_total
    )
    if resolved_filament < 0:
        raise ValueError("filament_cost cannot be negative")
    resolved_electricity = (
        float(electricity_cost) if electricity_cost is not None else 0.0
    )
    if resolved_electricity < 0:
        raise ValueError("electricity_cost cannot be negative")

    with connection_scope(path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        spool = conn.execute(
            "SELECT id, remaining_weight_g FROM spools WHERE id = ?",
            (spool_id,),
        ).fetchone()
        if spool is None:
            raise ValueError(f"spool with id {spool_id} does not exist")
        if spool["remaining_weight_g"] < float(grams_used):
            raise ValueError("spool does not have enough remaining filament")

        symbol = _resolve_currency(conn, currency_symbol)

        columns = [
            "spool_id",
            "file_name",
            "grams_used",
            "duration_seconds",
            "cost",
            "status",
        ]
        values: list = [
            spool_id,
            file_name.strip(),
            float(grams_used),
            int(duration_seconds),
            resolved_total,
            status,
        ]
        # Legacy databases may still lack the snapshot columns.
        snapshot_values = {
            "filament_cost": resolved_filament,
            "electricity_cost": resolved_electricity,
            "total_cost": resolved_total,
            "currency_symbol": symbol,
        }
        absent = missing_columns(conn, PRINTS_TABLE, SNAPSHOT_COLUMNS)
        for name in SNAPSHOT_COLUMNS:
            if name not in absent:
                columns.append(name)
                values.append(snapshot_values[name])

        placeholders = ", ".join(["?"] * len(columns))
        cursor = conn.execute(
            f"INSERT INTO prints ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values),
        )
        conn.execute(
            "UPDATE spools SET remaining_weight_g = remaining_weight_g - ? WHERE id = ?",
            (float(grams_used), spool_id),
        )
        return int(cursor.lastrowid)


def update_failed_print(
    print_id: int,
    actual_grams_used: float,
    path: DbPath = None,
) -> dict:
    """Flag a print job as failed and refund its unused filament."""
    if actual_grams_used < 0:
        raise ValueError("actual_grams_used cannot be negative")

    with connection_scope(path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        record = conn.execute(
            "SELECT * FROM prints WHERE id = ?", (print_id,)
        ).fetchone()
        if record is None:
            raise ValueError(f"print with id {print_id} does not exist")

        previous = float(record["grams_used"])
        refund = previous - float(actual_grams_used)
        if refund < 0:
            spool = conn.execute(
                "SELECT remaining_weight_g FROM spools WHERE id = ?",
                (record["spool_id"],),
            ).fetchone()
            if spool is None or spool["remaining_weight_g"] < abs(refund):
                raise ValueError("spool does not have enough filament for adjustment")

        conn.execute(
            "UPDATE prints SET grams_used = ?, status = 'failed' WHERE id = ?",
            (float(actual_grams_used), print_id),
        )
        conn.execute(
            "UPDATE spools SET remaining_weight_g = remaining_weight_g + ? WHERE id = ?",
            (refund, record["spool_id"]),
        )
        updated = conn.execute(
            "SELECT * FROM prints WHERE id = ?", (print_id,)
        ).fetchone()
        return dict(updated)


def convert_all_records_currency(
    multiplier: float, new_currency: str, path: DbPath = None
) -> dict:
    """Convert spool prices and historical costs to a new currency."""
    try:
        factor = float(multiplier)
    except (TypeError, ValueError):
        raise ValueError("multiplier must be a valid number")
    if factor <= 0:
        raise ValueError("multiplier must be greater than 0")
    if not new_currency or not str(new_currency).strip():
        raise ValueError("new_currency must be a non-empty string")
    symbol = str(new_currency).strip()

    with connection_scope(path) as conn:
        spools_cursor = conn.execute(
            "UPDATE spools SET purchase_price = ROUND(purchase_price * ?, 2)",
            (factor,),
        )
        prints_cursor = conn.execute(
            "UPDATE prints SET filament_cost = ROUND(filament_cost * ?, 4), "
            "electricity_cost = ROUND(electricity_cost * ?, 4), "
            "total_cost = ROUND(total_cost * ?, 4), "
            "cost = ROUND(cost * ?, 4), "
            "currency_symbol = ?",
            (factor, factor, factor, factor, symbol),
        )
        return {
            "spools": int(spools_cursor.rowcount or 0),
            "prints": int(prints_cursor.rowcount or 0),
        }


def get_print_history(
    limit: int = DEFAULT_HISTORY_LIMIT, path: DbPath = None
) -> list[dict]:
    """Return the most recent print jobs, newest first.

    Every record keeps its own recorded currency symbol.
    """
    with connection_scope(path) as conn:
        rows = conn.execute(
            "SELECT * FROM prints ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [_build_history_record(row) for row in rows]
