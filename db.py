"""Backwards-compatible facade of the :mod:`spooli.storage` package.

The persistence layer now lives in ``spooli.storage``; this module keeps the
historical ``db`` import path working for the CLI modules and the test-suite.
"""

from pathlib import Path

from spooli.constants.defaults import DEFAULT_SETTINGS
from spooli.storage import (
    connection_scope,
    convert_all_records_currency,
    create_spool,
    get_all_spools,
    get_compatible_spools,
    get_connection,
    get_data_dir,
    get_float_setting,
    get_print_history,
    get_setting,
    get_spool_by_id,
    init_db,
    record_print_job,
    resolve_db_path,
    set_setting,
    update_failed_print,
)
from spooli.storage import paths as _paths

__all__ = [
    "DEFAULT_SETTINGS",
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


def get_db_path() -> Path:
    """Return the path of the active database file."""
    return _paths.default_db_path()


# Keep "db.get_db_path" as the single lookup point of the active database
# path, so overriding it here also redirects the implicit accesses of the
# storage layer.
_paths.set_db_path_resolver(lambda: get_db_path())
