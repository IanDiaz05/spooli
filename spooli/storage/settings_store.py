"""Access to the key/value settings table."""

from .connection import DbPath, connection_scope


def get_setting(
    key: str, path: DbPath = None, default: str | None = None
) -> str | None:
    """Return the value of a setting.

    ``path`` stays the second positional parameter of the former ``db`` API,
    so pass ``default`` by keyword to request a fallback value.
    """
    with connection_scope(path) as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    if row is None:
        return default
    return row["value"]


def get_float_setting(
    key: str, path: DbPath = None, default: float = 0.0
) -> float:
    """Return a setting as a float, falling back on missing or invalid data."""
    raw = get_setting(key, path)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def set_setting(key: str, value: str, path: DbPath = None) -> None:
    """Insert a setting, replacing the value of an existing key."""
    with connection_scope(path) as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
