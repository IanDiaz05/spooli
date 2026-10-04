"""SQLite persistence layer of Spooli.

The responsibilities are split by module: path resolution, connection
lifecycle, schema and migrations, settings, spools and print jobs. The root
``db`` module re-exports this public API for backwards compatibility.
"""

from .connection import connection_scope, get_connection, resolve_db_path
from .paths import get_data_dir, get_db_path
from .print_repo import (
    convert_all_records_currency,
    get_print_history,
    record_print_job,
    update_failed_print,
)
from .schema import init_db
from .settings_store import get_float_setting, get_setting, set_setting
from .spool_repo import (
    create_spool,
    get_all_spools,
    get_compatible_spools,
    get_spool_by_id,
)

__all__ = [
    "connection_scope",
    "convert_all_records_currency",
    "create_spool",
    "get_all_spools",
    "get_compatible_spools",
    "get_connection",
    "get_data_dir",
    "get_db_path",
    "get_float_setting",
    "get_print_history",
    "get_setting",
    "get_spool_by_id",
    "init_db",
    "record_print_job",
    "resolve_db_path",
    "set_setting",
    "update_failed_print",
]
