"""Direct-mode CLI entry point for Spooli."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from . import db
    from . import core
    from . import menu
    from . import install
    from .parser import (
        MissingMetadataError,
        UnsupportedFormatError,
        parse_file,
    )
except ImportError:
    import db
    import core
    import menu
    import install
    from parser import (
        MissingMetadataError,
        UnsupportedFormatError,
        parse_file,
    )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spooli - control de filamento")
    parser.add_argument("file_path", nargs="?", help="Archivo .gcode o .3mf")
    parser.add_argument("--spool", type=int, default=None, help="ID de bobina a usar")
    parser.add_argument("--yes", "-y", action="store_true", help="Omitir confirmacion")
    return parser.parse_args(argv)


def is_first_run() -> bool:
    # Check DB file existence without creating or initializing it.
    try:
        db_path = db.get_db_path()
    except Exception:
        return False
    return not db_path.is_file()


def _onboarding_input(prompt: str) -> str | None:
    # Prompt helper that returns None on EOF/interrupt.
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def run_onboarding() -> None:
    # First-run wizard: welcome, optional global install, basic settings.
    print("=== Bienvenido a Spooli ===")
    print("Parece que es la primera vez que inicias Spooli.")
    print("Vamos a realizar una configuración inicial rápida.")

    answer = _onboarding_input(
        "¿Deseas instalar 'spooli' como comando global en tu sistema? [Y/n]: "
    )
    if answer is None:
        print("Instalación global omitida.")
    elif answer.strip() == "" or answer.strip().lower() in (
        "y",
        "yes",
        "s",
        "si",
        "sí",
    ):
        try:
            ok = install.install_cli(quiet=False)
        except Exception as exc:
            ok = False
            print(f"Error durante la instalación: {exc}")
        if not ok:
            print("No se pudo completar la instalación global.")
            print("Puedes intentarlo más tarde con: python3 install.py")
    else:
        print("De acuerdo, puedes instalarlo más tarde con: python3 install.py")

    print("Configuración inicial (pulsa Enter para aceptar el valor por defecto).")

    currency_raw = _onboarding_input("Símbolo de moneda [$]: ")
    if currency_raw is None or currency_raw.strip() == "":
        currency = "$"
    else:
        currency = currency_raw.strip()

    kwh_raw = _onboarding_input("Costo de electricidad por kWh [0.15]: ")
    if kwh_raw is None or kwh_raw.strip() == "":
        kwh_cost = "0.15"
    else:
        try:
            kwh_value = float(kwh_raw.strip().replace(",", "."))
            if kwh_value < 0:
                print("Valor no válido, se usará el valor por defecto: 0.15")
                kwh_cost = "0.15"
            else:
                kwh_cost = str(kwh_value)
        except ValueError:
            print("Valor no válido, se usará el valor por defecto: 0.15")
            kwh_cost = "0.15"

    watts_raw = _onboarding_input(
        "Consumo estimado de la impresora en Watts [150]: "
    )
    if watts_raw is None or watts_raw.strip() == "":
        watts = "150"
    else:
        try:
            watts_value = float(watts_raw.strip().replace(",", "."))
            if watts_value < 0:
                print("Valor no válido, se usará el valor por defecto: 150")
                watts = "150"
            else:
                watts = str(watts_value)
        except ValueError:
            print("Valor no válido, se usará el valor por defecto: 150")
            watts = "150"

    db.init_db()
    db.set_setting("currency_symbol", currency)
    db.set_setting("electricity_kwh_cost", kwh_cost)
    db.set_setting("printer_power_watts", watts)
    print("Configuración guardada correctamente.")


def format_duration(total_seconds: int) -> str:
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def display_summary(metadata, spool: dict, costs, currency: str) -> float:
    remaining_after = float(spool["remaining_weight_g"]) - float(metadata.grams)
    label_parts = [str(spool.get("brand") or "").strip(), str(spool.get("color") or "").strip()]
    spool_name = " ".join(p for p in label_parts if p) or "Sin nombre"
    print("--- Resumen de impresión ---")
    print(f"Archivo: {metadata.file_name}")
    print(f"Material: {metadata.material}")
    print(f"Peso requerido: {metadata.grams:.2f} g")
    print(f"Duración estimada: {format_duration(metadata.duration_seconds)}")
    print(f"Bobina asignada: ID {spool['id']} ({spool_name})")
    print(f"Restante en bobina: {float(spool['remaining_weight_g']):.2f} g")
    print(f"Restante tras impresión: {remaining_after:.2f} g")
    print(f"Costo filamento: {currency}{costs.filament_cost:.4f}")
    print(f"Costo electricidad: {currency}{costs.electricity_cost:.4f}")
    print(f"Costo total estimado: {currency}{costs.total_cost:.4f}")
    return remaining_after


def run_direct_mode(file_path_arg: str, spool_id: int | None, auto_confirm: bool) -> int:
    resolved = Path(file_path_arg).expanduser()
    if not resolved.is_absolute():
        resolved = Path.cwd() / resolved
    if not resolved.is_file():
        print(f"Error: no se encontró el archivo '{file_path_arg}'.")
        return 1

    metadata = None
    try:
        db.init_db()
        metadata = parse_file(resolved)

        kwh_cost = float(db.get_setting("electricity_kwh_cost") or 0.15)
        printer_watts = float(db.get_setting("printer_power_watts") or 150)
        currency = db.get_setting("currency_symbol") or "$"

        selection = core.select_spool(
            metadata.material, metadata.grams, manual_spool_id=spool_id
        )
        spool = selection.selected_spool
        costs = core.calculate_costs(
            metadata.grams,
            metadata.duration_seconds,
            float(spool.get("purchase_price") or 0.0),
            float(spool["initial_weight_g"]),
            printer_watts,
            kwh_cost,
        )

        display_summary(metadata, spool, costs, currency)

        if selection.alternatives:
            others = ", ".join(f"ID {s['id']}" for s in selection.alternatives)
            print(f"Bobinas alternativas disponibles: {others}")

        confirmed = auto_confirm
        if not confirmed:
            try:
                answer = input("¿Registrar impresión? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nOperación cancelada por el usuario.")
                return 1
            confirmed = answer in ("y", "yes", "s", "si", "sí")

        if not confirmed:
            print("Operación cancelada por el usuario.")
            return 0

        print_id = db.record_print_job(
            spool_id=int(spool["id"]),
            file_name=metadata.file_name,
            grams_used=float(metadata.grams),
            duration_seconds=int(metadata.duration_seconds),
            cost=float(costs.total_cost),
            filament_cost=float(costs.filament_cost),
            electricity_cost=float(costs.electricity_cost),
            total_cost=float(costs.total_cost),
            currency_symbol=currency,
        )
        print(f"Impresión registrada correctamente con ID {print_id}.")
        return 0
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{file_path_arg}'.")
        return 1
    except (UnsupportedFormatError, MissingMetadataError) as exc:
        print(f"Error al analizar el archivo: {exc}")
        return 1
    except ValueError as exc:
        if metadata is not None and "no compatible spools" in str(exc).lower():
            print(
                f"Error: No hay bobinas de '{metadata.material}' "
                f"con al menos {metadata.grams}g disponibles."
            )
            print("Inventario actual:")
            try:
                spools = db.get_all_spools()
            except Exception:
                spools = []
            if not spools:
                print("  (No hay bobinas registradas en la base de datos)")
            else:
                for spool in spools:
                    print(
                        f"  - ID {spool['id']}: {spool['material']} "
                        f"({spool['remaining_weight_g']}g restantes)"
                    )
            return 1
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Error inesperado al procesar la impresión: {exc}")
        return 1


def main(argv=None) -> int:
    args = parse_args(argv)
    # First-run check before any DB initialization or connection.
    if is_first_run():
        run_onboarding()
    if not args.file_path:
        menu.main_menu()
        return 0
    return run_direct_mode(args.file_path, args.spool, args.yes)


if __name__ == "__main__":
    sys.exit(main())
