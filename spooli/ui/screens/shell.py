"""Main navigation loop driven by a declarative option table."""

from __future__ import annotations

from collections.abc import Callable

from spooli.constants import ansi as _ansi
from spooli.storage import init_db
from spooli.ui.input import pause, safe_input
from spooli.ui.screens.failed_prints import register_failed_print
from spooli.ui.screens.history import show_history
from spooli.ui.screens.inventory import show_inventory
from spooli.ui.screens.settings import show_settings
from spooli.ui.screens.spool_form import create_spool_form


def main_menu() -> None:
    """Run the main interactive navigation loop."""
    init_db()
    entries: list[tuple[str, str, Callable[[], None]]] = [
        ("1", "Ver Inventario", show_inventory),
        ("2", "Registrar Nueva Bobina", create_spool_form),
        ("3", "Registrar Pieza Fallida", register_failed_print),
        ("4", "Historial de Impresiones", show_history),
        ("5", "Configuración", show_settings),
    ]
    handlers = {key: action for key, _, action in entries}
    while True:
        print(f"\n{_ansi.paint('=== Spooli - Menú Principal ===', _ansi.BOLD, _ansi.CYAN)}")
        for key, label, _ in entries:
            print(f"{key}. {label}")
        print("6. Salir")

        choice_raw = safe_input("Selecciona una opción (1-6): ")
        if choice_raw is None:
            print("Saliendo...")
            break
        choice = choice_raw.strip()

        if choice == "6":
            print("Saliendo... ¡Hasta pronto!")
            break
        action = handlers.get(choice)
        if action is None:
            print(_ansi.paint("Opción no válida. Elige un número del 1 al 6.", _ansi.YELLOW))
            continue
        action()
        pause()


__all__ = ["main_menu"]
