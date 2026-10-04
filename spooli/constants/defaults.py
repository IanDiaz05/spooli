"""Default configuration values for Spooli."""

from enum import Enum


class SettingKey(str, Enum):
    """Canonical keys of the settings stored in the database."""

    ELECTRICITY_KWH_COST = "electricity_kwh_cost"
    PRINTER_POWER_WATTS = "printer_power_watts"
    CURRENCY_SYMBOL = "currency_symbol"


# Single source of truth for the settings seeded into every database.
DEFAULT_SETTINGS: dict[str, str] = {
    SettingKey.ELECTRICITY_KWH_COST.value: "0.15",
    SettingKey.PRINTER_POWER_WATTS.value: "150",
    SettingKey.CURRENCY_SYMBOL.value: "$",
}

# Spool creation form defaults.
DEFAULT_BRAND = "Sunlu"
DEFAULT_MATERIAL = "PLA"
DEFAULT_COLOR = "Blanco"
DEFAULT_WEIGHT_G = "1000"  # Prompt default in the UI.
DEFAULT_WEIGHT_G_FLOAT = 1000.0  # Numeric default for domain logic.
DEFAULT_PRICE = "19.99"

# Number of print records returned by the history queries by default.
DEFAULT_HISTORY_LIMIT = 20
