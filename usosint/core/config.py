"""Персистентная конфигурация приложения (JSON в директории данных).

Путь разрешается через `core.storage` (на десктопе ~/.usosint,
на Android — приватное хранилище приложения).
"""

import json
import os

from usosint.core import storage

_cache = None


def _config_path():
    base = storage.data_dir()
    return os.path.join(base, "config.json") if base else None


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    path = _config_path()
    if path:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                _cache = json.load(fh)
                return _cache
        except Exception:
            pass
    _cache = {}
    return _cache


def get(key: str, default=None):
    """Прочитать значение конфигурации."""
    return _load().get(key, default)


def set_value(key: str, value):
    """Записать значение и сохранить на диск."""
    cfg = _load()
    cfg[key] = value
    path = _config_path()
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass
