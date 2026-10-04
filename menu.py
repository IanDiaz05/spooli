"""Interactive terminal menu for Spooli."""

from __future__ import annotations

try:
    from . import core
    from . import db
except ImportError:
    import core
    import db

from spooli.constants.ansi import BOLD, CYAN, GREEN, RED, RESET, YELLOW, paint
from spooli.constants.defaults import (
    DEFAULT_BRAND,
    DEFAULT_COLOR,
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_MATERIAL,
    DEFAULT_PRICE,
    DEFAULT_SETTINGS,
    DEFAULT_WEIGHT_G,
    SettingKey,
)
from spooli.constants.formats import (
    COL_BRAND_WIDTH,
    COL_COLOR_WIDTH,
    COL_HISTORY_COST_VALUE_WIDTH,
    COL_HISTORY_COST_WIDTH,
    COL_HISTORY_FILE_WIDTH,
    COL_HISTORY_GRAMS_WIDTH,
    COL_HISTORY_SPOOL_WIDTH,
    COL_ID_WIDTH,
    COL_MATERIAL_WIDTH,
    COL_RECENT_FILE_WIDTH,
    COL_RECENT_GRAMS_WIDTH,
    COL_RECENT_ID_WIDTH,
    COL_REMAINING_WIDTH,
    FILE_NAME_HISTORY_LIMIT,
    FILE_NAME_RECENT_LIMIT,
    GRAMS_DECIMALS,
    MONEY_DECIMALS,
    PERCENT_DECIMALS,
    RECENT_SEPARATOR_WIDTH,
    WEIGHT_DECIMALS,
)
from spooli.constants.messages import (
    MSG_INVALID_NUMBER,
    MSG_NO_PRINTS_YET,
    MSG_OPERATION_CANCELLED,
    MSG_PRESS_ENTER,
)
from spooli.constants.thresholds import LOW_STOCK_RATIO, PERCENT_MAX

# Backwards-compatible alias for the previous module-level threshold.
LOW_STOCK_THRESHOLD = LOW_STOCK_RATIO


