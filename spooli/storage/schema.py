"""Schema creation and migrations of the Spooli database."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from spooli.constants.defaults import DEFAULT_SETTINGS

from .connection import DbPath, connection_scope, resolve_db_path

SETTINGS_TABLE = "settings"
SPOOLS_TABLE = "spools"
PRINTS_TABLE = "prints"

# Cost snapshot columns stored with every print job.
SNAPSHOT_COLUMNS: tuple[str, ...] = (
    "filament_cost",
    "electricity_cost",
    "total_cost",
    "currency_symbol",
)

SETTINGS_DDL = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

SPOOLS_DDL = """
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

PRINTS_DDL = """
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

# Executed in order on every initialisation.
SCHEMA_STATEMENTS: tuple[str, ...] = (SETTINGS_DDL, SPOOLS_DDL, PRINTS_DDL)


@dataclass(frozen=True)
class ColumnMigration:
    """A column added to an already released database."""

    table: str
    column: str
    definition: str
    backfill: Optional[str] = None


# Applied in order; entries already present in the database are skipped.
MIGRATIONS: tuple[ColumnMigration, ...] = (
    ColumnMigration(PRINTS_TABLE, "filament_cost", "REAL NOT NULL DEFAULT 0"),
    ColumnMigration(PRINTS_TABLE, "electricity_cost", "REAL NOT NULL DEFAULT 0"),
    ColumnMigration(PRINTS_TABLE, "total_cost", "REAL NOT NULL DEFAULT 0"),
    ColumnMigration(
        PRINTS_TABLE,
        "currency_symbol",
        "TEXT DEFAULT '$'",
        "UPDATE prints SET currency_symbol = '$' WHERE currency_symbol IS NULL",
    ),
)


def get_column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the column names of a table, identified by our own schema."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def missing_columns(
    conn: sqlite3.Connection, table: str, columns: tuple[str, ...]
) -> set[str]:
    """Return the subset of columns the table does not have yet."""
    present = get_column_names(conn, table)
    return {column for column in columns if column not in present}


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Bring an existing database up to the current schema."""
    present = {
        migration.table: get_column_names(conn, migration.table)
        for migration in MIGRATIONS
    }
    for migration in MIGRATIONS:
        known = present[migration.table]
        if migration.column in known:
            continue
        # Table and column names come from the constants declared above.
        conn.execute(
            f"ALTER TABLE {migration.table} ADD COLUMN "
            f"{migration.column} {migration.definition}"
        )
        known.add(migration.column)
        if migration.backfill is not None:
            conn.execute(migration.backfill)


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the tables, apply the migrations and seed the defaults."""
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    apply_migrations(conn)
    conn.executemany(
        f"INSERT OR IGNORE INTO {SETTINGS_TABLE} (key, value) VALUES (?, ?)",
        list(DEFAULT_SETTINGS.items()),
    )


def init_db(path: DbPath = None) -> Path:
    """Prepare the database at the given location and return its path."""
    db_path = resolve_db_path(path)
    with connection_scope(db_path) as conn:
        create_schema(conn)
    return db_path
