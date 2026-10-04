"""SQLite persistence layer for Spooli."""

import os
import sqlite3
from pathlib import Path

from spooli.constants.defaults import (
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_SETTINGS,
    DEFAULT_WEIGHT_G_FLOAT,
    SettingKey,
)
from spooli.constants.formats import MONEY_FORMAT
from spooli.constants.paths import APP_DIR_NAME, DB_FILE_NAME


def get_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        data_dir = Path(base) / APP_DIR_NAME if base else Path.home() / APP_DIR_NAME
    else:
        data_dir = Path.home() / f".{APP_DIR_NAME}"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    return get_data_dir() / DB_FILE_NAME


def get_connection(path: Path | str | None = None) -> sqlite3.Connection:
    db_path = Path(path) if path is not None else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | str | None = None) -> Path:
    db_path = Path(path) if path is not None else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material TEXT NOT NULL,
                brand TEXT,
                color TEXT,
                initial_weight_g REAL NOT NULL CHECK (initial_weight_g > 0),
                remaining_weight_g REAL NOT NULL CHECK (remaining_weight_g >= 0),
                purchase_price REAL NOT NULL DEFAULT 0 CHECK (purchase_price >= 0),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spool_id INTEGER NOT NULL REFERENCES spools(id) ON DELETE RESTRICT,
                file_name TEXT NOT NULL,
                grams_used REAL NOT NULL CHECK (grams_used >= 0),
                duration_seconds INTEGER NOT NULL DEFAULT 0 CHECK (duration_seconds >= 0),
                cost REAL NOT NULL DEFAULT 0 CHECK (cost >= 0),
                filament_cost REAL NOT NULL DEFAULT 0 CHECK (filament_cost >= 0),
                electricity_cost REAL NOT NULL DEFAULT 0 CHECK (electricity_cost >= 0),
                total_cost REAL NOT NULL DEFAULT 0 CHECK (total_cost >= 0),
                currency_symbol TEXT NOT NULL DEFAULT '$',
                status TEXT NOT NULL DEFAULT 'completed',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Safe migration for databases created before snapshot fields existed.
        existing = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(prints)").fetchall()
        }
        if "filament_cost" not in existing:
            conn.execute(
                "ALTER TABLE prints ADD COLUMN filament_cost REAL NOT NULL DEFAULT 0"
            )
        if "electricity_cost" not in existing:
            conn.execute(
                "ALTER TABLE prints ADD COLUMN electricity_cost REAL NOT NULL DEFAULT 0"
            )
        if "total_cost" not in existing:
            conn.execute(
                "ALTER TABLE prints ADD COLUMN total_cost REAL NOT NULL DEFAULT 0"
            )
        if "currency_symbol" not in existing:
            conn.execute(
                "ALTER TABLE prints ADD COLUMN currency_symbol TEXT DEFAULT '$'"
            )
            conn.execute(
                "UPDATE prints SET currency_symbol = '$' WHERE currency_symbol IS NULL"
            )
        conn.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            list(DEFAULT_SETTINGS.items()),
        )
        conn.commit()

    return db_path


def get_setting(key: str, path: Path | str | None = None) -> str | None:
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str, path: Path | str | None = None) -> None:
    with get_connection(path) as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        conn.commit()


def create_spool(
    material: str,
    color: str | None = None,
    initial_weight_g: float = DEFAULT_WEIGHT_G_FLOAT,
    purchase_price: float = 0.0,
    brand: str | None = None,
    remaining_weight_g: float | None = None,
    path: Path | str | None = None,
) -> int:
    if not material or not material.strip():
        raise ValueError("material must be a non-empty string")
    if initial_weight_g <= 0:
        raise ValueError("initial_weight_g must be greater than 0")
    if purchase_price < 0:
        raise ValueError("purchase_price cannot be negative")

    remaining = (
        float(initial_weight_g)
        if remaining_weight_g is None
        else float(remaining_weight_g)
    )
    if remaining < 0 or remaining > float(initial_weight_g):
        raise ValueError("remaining_weight_g must be within [0, initial_weight_g]")

    with get_connection(path) as conn:
        cur = conn.execute(
            """
            INSERT INTO spools
                (material, brand, color, initial_weight_g, remaining_weight_g, purchase_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                material.strip(),
                brand,
                color,
                float(initial_weight_g),
                remaining,
                float(purchase_price),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_all_spools(path: Path | str | None = None) -> list[dict]:
    with get_connection(path) as conn:
        rows = conn.execute("SELECT * FROM spools ORDER BY id ASC").fetchall()
        return [dict(row) for row in rows]


def get_spool_by_id(
    spool_id: int, path: Path | str | None = None
) -> dict | None:
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT * FROM spools WHERE id = ?", (spool_id,)
        ).fetchone()
        return dict(row) if row else None


def get_compatible_spools(
    material: str,
    required_grams: float,
    path: Path | str | None = None,
) -> list[dict]:
    if required_grams < 0:
        raise ValueError("required_grams cannot be negative")
    with get_connection(path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM spools
            WHERE material = ? AND remaining_weight_g >= ?
            ORDER BY remaining_weight_g ASC
            """,
            (material, float(required_grams)),
        ).fetchall()
        return [dict(row) for row in rows]


