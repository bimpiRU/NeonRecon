"""Разрешение записываемой директории данных приложения.

На десктопе это ``~/.usosint``. На Android ``~`` указывает в незаписываемый
``/data``, поэтому используется приватное хранилище приложения
(``ANDROID_PRIVATE``). Если и оно недоступно — системный temp.
Функция проверяет кандидатов реальной пробной записью, а не только
существованием пути.
"""

import os
import tempfile
from typing import Optional

_APP_DIRNAME = "usosint_data"

_cached_dir: Optional[str] = None
_resolved: bool = False


def _candidates():
    android_private = os.environ.get("ANDROID_PRIVATE")
    if android_private:
        yield os.path.join(android_private, _APP_DIRNAME)
    yield os.path.join(os.path.expanduser("~"), ".usosint")
    yield os.path.join(tempfile.gettempdir(), _APP_DIRNAME)


def _probe(path: str) -> bool:
    """Проверить, что директорию можно создать и в неё можно писать."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".probe")
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.remove(probe)
        return True
    except Exception:
        return False


def data_dir() -> Optional[str]:
    """Вернуть записываемую директорию данных (или None, если нет ни одной).

    Результат кэшируется: повторные вызовы бесплатны.
    """
    global _cached_dir, _resolved
    if _resolved:
        return _cached_dir
    for path in _candidates():
        if _probe(path):
            _cached_dir = path
            break
    _resolved = True
    return _cached_dir
