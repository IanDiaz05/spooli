"""Connection lifecycle management for the Spooli database."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

from .paths import get_db_path

# Every storage function accepts an optional explicit database location.
DbPath = Union[Path, str, None]


def resolve_db_path(db_path: DbPath = None) -> Path:
    """Return the given path, or the active database path when omitted."""
    if db_path is None:
        return get_db_path()
    return Path(db_path)


def get_connection(db_path: DbPath = None) -> sqlite3.Connection:
    """Open a connection whose rows are addressable by column name."""
    target = resolve_db_path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection_scope(db_path: DbPath = None) -> Iterator[sqlite3.Connection]:
    """Yield a connection, committing on success and closing it always.

    Errors roll the pending transaction back and propagate, and the close in
    the final block guarantees no connection outlives the block (defect D2).
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
