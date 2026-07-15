"""Утилиты для определения платформы и окружения."""

import os
import platform
import shutil


def is_android() -> bool:
    """Проверить, запущено ли приложение на Android."""
    return "ANDROID_STORAGE" in os.environ or os.path.exists("/system/build.prop")


def is_linux() -> bool:
    """Проверить, что система Linux (не Android)."""
    return platform.system().lower() == "linux" and not is_android()


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_root() -> bool:
    """Проверить, запущен ли процесс с правами root (Unix)."""
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def has_sudo() -> bool:
    """Проверить наличие sudo (Linux, не Android)."""
    return os.name == "posix" and not is_android() and shutil.which("sudo") is not None


def sudo_prefix() -> list:
    """Префикс для команды, требующей root: sudo -n, если мы не root.

    Возвращает [] если root уже есть или sudo недоступен.
    """
    if is_root() or not has_sudo():
        return []
    return ["sudo", "-n"]


def check_tool(name: str) -> bool:
    """Проверить наличие утилиты в PATH."""
    return shutil.which(name) is not None


def platform_label() -> str:
    """Вернуть человекочитаемую метку платформы."""
    if is_android():
        return "Android"
    if is_linux():
        return "Linux"
    if is_windows():
        return "Windows"
    return platform.system()


def get_desktop_path() -> str:
    """Вернуть путь к рабочему столу."""
    if is_windows():
        return os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    return os.path.join(os.environ.get("HOME", "/tmp"), "Desktop")


def ensure_dir(path: str) -> str:
    """Создать директорию, если её нет."""
    os.makedirs(path, exist_ok=True)
    return path
