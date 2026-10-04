"""Application settings screen."""

from __future__ import annotations

from spooli.constants import ansi as _ansi
from spooli.constants.defaults import DEFAULT_SETTINGS, SettingKey
from spooli.constants.messages import MSG_INVALID_NUMBER
from spooli.services.currency import run_currency_migration
from spooli.storage import settings_store, spool_repo
from spooli.ui.input import safe_input


def show_settings() -> None:
    """Display and update application settings."""
    print(f"\n{_ansi.paint('=== Configuración ===', _ansi.BOLD, _ansi.CYAN)}")
    try:
        kwh_cost = (
            settings_store.get_setting(SettingKey.ELECTRICITY_KWH_COST.value)
            or DEFAULT_SETTINGS[SettingKey.ELECTRICITY_KWH_COST.value]
        )
        watts = (
            settings_store.get_setting(SettingKey.PRINTER_POWER_WATTS.value)
            or DEFAULT_SETTINGS[SettingKey.PRINTER_POWER_WATTS.value]
        )
        currency = (
            settings_store.get_setting(SettingKey.CURRENCY_SYMBOL.value)
            or DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
        )
    except Exception as exc:
        print(_ansi.paint(f"Error al obtener la configuración: {exc}", _ansi.RED))
        return

    print(f"Costo por kWh actual: {kwh_cost}")
    print(f"Potencia de la impresora (W) actual: {watts}")
    print(f"Símbolo de moneda actual: {currency}")
    print("Deja el campo vacío para mantener el valor actual.")

    kwh_raw = safe_input("Nuevo costo por kWh: ")
    if kwh_raw is None:
        return
    watts_raw = safe_input("Nueva potencia de la impresora (W): ")
    if watts_raw is None:
        return
    currency_raw = safe_input("Nuevo símbolo de moneda: ")
    if currency_raw is None:
        return

    try:
        if kwh_raw.strip() != "":
            new_kwh = float(kwh_raw.strip().replace(",", "."))
            if new_kwh < 0:
                print(_ansi.paint("Error: el costo por kWh no puede ser negativo.", _ansi.RED))
                return
            settings_store.set_setting(SettingKey.ELECTRICITY_KWH_COST.value, str(new_kwh))
        if watts_raw.strip() != "":
            new_watts = float(watts_raw.strip().replace(",", "."))
            if new_watts < 0:
                print(_ansi.paint("Error: la potencia no puede ser negativa.", _ansi.RED))
                return
            settings_store.set_setting(SettingKey.PRINTER_POWER_WATTS.value, str(new_watts))
        if currency_raw.strip() != "":
            new_currency = currency_raw.strip()
            if new_currency != currency:
                try:
                    spools = spool_repo.get_all_spools()
                except Exception as exc:
                    print(_ansi.paint(f"Error al obtener las bobinas: {exc}", _ansi.RED))
                    return
                if not spools:
                    settings_store.set_setting(SettingKey.CURRENCY_SYMBOL.value, new_currency)
                else:
                    count = len(spools)
                    print(
                        _ansi.paint(
                            f"Atención: Tienes {count} bobina(s) registradas "
                            f"con la moneda anterior ({currency}).",
                            _ansi.YELLOW,
                        )
                    )
                    print("1. Convertir precios de bobinas con tipo de cambio")
                    print("2. Solo cambiar el símbolo (mantener los importes actuales)")
                    print("3. Cancelar cambio de moneda")
                    option_raw = safe_input("Selecciona una opción (1-3): ")
                    if option_raw is None:
                        return
                    option = option_raw.strip()
                    if option == "1":
                        print(
                            "Se convertirán los precios del inventario y el historial "
                            "de impresiones al nuevo valor."
                        )
                        rate_raw = safe_input(
                            f"Tipo de cambio (1 {currency} = X {new_currency}): "
                        )
                        if rate_raw is None:
                            return
                        try:
                            multiplier = float(rate_raw.strip().replace(",", "."))
                        except ValueError:
                            print(
                                _ansi.paint(
                                    "Error: el tipo de cambio debe ser un número válido.",
                                    _ansi.RED,
                                )
                            )
                            return
                        if multiplier <= 0:
                            print(
                                _ansi.paint(
                                    "Error: el tipo de cambio debe ser mayor que cero.",
                                    _ansi.RED,
                                )
                            )
                            return
                        try:
                            result = run_currency_migration(new_currency, multiplier)
                        except Exception as exc:
                            print(_ansi.paint(f"Error al convertir los precios: {exc}", _ansi.RED))
                            return
                        if isinstance(result, dict):
                            spools_n = result.get("spools", 0)
                            prints_n = result.get("prints", 0)
                            print(
                                _ansi.paint(
                                    f"Precios de {spools_n} bobina(s) y "
                                    f"{prints_n} registro(s) del historial "
                                    "convertidos correctamente.",
                                    _ansi.GREEN,
                                )
                            )
                        else:
                            print(_ansi.paint("Precios convertidos correctamente.", _ansi.GREEN))
                    elif option == "2":
                        settings_store.set_setting(
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
                            _ansi.paint(
                                "Opción no válida. Cambio de moneda cancelado.",
                                _ansi.YELLOW,
                            )
                        )
            else:
                settings_store.set_setting(SettingKey.CURRENCY_SYMBOL.value, new_currency)
    except ValueError:
        print(_ansi.paint(MSG_INVALID_NUMBER, _ansi.RED))
        return
    except Exception as exc:
        print(_ansi.paint(f"Error al guardar la configuración: {exc}", _ansi.RED))
        return

    print(_ansi.paint("Configuración actualizada correctamente.", _ansi.GREEN))


__all__ = ["show_settings"]
