"""New spool creation wizard."""

from __future__ import annotations

from spooli.constants import ansi as _ansi
from spooli.constants.defaults import (
    DEFAULT_BRAND,
    DEFAULT_COLOR,
    DEFAULT_MATERIAL,
    DEFAULT_PRICE,
    DEFAULT_WEIGHT_G,
)
from spooli.storage import spool_repo
from spooli.ui.input import safe_input


def create_spool_form() -> int | None:
    """Guide the user through spool creation. Returns new spool id or None."""
    print(f"\n{_ansi.paint('=== Registrar Nueva Bobina ===', _ansi.BOLD, _ansi.CYAN)}")
    print(_ansi.paint("(Pulsa Enter para aceptar el valor por defecto)", _ansi.CYAN))

    brand_raw = safe_input(f"Marca [{DEFAULT_BRAND}]: ")
    if brand_raw is None:
        return None
    material_raw = safe_input(f"Material [{DEFAULT_MATERIAL}]: ")
    if material_raw is None:
        return None
    color_raw = safe_input(f"Color [{DEFAULT_COLOR}]: ")
    if color_raw is None:
        return None
    weight_raw = safe_input(f"Peso inicial en gramos [{DEFAULT_WEIGHT_G}]: ")
    if weight_raw is None:
        return None
    price_raw = safe_input(f"Precio de compra [{DEFAULT_PRICE}]: ")
    if price_raw is None:
        return None

    brand = brand_raw.strip() or DEFAULT_BRAND
    material = material_raw.strip() or DEFAULT_MATERIAL
    color = color_raw.strip() or DEFAULT_COLOR

    if not material:
        print(_ansi.paint("Error: el material no puede estar vacío.", _ansi.RED))
        return None

    weight_text = weight_raw.strip().replace(",", ".") or DEFAULT_WEIGHT_G
    try:
        initial_weight = float(weight_text)
    except ValueError:
        print(_ansi.paint("Error: el peso inicial debe ser un número válido.", _ansi.RED))
        return None
    if initial_weight <= 0:
        print(_ansi.paint("Error: el peso inicial debe ser mayor que cero.", _ansi.RED))
        return None

    price_text = price_raw.strip().replace(",", ".") or DEFAULT_PRICE
    try:
        price = float(price_text)
    except ValueError:
        print(_ansi.paint("Error: el precio debe ser un número válido.", _ansi.RED))
        return None
    if price < 0:
        print(_ansi.paint("Error: el precio no puede ser negativo.", _ansi.RED))
        return None

    try:
        spool_id = spool_repo.create_spool(
            material=material,
            color=color,
            initial_weight_g=initial_weight,
            purchase_price=price,
            brand=brand,
        )
    except Exception as exc:
        print(_ansi.paint(f"Error al registrar la bobina: {exc}", _ansi.RED))
        return None

    print(_ansi.paint(f"Bobina registrada correctamente con ID {spool_id}.", _ansi.GREEN))
    return spool_id


__all__ = ["create_spool_form"]
