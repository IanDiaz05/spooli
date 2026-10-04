"""Global installer for the spooli command (no admin rights required)."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

from spooli.constants.paths import (
    LAUNCHER_NAME,
    MAIN_SCRIPT_NAME,
    UNIX_BIN_DIR,
    WINDOWS_FALLBACK_DIR,
    WINDOWS_WRAPPER_NAME,
)


def resolve_main_path() -> Path:
    # Absolute path to main.py next to this installer.
    return Path(__file__).resolve().parent / MAIN_SCRIPT_NAME


def is_unix() -> bool:
    # True for Linux/macOS, False for Windows.
    return sys.platform != "win32"


def target_in_path(target: Path) -> bool:
    # Check whether target dir is listed in PATH.
    path_value = os.environ.get("PATH", "")
    entries = [p for p in path_value.split(os.pathsep) if p]
    target_str = str(target)
    for entry in entries:
        try:
            if os.path.normcase(os.path.normpath(entry)) == os.path.normcase(
                os.path.normpath(target_str)
            ):
                return True
        except Exception:
            if entry == target_str:
                return True
    return False


def install_unix(main_path: Path, quiet: bool = False) -> int:
    # Install bash wrapper into the user bin directory.
    target_dir = Path.home() / UNIX_BIN_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    wrapper = target_dir / LAUNCHER_NAME
    content = f'#!/bin/sh\npython3 "{main_path}" "$@"\n'
    wrapper.write_text(content, encoding="utf-8")
    current_mode = os.stat(wrapper).st_mode
    os.chmod(
        wrapper,
        current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
    )
    if not quiet:
        print(f"Comando '{LAUNCHER_NAME}' instalado correctamente en: {wrapper}")
    if target_in_path(target_dir):
        if not quiet:
            print(
                "La instalación está lista. Ya puedes usar el comando "
                f"'{LAUNCHER_NAME}'."
            )
    else:
        if not quiet:
            print(f"Advertencia: el directorio '{target_dir}' no está en el PATH.")
            print("Reinicia tu terminal o agrega esta línea a tu ~/.bashrc o ~/.zshrc:")
            print(f'  export PATH="$HOME/{UNIX_BIN_DIR}:$PATH"')
    return 0


def resolve_windows_target() -> Path:
    # Prefer user-level WindowsApps dir, fall back to the home-based bin dir.
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        candidate = Path(local_app_data) / "Microsoft" / "WindowsApps"
    else:
        candidate = Path.home() / WINDOWS_FALLBACK_DIR
    return candidate


def install_windows(main_path: Path, quiet: bool = False) -> int:
    # Install batch wrapper spooli.cmd into a user-level dir.
    target_dir = resolve_windows_target()
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        fallback = Path.home() / WINDOWS_FALLBACK_DIR
        fallback.mkdir(parents=True, exist_ok=True)
        target_dir = fallback
    wrapper = target_dir / WINDOWS_WRAPPER_NAME
    content = f'@echo off\r\npython "{main_path}" %*\r\n'
    wrapper.write_text(content, encoding="utf-8")
    if not quiet:
        print(f"Comando '{LAUNCHER_NAME}' instalado correctamente en: {wrapper}")
    if target_in_path(target_dir):
        if not quiet:
            print(
                "La instalación está lista. Ya puedes usar el comando "
                f"'{LAUNCHER_NAME}'."
            )
    else:
        if not quiet:
            print(f"Advertencia: el directorio '{target_dir}' no está en el PATH.")
            print("Reinicia tu terminal para que los cambios surtan efecto")
            print("o agrega el directorio al PATH del usuario en la configuración de Windows.")
    return 0


def install_cli(quiet: bool = False) -> bool:
    # Import-safe entry point: install global spooli command, no subprocess needed.
    try:
        main_path = resolve_main_path()
    except Exception:
        if not quiet:
            print(f"Error: no se pudo resolver la ruta de '{MAIN_SCRIPT_NAME}'.")
        return False
    if not main_path.is_file():
        if not quiet:
            print(f"Error: no se encontró el archivo '{main_path}'.")
        return False
    try:
        if is_unix():
            code = install_unix(main_path, quiet=quiet)
        else:
            code = install_windows(main_path, quiet=quiet)
        return code == 0
    except Exception as exc:
        if not quiet:
            print(f"Error durante la instalación: {exc}")
        return False


def main() -> int:
    ok = install_cli(quiet=False)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
