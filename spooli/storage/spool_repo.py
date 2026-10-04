"""Persistence operations over the spool inventory."""

from spooli.constants.defaults import DEFAULT_WEIGHT_G_FLOAT

from .connection import DbPath, connection_scope


def create_spool(
    material: str,
    color: str | None = None,
    initial_weight_g: float = DEFAULT_WEIGHT_G_FLOAT,
    purchase_price: float = 0.0,
    brand: str | None = None,
    remaining_weight_g: float | None = None,
    path: DbPath = None,
) -> int:
    """Insert a new spool and return its identifier."""
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

    with connection_scope(path) as conn:
        cursor = conn.execute(
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
        return int(cursor.lastrowid)


def get_all_spools(path: DbPath = None) -> list[dict]:
    """Return every spool, oldest identifier first."""
    with connection_scope(path) as conn:
        rows = conn.execute("SELECT * FROM spools ORDER BY id ASC").fetchall()
        return [dict(row) for row in rows]


def get_spool_by_id(spool_id: int, path: DbPath = None) -> dict | None:
    """Return a single spool, or None when the identifier is unknown."""
    with connection_scope(path) as conn:
        row = conn.execute(
            "SELECT * FROM spools WHERE id = ?", (spool_id,)
        ).fetchone()
        return dict(row) if row else None


def get_compatible_spools(
    material: str,
    required_grams: float,
    path: DbPath = None,
) -> list[dict]:
    """Return the spools of a material holding enough filament.

    Ordered by remaining weight ascending to exhaust the oldest spools first.
    """
    if required_grams < 0:
        raise ValueError("required_grams cannot be negative")
    with connection_scope(path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM spools
            WHERE material = ? AND remaining_weight_g >= ?
            ORDER BY remaining_weight_g ASC
            """,
            (material, float(required_grams)),
        ).fetchall()
        return [dict(row) for row in rows]
