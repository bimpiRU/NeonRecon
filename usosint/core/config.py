"""Персистентная конфигурация приложения (JSON в домашней директории)."""

import json
import os

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".usosint")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")

_cache = None


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            _cache = json.load(fh)
    except Exception:
        _cache = {}
    return _cache


def get(key: str, default=None):
    """Прочитать значение конфигурации."""
    return _load().get(key, default)


def set_value(key: str, value):
    """Записать значение и сохранить на диск."""
    cfg = _load()
    cfg[key] = value
    try:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass
