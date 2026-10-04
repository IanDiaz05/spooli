"""First-run onboarding wizard."""

from __future__ import annotations

try:
    import install as _install
except ImportError:  # pragma: no cover - fallback for package layouts
    _install = None

from spooli.constants.defaults import DEFAULT_SETTINGS, SettingKey
from spooli.constants.formats import YES_TOKENS
from spooli.constants.messages import MSG_INVALID_VALUE_FALLBACK
from spooli.constants.paths import INSTALL_SCRIPT_NAME
from spooli.storage import init_db
from spooli.storage.settings_store import set_setting
from spooli.ui.input import prompt_float, safe_input


def _onboarding_input(prompt: str) -> str | None:
    """Prompt helper that returns None on EOF/interrupt."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def run_onboarding() -> None:
    """Run the first-run wizard and persist the initial settings."""
    print("=== Bienvenido a Spooli ===")
    print("Parece que es la primera vez que inicias Spooli.")
    print("Vamos a realizar una configuración inicial rápida.")

    answer = _onboarding_input(
        "¿Deseas instalar 'spooli' como comando global en tu sistema? [Y/n]: "
    )
    if answer is None:
        print("Instalación global omitida.")
    elif answer.strip() == "" or answer.strip().lower() in YES_TOKENS:
        try:
            ok = _install.install_cli(quiet=False) if _install is not None else False
        except Exception as exc:
            ok = False
            print(f"Error durante la instalación: {exc}")
        if not ok:
            print("No se pudo completar la instalación global.")
            print(f"Puedes intentarlo más tarde con: python3 {INSTALL_SCRIPT_NAME}")
    else:
        print(
            f"De acuerdo, puedes instalarlo más tarde con: python3 {INSTALL_SCRIPT_NAME}"
        )

    print("Configuración inicial (pulsa Enter para aceptar el valor por defecto).")

    currency_default = DEFAULT_SETTINGS[SettingKey.CURRENCY_SYMBOL.value]
    currency_raw = safe_input(
        f"Símbolo o código de moneda local (ej. MXN, USD, EUR, $) [{currency_default}]: "
    )
    if currency_raw is None or currency_raw.strip() == "":
        currency = currency_default
    else:
        currency = currency_raw.strip()

    kwh_default = DEFAULT_SETTINGS[SettingKey.ELECTRICITY_KWH_COST.value]
    kwh_value = prompt_float(
        f"Costo de electricidad por kWh [{kwh_default}]: ",
        default=float(kwh_default),
    )
    if kwh_value is None or kwh_value < 0:
        print(MSG_INVALID_VALUE_FALLBACK.format(default=kwh_default))
        kwh_cost = kwh_default
    else:
        kwh_cost = str(kwh_value)

    watts_default = DEFAULT_SETTINGS[SettingKey.PRINTER_POWER_WATTS.value]
    watts_value = prompt_float(
        f"Consumo estimado de la impresora en Watts [{watts_default}]: ",
        default=float(watts_default),
    )
    if watts_value is None or watts_value < 0:
        print(MSG_INVALID_VALUE_FALLBACK.format(default=watts_default))
        watts = watts_default
    else:
        watts = str(watts_value)

    init_db()
    set_setting(SettingKey.CURRENCY_SYMBOL.value, currency)
    set_setting(SettingKey.ELECTRICITY_KWH_COST.value, kwh_cost)
    set_setting(SettingKey.PRINTER_POWER_WATTS.value, watts)
    print("Configuración guardada correctamente.")


__all__ = ["_onboarding_input", "run_onboarding"]
