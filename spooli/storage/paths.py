"""Resolution of the directories and files used by the storage layer."""

import os
from pathlib import Path
from typing import Callable, Optional

from spooli.constants.paths import APP_DIR_NAME, DB_FILE_NAME


def get_data_dir() -> Path:
    """Return the per-user data directory, creating it when it is missing."""
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        data_dir = Path(base) / APP_DIR_NAME if base else Path.home() / APP_DIR_NAME
    else:
        data_dir = Path.home() / f".{APP_DIR_NAME}"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def default_db_path() -> Path:
    """Return the database path inside the per-user data directory."""
    return get_data_dir() / DB_FILE_NAME


# Indirection installed by the root "db" facade so that overriding
# "db.get_db_path" also redirects the implicit accesses of this package.
_db_path_resolver: Optional[Callable[[], Path]] = None


def set_db_path_resolver(resolver: Optional[Callable[[], Path]]) -> None:
    """Install the callable resolving the active database path."""
    global _db_path_resolver
    _db_path_resolver = resolver


def get_db_path() -> Path:
    """Return the active database path."""
    if _db_path_resolver is not None:
        return Path(_db_path_resolver())
    return default_db_path()
