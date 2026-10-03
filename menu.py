"""Interactive terminal menu for Spooli."""

from __future__ import annotations

try:
    from . import core
    from . import db
except ImportError:
    import core
    import db

# ANSI color palette for terminal UI.
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

LOW_STOCK_THRESHOLD = 0.15


def _safe_input(prompt: str) -> str | None:
    """Prompt the user, returning None on EOF/interrupt."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print(f"\n{YELLOW}Operación cancelada por el usuario.{RESET}")
        return None


def _pause() -> None:
    try:
        input("Pulsa Enter para continuar...")
    except (EOFError, KeyboardInterrupt):
        print()


def get_recent_prints(limit: int = 20) -> list[dict]:
    """Return the most recent print jobs, newest first."""
    db.init_db()
    with db.get_connection() as conn:
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
        print(f"{RED}Error al obtener el inventario: {exc}{RESET}")
        return

    print(f"\n{BOLD}{CYAN}=== Inventario de Bobinas ==={RESET}")
    if not spools:
        print("No hay bobinas registradas en el inventario.")
        print("Usa la opción 'Registrar Nueva Bobina' para añadir una.")
        return

    header = f"{'ID':<5} {'Marca':<15} {'Material':<10} {'Color':<12} {'Restante':<16} {'Estado'}"
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
        percent = (remaining / initial * 100.0) if initial > 0 else 0.0
        low = initial > 0 and (remaining / initial) < LOW_STOCK_THRESHOLD
        brand = str(spool.get("brand") or "-")
        material = str(spool.get("material") or "-")
        color = str(spool.get("color") or "-")
        remaining_text = f"{remaining:.1f} g ({percent:.0f}%)"
        state_text = "Disponible" if not low else "Nivel bajo"
        row = (
            f"{spool.get('id')!s:<5} {brand:<15} {material:<10} "
            f"{color:<12} {remaining_text:<16} {state_text}"
        )
        if low:
            print(f"{RED}{row}{RESET}")
        else:
            print(row)
    print(f"\nTotal de bobinas: {len(spools)}")


def create_spool_form() -> int | None:
    """Guide the user through spool creation. Returns new spool id or None."""
    print(f"\n{BOLD}{CYAN}=== Registrar Nueva Bobina ==={RESET}")

    brand_raw = _safe_input("Marca (ej. Sunlu): ")
    if brand_raw is None:
        return None
    material_raw = _safe_input("Material (ej. PLA): ")
    if material_raw is None:
        return None
    color_raw = _safe_input("Color (ej. Negro): ")
    if color_raw is None:
        return None
    weight_raw = _safe_input("Peso inicial en gramos (ej. 1000): ")
    if weight_raw is None:
        return None
    price_raw = _safe_input("Precio de compra (ej. 19.99): ")
    if price_raw is None:
        return None

    brand = brand_raw.strip() or None
    material = material_raw.strip()
    color = color_raw.strip() or None

    if not material:
        print(f"{RED}Error: el material no puede estar vacío.{RESET}")
        return None

    try:
        initial_weight = float(weight_raw.strip().replace(",", "."))
    except ValueError:
        print(f"{RED}Error: el peso inicial debe ser un número válido.{RESET}")
        return None
    if initial_weight <= 0:
        print(f"{RED}Error: el peso inicial debe ser mayor que cero.{RESET}")
        return None

    price_text = price_raw.strip().replace(",", ".")
    if price_text == "":
        price = 0.0
    else:
        try:
            price = float(price_text)
        except ValueError:
            print(f"{RED}Error: el precio debe ser un número válido.{RESET}")
            return None
        if price < 0:
            print(f"{RED}Error: el precio no puede ser negativo.{RESET}")
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
        print(f"{RED}Error al registrar la bobina: {exc}{RESET}")
        return None

    print(f"{GREEN}Bobina registrada correctamente con ID {spool_id}.{RESET}")
    return spool_id


# Backwards-compatible alias.
register_spool = create_spool_form


def register_failed_print() -> dict | None:
    """Register a failed print, refunding unused filament to the spool."""
    print(f"\n{BOLD}{CYAN}=== Registrar Pieza Fallida ==={RESET}")
    try:
        prints = get_recent_prints()
    except Exception as exc:
        print(f"{RED}Error al obtener el historial: {exc}{RESET}")
        return None

    if not prints:
        print("No hay impresiones registradas todavía.")
        return None

    print("Impresiones recientes:")
    print(f"{'ID':<6} {'Archivo':<30} {'Gramos':<10} {'Estado'}")
    print("-" * 60)
    for record in prints:
        print(
            f"{record.get('id')!s:<6} "
            f"{str(record.get('file_name') or '-')[:30]:<30} "
            f"{float(record.get('grams_used') or 0):<10.2f} "
            f"{record.get('status')}"
        )

    id_raw = _safe_input("Introduce el ID de la impresión fallida: ")
    if id_raw is None:
        return None
    try:
        print_id = int(str(id_raw).strip())
    except ValueError:
        print(f"{RED}Error: el ID debe ser un número entero.{RESET}")
        return None

    target = next((p for p in prints if int(p.get("id")) == print_id), None)
    if target is None:
        # Look it up directly in case it is older than the recent window.
        try:
            with db.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM prints WHERE id = ?", (print_id,)
                ).fetchone()
                target = dict(row) if row else None
        except Exception:
            target = None
    if target is None:
        print(f"{RED}Error: no existe una impresión con ID {print_id}.{RESET}")
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
        print(f"{RED}Error: debes elegir 1 o 2.{RESET}")
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
        print(f"{RED}Error: el valor debe ser un número válido.{RESET}")
        return None

    try:
        refund = core.calculate_refund(
            estimated, value, is_percent=is_percent
        )
    except Exception as exc:
        print(f"{RED}Error al calcular la devolución: {exc}{RESET}")
        return None

    try:
        updated = db.update_failed_print(
            print_id, float(refund.actual_consumption)
        )
    except Exception as exc:
        print(f"{RED}Error al actualizar la impresión: {exc}{RESET}")
        return None

    print(f"{GREEN}Impresión {print_id} marcada como fallida.{RESET}")
    print(f"Consumo estimado: {refund.estimated_grams:.2f} g")
    print(f"Consumo real: {refund.actual_consumption:.2f} g")
    print(f"Filamento devuelto a la bobina: {refund.refund_grams:.2f} g")
    return updated


def show_history(limit: int = 20) -> None:
    """Display recent print jobs with their cost breakdown."""
    print(f"\n{BOLD}{CYAN}=== Historial de Impresiones ==={RESET}")
    try:
        prints = get_recent_prints(limit=limit)
    except Exception as exc:
        print(f"{RED}Error al obtener el historial: {exc}{RESET}")
        return

    if not prints:
        print("No hay impresiones registradas todavía.")
        return

    currency = db.get_setting("currency_symbol") or "$"
    header = (
        f"{'ID':<5} {'Archivo':<28} {'Bobina':<7} "
        f"{'Gramos':<8} {'Costo':<12} {'Estado'}"
    )
    print(header)
    print("-" * len(header))
    total_cost = 0.0
    total_grams = 0.0
    for record in prints:
        try:
            cost = float(record.get("cost") or 0)
        except (TypeError, ValueError):
            cost = 0.0
        try:
            grams = float(record.get("grams_used") or 0)
        except (TypeError, ValueError):
            grams = 0.0
        total_cost += cost
        total_grams += grams
        print(
            f"{record.get('id')!s:<5} "
            f"{str(record.get('file_name') or '-')[:28]:<28} "
            f"{str(record.get('spool_id')):<7} "
            f"{grams:<8.2f} "
            f"{currency}{cost:<11.4f} "
            f"{record.get('status')}"
        )
    print("-" * len(header))
    print(f"Total impresiones: {len(prints)}")
    print(f"Filamento total consumido: {total_grams:.2f} g")
    print(f"Costo total: {currency}{total_cost:.4f}")


def show_settings() -> None:
    """Display and update application settings."""
    print(f"\n{BOLD}{CYAN}=== Configuración ==={RESET}")
    try:
        kwh_cost = db.get_setting("electricity_kwh_cost") or "0.15"
        watts = db.get_setting("printer_power_watts") or "150"
        currency = db.get_setting("currency_symbol") or "$"
    except Exception as exc:
        print(f"{RED}Error al obtener la configuración: {exc}{RESET}")
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
                print(f"{RED}Error: el costo por kWh no puede ser negativo.{RESET}")
                return None
            db.set_setting("electricity_kwh_cost", str(new_kwh))
        if watts_raw.strip() != "":
            new_watts = float(watts_raw.strip().replace(",", "."))
            if new_watts < 0:
                print(f"{RED}Error: la potencia no puede ser negativa.{RESET}")
                return None
            db.set_setting("printer_power_watts", str(new_watts))
        if currency_raw.strip() != "":
            db.set_setting("currency_symbol", currency_raw.strip())
    except ValueError:
        print(f"{RED}Error: el valor debe ser un número válido.{RESET}")
        return None
    except Exception as exc:
        print(f"{RED}Error al guardar la configuración: {exc}{RESET}")
        return None

    print(f"{GREEN}Configuración actualizada correctamente.{RESET}")


def main_menu() -> None:
    """Run the main interactive navigation loop."""
    db.init_db()
    while True:
        print(f"\n{BOLD}{CYAN}=== Spooli - Menú Principal ==={RESET}")
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
            print(f"{YELLOW}Opción no válida. Elige un número del 1 al 6.{RESET}")


if __name__ == "__main__":
    main_menu()