def _safe_input(prompt: str) -> str | None:
    """Prompt the user, returning None on EOF/interrupt."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print(f"\n{paint(MSG_OPERATION_CANCELLED, YELLOW)}")
        return None


def _pause() -> None:
    try:
        input(MSG_PRESS_ENTER)
    except (EOFError, KeyboardInterrupt):
        print()


def get_recent_prints(limit: int = DEFAULT_HISTORY_LIMIT) -> list[dict]:
    """Return the most recent print jobs, newest first."""
    db.init_db()
    with db.connection_scope() as conn:
        rows = conn.execute(
            "SELECT * FROM prints ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [dict(row) for row in rows]


def show_inventory() -> None:
    """Display the spool inventory as a formatted table."""
    try:
        spools = db.get_all_spools()
    except Exception as exc:
        print(paint(f"Error al obtener el inventario: {exc}", RED))
        return

    print(f"\n{paint('=== Inventario de Bobinas ===', BOLD, CYAN)}")
    if not spools:
        print("No hay bobinas registradas en el inventario.")
        print("Usa la opción 'Registrar Nueva Bobina' para añadir una.")
        return

    header = (
        f"{'ID':<{COL_ID_WIDTH}} {'Marca':<{COL_BRAND_WIDTH}} "
        f"{'Material':<{COL_MATERIAL_WIDTH}} {'Color':<{COL_COLOR_WIDTH}} "
        f"{'Restante':<{COL_REMAINING_WIDTH}} {'Estado'}"
    )
    print(header)
    print("-" * len(header))
    for spool in spools:
        try:
            initial = float(spool.get("initial_weight_g") or 0)
        except (TypeError, ValueError):
            initial = 0
        try:
            remaining = float(spool.get("remaining_weight_g") or 0)
        except (TypeError, ValueError):
            remaining = 0
        percent = (remaining / initial * PERCENT_MAX) if initial > 0 else 0.0
        low = initial > 0 and (remaining / initial) < LOW_STOCK_RATIO
        brand = str(spool.get("brand") or "-")
        material = str(spool.get("material") or "-")
        color = str(spool.get("color") or "-")
        remaining_text = (
            f"{remaining:.{WEIGHT_DECIMALS}f} g ({percent:.{PERCENT_DECIMALS}f}%)"
        )
        state_text = "Disponible" if not low else "Nivel bajo"
        row = (
            f"{spool.get('id')!s:<{COL_ID_WIDTH}} {brand:<{COL_BRAND_WIDTH}} "
            f"{material:<{COL_MATERIAL_WIDTH}} {color:<{COL_COLOR_WIDTH}} "
            f"{remaining_text:<{COL_REMAINING_WIDTH}} {state_text}"
        )
        if low:
            print(paint(row, RED))
        else:
            print(row)
    print(f"\nTotal de bobinas: {len(spools)}")


def create_spool_form() -> int | None:
    """Guide the user through spool creation. Returns new spool id or None."""
    print(f"\n{paint('=== Registrar Nueva Bobina ===', BOLD, CYAN)}")
    print(paint("(Pulsa Enter para aceptar el valor por defecto)", CYAN))

    brand_raw = _safe_input(f"Marca [{DEFAULT_BRAND}]: ")
    if brand_raw is None:
        return None
    material_raw = _safe_input(f"Material [{DEFAULT_MATERIAL}]: ")
    if material_raw is None:
        return None
    color_raw = _safe_input(f"Color [{DEFAULT_COLOR}]: ")
    if color_raw is None:
        return None
    weight_raw = _safe_input(f"Peso inicial en gramos [{DEFAULT_WEIGHT_G}]: ")
    if weight_raw is None:
        return None
    price_raw = _safe_input(f"Precio de compra [{DEFAULT_PRICE}]: ")
    if price_raw is None:
        return None

    brand = brand_raw.strip() or DEFAULT_BRAND
    material = material_raw.strip() or DEFAULT_MATERIAL
    color = color_raw.strip() or DEFAULT_COLOR

    if not material:
        print(paint("Error: el material no puede estar vacío.", RED))
        return None

    weight_text = weight_raw.strip().replace(",", ".") or DEFAULT_WEIGHT_G
    try:
        initial_weight = float(weight_text)
    except ValueError:
        print(paint("Error: el peso inicial debe ser un número válido.", RED))
        return None
    if initial_weight <= 0:
        print(paint("Error: el peso inicial debe ser mayor que cero.", RED))
        return None

    price_text = price_raw.strip().replace(",", ".") or DEFAULT_PRICE
    try:
        price = float(price_text)
    except ValueError:
        print(paint("Error: el precio debe ser un número válido.", RED))
        return None
    if price < 0:
        print(paint("Error: el precio no puede ser negativo.", RED))
        return None

    try:
        spool_id = db.create_spool(
            material=material,
            color=color,
            initial_weight_g=initial_weight,
            purchase_price=price,
            brand=brand,
        )
    except Exception as exc:
        print(paint(f"Error al registrar la bobina: {exc}", RED))
        return None

    print(paint(f"Bobina registrada correctamente con ID {spool_id}.", GREEN))
    return spool_id


# Backwards-compatible alias.
register_spool = create_spool_form


def register_failed_print() -> dict | None:
    """Register a failed print, refunding unused filament to the spool."""
    print(f"\n{paint('=== Registrar Pieza Fallida ===', BOLD, CYAN)}")
    try:
        prints = get_recent_prints()
    except Exception as exc:
        print(paint(f"Error al obtener el historial: {exc}", RED))
        return None

    if not prints:
        print(MSG_NO_PRINTS_YET)
        return None

    print("Impresiones recientes:")
    print(
        f"{'ID':<{COL_RECENT_ID_WIDTH}} {'Archivo':<{COL_RECENT_FILE_WIDTH}} "
        f"{'Gramos':<{COL_RECENT_GRAMS_WIDTH}} {'Estado'}"
    )
    print("-" * RECENT_SEPARATOR_WIDTH)
    for record in prints:
        file_cell = str(record.get("file_name") or "-")[:FILE_NAME_RECENT_LIMIT]
        grams_used = float(record.get("grams_used") or 0)
        print(
            f"{record.get('id')!s:<{COL_RECENT_ID_WIDTH}} "
            f"{file_cell:<{COL_RECENT_FILE_WIDTH}} "
            f"{grams_used:<{COL_RECENT_GRAMS_WIDTH}.{GRAMS_DECIMALS}f} "
            f"{record.get('status')}"
        )

    id_raw = _safe_input("Introduce el ID de la impresión fallida: ")
    if id_raw is None:
        return None
    try:
        print_id = int(str(id_raw).strip())
    except ValueError:
        print(paint("Error: el ID debe ser un número entero.", RED))
        return None

    target = next((p for p in prints if int(p.get("id")) == print_id), None)
    if target is None:
        # Look it up directly in case it is older than the recent window.
        try:
            with db.connection_scope() as conn:
                row = conn.execute(
                    "SELECT * FROM prints WHERE id = ?", (print_id,)
                ).fetchone()
                target = dict(row) if row else None
        except Exception:
            target = None
    if target is None:
        print(paint(f"Error: no existe una impresión con ID {print_id}.", RED))
        return None

    try:
        estimated = float(target.get("grams_used") or 0)
    except (TypeError, ValueError):
        estimated = 0.0

    print("Método de ajuste:")
    print("  1. Porcentaje de la pieza completado (0-100)")
    print("  2. Gramos reales pesados del desperdicio")
    method_raw = _safe_input("Selecciona el método (1/2): ")
    if method_raw is None:
        return None
    method = method_raw.strip()
    if method not in ("1", "2"):
        print(paint("Error: debes elegir 1 o 2.", RED))
        return None

    is_percent = method == "1"
    if is_percent:
        value_raw = _safe_input("Porcentaje completado (0-100): ")
    else:
        value_raw = _safe_input("Gramos reales consumidos: ")
    if value_raw is None:
        return None
    try:
        value = float(value_raw.strip().replace(",", "."))
    except ValueError:
        print(paint(MSG_INVALID_NUMBER, RED))
        return None

    try:
        refund = core.calculate_refund(
            estimated, value, is_percent=is_percent
        )
    except Exception as exc:
        print(paint(f"Error al calcular la devolución: {exc}", RED))
        return None

    try:
        updated = db.update_failed_print(
            print_id, float(refund.actual_consumption)
        )
    except Exception as exc:
        print(paint(f"Error al actualizar la impresión: {exc}", RED))
        return None

    print(paint(f"Impresión {print_id} marcada como fallida.", GREEN))
    print(f"Consumo estimado: {refund.estimated_grams:.{GRAMS_DECIMALS}f} g")
    print(f"Consumo real: {refund.actual_consumption:.{GRAMS_DECIMALS}f} g")
    print(
        "Filamento devuelto a la bobina: "
        f"{refund.refund_grams:.{GRAMS_DECIMALS}f} g"
    )
    return updated


def show_history(limit: int = DEFAULT_HISTORY_LIMIT) -> None:
    """Display recent print jobs with their cost breakdown."""
    print(f"\n{paint('=== Historial de Impresiones ===', BOLD, CYAN)}")
    try:
        prints = get_recent_prints(limit=limit)
    except Exception as exc:
        print(paint(f"Error al obtener el historial: {exc}", RED))
        return

    if not prints:
        print(MSG_NO_PRINTS_YET)
        return

    fallback_currency = DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
    default_currency = (
        db.get_setting(SettingKey.CURRENCY_SYMBOL.value) or fallback_currency
    ).strip() or fallback_currency
    header = (
        f"{'ID':<{COL_ID_WIDTH}} {'Archivo':<{COL_HISTORY_FILE_WIDTH}} "
        f"{'Bobina':<{COL_HISTORY_SPOOL_WIDTH}} "
        f"{'Gramos':<{COL_HISTORY_GRAMS_WIDTH}} "
        f"{'Costo':<{COL_HISTORY_COST_WIDTH}} {'Estado'}"
    )
    print(header)
    print("-" * len(header))
    total_cost = 0.0
    total_grams = 0.0
    for record in prints:
        try:
            cost = float(
                record.get("total_cost")
                if record.get("total_cost") is not None
                else record.get("cost") or 0
            )
        except (TypeError, ValueError):
            cost = 0.0
        try:
            grams = float(record.get("grams_used") or 0)
        except (TypeError, ValueError):
            grams = 0.0
        # Each print keeps its own recorded currency symbol (snapshot integrity).
        record_currency = str(
            record.get("currency_symbol") or default_currency
        ).strip() or default_currency
        total_cost += cost
        total_grams += grams
        file_cell = str(record.get("file_name") or "-")[:FILE_NAME_HISTORY_LIMIT]
        print(
            f"{record.get('id')!s:<{COL_ID_WIDTH}} "
            f"{file_cell:<{COL_HISTORY_FILE_WIDTH}} "
            f"{str(record.get('spool_id')):<{COL_HISTORY_SPOOL_WIDTH}} "
            f"{grams:<{COL_HISTORY_GRAMS_WIDTH}.{GRAMS_DECIMALS}f} "
            f"{record_currency}{cost:<{COL_HISTORY_COST_VALUE_WIDTH}.{MONEY_DECIMALS}f} "
            f"{record.get('status')}"
        )
    print("-" * len(header))
    print(f"Total impresiones: {len(prints)}")
    print(f"Filamento total consumido: {total_grams:.{GRAMS_DECIMALS}f} g")
    print(f"Costo total: {default_currency}{total_cost:.{MONEY_DECIMALS}f}")


def show_settings() -> None:
    """Display and update application settings."""
    print(f"\n{paint('=== Configuración ===', BOLD, CYAN)}")
    try:
        kwh_cost = (
            db.get_setting(SettingKey.ELECTRICITY_KWH_COST.value)
            or DEFAULT_SETTINGS[SettingKey.ELECTRICITY_KWH_COST.value]
        )
        watts = (
            db.get_setting(SettingKey.PRINTER_POWER_WATTS.value)
            or DEFAULT_SETTINGS[SettingKey.PRINTER_POWER_WATTS.value]
        )
        currency = (
            db.get_setting(SettingKey.CURRENCY_SYMBOL.value)
            or DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
        )
    except Exception as exc:
        print(paint(f"Error al obtener la configuración: {exc}", RED))
        return

    print(f"Costo por kWh actual: {kwh_cost}")
    print(f"Potencia de la impresora (W) actual: {watts}")
    print(f"Símbolo de moneda actual: {currency}")
    print("Deja el campo vacío para mantener el valor actual.")

    kwh_raw = _safe_input("Nuevo costo por kWh: ")
    if kwh_raw is None:
        return None
    watts_raw = _safe_input("Nueva potencia de la impresora (W): ")
    if watts_raw is None:
        return None
    currency_raw = _safe_input("Nuevo símbolo de moneda: ")
    if currency_raw is None:
        return None

    try:
        if kwh_raw.strip() != "":
            new_kwh = float(kwh_raw.strip().replace(",", "."))
            if new_kwh < 0:
                print(paint("Error: el costo por kWh no puede ser negativo.", RED))
                return None
            db.set_setting(SettingKey.ELECTRICITY_KWH_COST.value, str(new_kwh))
        if watts_raw.strip() != "":
            new_watts = float(watts_raw.strip().replace(",", "."))
            if new_watts < 0:
                print(paint("Error: la potencia no puede ser negativa.", RED))
                return None
            db.set_setting(SettingKey.PRINTER_POWER_WATTS.value, str(new_watts))
        if currency_raw.strip() != "":
            new_currency = currency_raw.strip()
            if new_currency != currency:
                try:
                    spools = db.get_all_spools()
                except Exception as exc:
                    print(paint(f"Error al obtener las bobinas: {exc}", RED))
                    return None
                if not spools:
                    db.set_setting(SettingKey.CURRENCY_SYMBOL.value, new_currency)
                else:
                    count = len(spools)
                    print(
                        paint(
                            f"Atención: Tienes {count} bobina(s) registradas "
                            f"con la moneda anterior ({currency}).",
                            YELLOW,
                        )
                    )
                    print("1. Convertir precios de bobinas con tipo de cambio")
                    print("2. Solo cambiar el símbolo (mantener los importes actuales)")
                    print("3. Cancelar cambio de moneda")
                    option_raw = _safe_input("Selecciona una opción (1-3): ")
                    if option_raw is None:
                        return None
                    option = option_raw.strip()
                    if option == "1":
                        print(
                            "Se convertirán los precios del inventario y el historial "
                            "de impresiones al nuevo valor."
                        )
                        rate_raw = _safe_input(
                            f"Tipo de cambio (1 {currency} = X {new_currency}): "
                        )
                        if rate_raw is None:
                            return None
                        try:
                            multiplier = float(rate_raw.strip().replace(",", "."))
                        except ValueError:
                            print(
                                paint(
                                    "Error: el tipo de cambio debe ser un número válido.",
                                    RED,
                                )
                            )
                            return None
                        if multiplier <= 0:
                            print(
                                paint(
                                    "Error: el tipo de cambio debe ser mayor que cero.",
                                    RED,
                                )
                            )
                            return None
                        try:
                            result = db.convert_all_records_currency(
                                multiplier, new_currency
                            )
                        except Exception as exc:
                            print(paint(f"Error al convertir los precios: {exc}", RED))
                            return None
                        db.set_setting(
                            SettingKey.CURRENCY_SYMBOL.value, new_currency
                        )
                        if isinstance(result, dict):
                            spools_n = result.get("spools", 0)
                            prints_n = result.get("prints", 0)
                            print(
                                paint(
                                    f"Precios de {spools_n} bobina(s) y "
                                    f"{prints_n} registro(s) del historial "
                                    "convertidos correctamente.",
                                    GREEN,
                                )
                            )
                        else:
                            print(paint("Precios convertidos correctamente.", GREEN))
                    elif option == "2":
                        db.set_setting(
                            SettingKey.CURRENCY_SYMBOL.value, new_currency
                        )
                        print(
                            "Solo se cambió el símbolo. Los importes numéricos y "
                            "el historial conservan sus valores anteriores."
                        )
                    elif option == "3":
                        print("Cambio de moneda cancelado. Se mantiene la moneda anterior.")
                    else:
                        print(
                            paint(
                                "Opción no válida. Cambio de moneda cancelado.",
                                YELLOW,
                            )
                        )
            else:
                db.set_setting(SettingKey.CURRENCY_SYMBOL.value, new_currency)
    except ValueError:
        print(paint(MSG_INVALID_NUMBER, RED))
        return None
    except Exception as exc:
        print(paint(f"Error al guardar la configuración: {exc}", RED))
        return None

    print(paint("Configuración actualizada correctamente.", GREEN))


def main_menu() -> None:
    """Run the main interactive navigation loop."""
    db.init_db()
    while True:
        print(f"\n{paint('=== Spooli - Menú Principal ===', BOLD, CYAN)}")
        print("1. Ver Inventario")
        print("2. Registrar Nueva Bobina")
        print("3. Registrar Pieza Fallida")
        print("4. Historial de Impresiones")
        print("5. Configuración")
        print("6. Salir")

        choice_raw = _safe_input("Selecciona una opción (1-6): ")
        if choice_raw is None:
            print("Saliendo...")
            break
        choice = choice_raw.strip()

        if choice == "1":
            show_inventory()
            _pause()
        elif choice == "2":
            create_spool_form()
            _pause()
        elif choice == "3":
            register_failed_print()
            _pause()
        elif choice == "4":
            show_history()
            _pause()
        elif choice == "5":
            show_settings()
            _pause()
        elif choice == "6":
            print("Saliendo... ¡Hasta pronto!")
            break
        else:
            print(paint("Opción no válida. Elige un número del 1 al 6.", YELLOW))


if __name__ == "__main__":
    main_menu()
