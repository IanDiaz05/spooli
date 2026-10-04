"""Direct-mode print workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from spooli.constants.defaults import DEFAULT_SETTINGS, SettingKey
from spooli.constants.formats import YES_TOKENS
from spooli.constants.messages import MSG_FILE_NOT_FOUND, MSG_OPERATION_CANCELLED
from spooli.domain.costing import calculate_costs
from spooli.domain.errors import NoCompatibleSpoolError
from spooli.domain.selection import select_spool
from spooli.parsing import MissingMetadataError, UnsupportedFormatError, parse_file
from spooli.storage import spool_repo
from spooli.storage.print_repo import record_print_job
from spooli.storage.schema import init_db
from spooli.storage.settings_store import get_setting
from spooli.ui.input import confirm, safe_input

from .summary import display_summary

# Reference the shared confirmation helper so the module explicitly uses it;
# direct mode relies on safe_input to distinguish EOF (exit 1) from decline.
_confirm = confirm


class _StorageSpoolRepository:
    """Adapter over spooli.storage.spool_repo for domain selection."""

    def get_by_id(self, spool_id: int) -> dict | None:
        """Return a single spool, or None when unknown."""
        return spool_repo.get_spool_by_id(spool_id)

    def get_compatible(self, material: str, required_grams: float) -> list[dict]:
        """Return spools of a material holding enough filament."""
        return spool_repo.get_compatible_spools(material, required_grams)


def run_direct_mode(file_path_arg: str, spool_id: Optional[int], auto_confirm: bool) -> int:
    """Run a single print job from a slicer file."""
    resolved = Path(file_path_arg).expanduser()
    if not resolved.is_absolute():
        resolved = Path.cwd() / resolved
    if not resolved.is_file():
        print(MSG_FILE_NOT_FOUND.format(file_path=file_path_arg))
        return 1

    metadata = None
    try:
        init_db()
        metadata = parse_file(resolved)

        kwh_cost = float(
            get_setting(SettingKey.ELECTRICITY_KWH_COST.value)
            or DEFAULT_SETTINGS[SettingKey.ELECTRICITY_KWH_COST.value]
        )
        printer_watts = float(
            get_setting(SettingKey.PRINTER_POWER_WATTS.value)
            or DEFAULT_SETTINGS[SettingKey.PRINTER_POWER_WATTS.value]
        )
        currency = (
            get_setting(SettingKey.CURRENCY_SYMBOL.value)
            or DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
        )

        repo = _StorageSpoolRepository()
        selection = select_spool(
            metadata.material, metadata.grams, manual_spool_id=spool_id, repo=repo
        )
        spool = selection.selected_spool
        costs = calculate_costs(
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
            raw = safe_input("¿Registrar impresión? [y/N]: ")
            if raw is None:
                print(MSG_OPERATION_CANCELLED)
                return 1
            confirmed = raw.strip().lower() in YES_TOKENS

        if not confirmed:
            print(MSG_OPERATION_CANCELLED)
            return 0

        print_id = record_print_job(
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
        print(MSG_FILE_NOT_FOUND.format(file_path=file_path_arg))
        return 1
    except (UnsupportedFormatError, MissingMetadataError) as exc:
        print(f"Error al analizar el archivo: {exc}")
        return 1
    except NoCompatibleSpoolError:
        print(
            f"Error: No hay bobinas de '{metadata.material}' "
            f"con al menos {metadata.grams}g disponibles."
        )
        print("Inventario actual:")
        try:
            spools = spool_repo.get_all_spools()
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
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Error inesperado al procesar la impresión: {exc}")
        return 1


__all__ = ["run_direct_mode"]
