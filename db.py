"""SQLite persistence layer for Spooli."""

import os
import sqlite3
from pathlib import Path

APP_DIR_NAME = "spooli"
DB_FILE_NAME = "filament.db"

DEFAULT_SETTINGS = {
    "electricity_kwh_cost": "0.15",
    "printer_power_watts": "150",
    "currency_symbol": "$",
}


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
                status TEXT NOT NULL DEFAULT 'completed',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
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
    initial_weight_g: float = 1000.0,
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
) -> int:
    if not file_name or not file_name.strip():
        raise ValueError("file_name must be a non-empty string")
    if grams_used <= 0:
        raise ValueError("grams_used must be greater than 0")
    if duration_seconds < 0:
        raise ValueError("duration_seconds cannot be negative")
    if cost < 0:
        raise ValueError("cost cannot be negative")

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

        cur = conn.execute(
            """
            INSERT INTO prints
                (spool_id, file_name, grams_used, duration_seconds, cost, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                spool_id,
                file_name.strip(),
                float(grams_used),
                int(duration_seconds),
                float(cost),
                status,
            ),
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
