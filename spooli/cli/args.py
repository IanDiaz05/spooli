"""Command-line argument parsing."""

from __future__ import annotations

import argparse
from typing import Optional


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Spooli - control de filamento")
    parser.add_argument("file_path", nargs="?", help="Archivo .gcode o .3mf")
    parser.add_argument("--spool", type=int, default=None, help="ID de bobina a usar")
    parser.add_argument("--yes", "-y", action="store_true", help="Omitir confirmacion")
    return parser.parse_args(args)


__all__ = ["parse_args"]
