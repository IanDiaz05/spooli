"""Interactive terminal screens."""

from .failed_prints import register_failed_print
from .history import show_history
from .inventory import show_inventory
from .settings import show_settings
from .shell import main_menu
from .spool_form import create_spool_form

__all__ = [
    "create_spool_form",
    "main_menu",
    "register_failed_print",
    "show_history",
    "show_inventory",
    "show_settings",
]