def record_print_job(
    spool_id: int,
    file_name: str,
    grams_used: float,
    duration_seconds: int = 0,
    cost: float = 0.0,
    status: str = "completed",
    path: Path | str | None = None,
    filament_cost: float | None = None,
    electricity_cost: float | None = None,
    total_cost: float | None = None,
    currency_symbol: str | None = None,
) -> int:
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

    conn = get_connection(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        spool = conn.execute(
            "SELECT id, remaining_weight_g FROM spools WHERE id = ?",
            (spool_id,),
        ).fetchone()
        if spool is None:
            raise ValueError(f"spool with id {spool_id} does not exist")
        if spool["remaining_weight_g"] < float(grams_used):
            raise ValueError("spool does not have enough remaining filament")

        # Resolve active currency symbol, defaulting to stored setting or '$'.
        resolved_currency = currency_symbol
        if resolved_currency is None or not str(resolved_currency).strip():
            try:
                row = conn.execute(
                    "SELECT value FROM settings WHERE key = 'currency_symbol'"
                ).fetchone()
                resolved_currency = (
                    row["value"]
                    if row and row["value"]
                    else DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
                )
            except Exception:
                resolved_currency = DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
        resolved_currency = str(resolved_currency)

        # Detect available snapshot columns (supports pre-migration databases).
        cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(prints)").fetchall()
        }
        has_filament = "filament_cost" in cols
        has_electricity = "electricity_cost" in cols
        has_total = "total_cost" in cols
        has_currency = "currency_symbol" in cols

        columns = ["spool_id", "file_name", "grams_used", "duration_seconds", "cost", "status"]
        values: list = [
            spool_id,
            file_name.strip(),
            float(grams_used),
            int(duration_seconds),
            resolved_total,
            status,
        ]
        if has_filament:
            columns.append("filament_cost")
            values.append(resolved_filament)
        if has_electricity:
            columns.append("electricity_cost")
            values.append(resolved_electricity)
        if has_total:
            columns.append("total_cost")
            values.append(resolved_total)
        if has_currency:
            columns.append("currency_symbol")
            values.append(resolved_currency)

        placeholders = ", ".join(["?"] * len(columns))
        cur = conn.execute(
            f"INSERT INTO prints ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values),
        )
        conn.execute(
            "UPDATE spools SET remaining_weight_g = remaining_weight_g - ? WHERE id = ?",
            (float(grams_used), spool_id),
        )
        conn.execute("COMMIT")
        return int(cur.lastrowid)
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def update_failed_print(
    print_id: int,
    actual_grams_used: float,
    path: Path | str | None = None,
) -> dict:
    if actual_grams_used < 0:
        raise ValueError("actual_grams_used cannot be negative")

    conn = get_connection(path)
    try:
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
        conn.execute("COMMIT")

        updated = conn.execute(
            "SELECT * FROM prints WHERE id = ?", (print_id,)
        ).fetchone()
        return dict(updated)
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def convert_all_spools_currency(
    multiplier: float, path: Path | str | None = None
) -> int:
    # Convert every spool purchase_price by multiplier, atomically.
    try:
        factor = float(multiplier)
    except (TypeError, ValueError):
        raise ValueError("multiplier must be a valid number")
    if factor <= 0:
        raise ValueError("multiplier must be greater than 0")

    conn = get_connection(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            "UPDATE spools SET purchase_price = ROUND(purchase_price * ?, 2)",
            (factor,),
        )
        updated = cur.rowcount if cur.rowcount is not None else 0
        conn.execute("COMMIT")
        return int(updated)
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def convert_all_records_currency(
    multiplier: float, new_currency: str, path: Path | str | None = None
) -> dict:
    # Convert spools and historical prints atomically to a new currency.
    try:
        factor = float(multiplier)
    except (TypeError, ValueError):
        raise ValueError("multiplier must be a valid number")
    if factor <= 0:
        raise ValueError("multiplier must be greater than 0")
    if not new_currency or not str(new_currency).strip():
        raise ValueError("new_currency must be a non-empty string")
    symbol = str(new_currency).strip()

    with get_connection(path) as conn:
        spools_cur = conn.execute(
            "UPDATE spools SET purchase_price = ROUND(purchase_price * ?, 2)",
            (factor,),
        )
        spools_updated = (
            spools_cur.rowcount if spools_cur.rowcount is not None else 0
        )
        prints_cur = conn.execute(
            "UPDATE prints SET filament_cost = ROUND(filament_cost * ?, 4), "
            "electricity_cost = ROUND(electricity_cost * ?, 4), "
            "total_cost = ROUND(total_cost * ?, 4), "
            "cost = ROUND(cost * ?, 4), "
            "currency_symbol = ?",
            (factor, factor, factor, factor, symbol),
        )
        prints_updated = (
            prints_cur.rowcount if prints_cur.rowcount is not None else 0
        )
        return {"spools": int(spools_updated), "prints": int(prints_updated)}


def get_print_history(
    limit: int = DEFAULT_HISTORY_LIMIT, path: Path | str | None = None
) -> list[dict]:
    # Return recent prints, each keeping its own recorded currency symbol.
    with get_connection(path) as conn:
        rows = conn.execute(
            "SELECT * FROM prints ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        history: list[dict] = []
        for row in rows:
            record = dict(row)
            symbol = record.get("currency_symbol")
            if symbol is None or not str(symbol).strip():
                record["currency_symbol"] = DEFAULT_SETTINGS[
                    SettingKey.CURRENCY_SYMBOL.value
                ]
            try:
                amount = float(
                    record.get("total_cost")
                    if record.get("total_cost") is not None
                    else record.get("cost") or 0
                )
            except (TypeError, ValueError):
                amount = 0.0
            record["display_cost"] = (
                f"{record['currency_symbol']}{amount:{MONEY_FORMAT}}"
            )
            history.append(record)
        return history
