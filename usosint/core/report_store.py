"""Сжатый архив отчётов приложения.

Каждый отчёт — gzip-сжатый JSON (`<ts>_<kind>_<slug>.json.gz`) в ~/.usosint/reports.
Метаданные читаются из имени файла (список без распаковки), содержимое —
только при открытии. Степень сжатия — максимальная (9), текстовые логи
сжимаются примерно в 8–12 раз. Архив ограничен MAX_REPORTS записями:
самые старые удаляются автоматически.
"""

import gzip
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".usosint")
REPORTS_DIR = os.path.join(_CONFIG_DIR, "reports")

MAX_REPORTS = 200
_GZIP_LEVEL = 9

_FNAME_RE = re.compile(r"^(?P<ts>\d{8}_\d{6})_(?P<kind>[a-z0-9-]+)_(?P<slug>.+)\.json\.gz$")


def _slugify(text: str, limit: int = 40) -> str:
    """Безопасный короткий slug из цели/заголовка для имени файла."""
    slug = re.sub(r"[^A-Za-z0-9.\-]+", "-", text.strip()).strip("-.")
    return (slug or "report")[:limit]


class ReportStore:
    """Хранилище сжатых отчётов с ротацией."""

    def __init__(self, reports_dir: str = REPORTS_DIR, max_reports: int = MAX_REPORTS):
        self.dir = reports_dir
        self.max_reports = max_reports
        os.makedirs(self.dir, exist_ok=True)

    # ---------- запись ----------

    def save(self, kind: str, target: str, title: str, lines: List[str]) -> str:
        """Сохранить отчёт (gzip-9). Возвращает id отчёта (имя файла)."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"{ts}_{_slugify(kind, 16)}_{_slugify(target or title)}.json.gz"
        payload = {
            "ts": ts,
            "kind": kind,
            "target": target,
            "title": title,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lines": list(lines),
        }
        blob = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        with gzip.open(os.path.join(self.dir, fname), "wb", compresslevel=_GZIP_LEVEL) as fh:
            fh.write(blob)
        self._rotate()
        return fname

    def _rotate(self):
        """Удалить самые старые отчёты сверх лимита."""
        files = self._files()
        excess = len(files) - self.max_reports
        for fname in files[:max(0, excess)]:
            self._remove(fname)

    # ---------- чтение ----------

    def _files(self) -> List[str]:
        """Имена файлов отчётов, отсортированные по дате (старые первыми)."""
        try:
            names = [f for f in os.listdir(self.dir) if _FNAME_RE.match(f)]
        except FileNotFoundError:
            return []
        return sorted(names)

    def list(self) -> List[Dict]:
        """Метаданные отчётов (новые первыми) без распаковки содержимого."""
        out = []
        for fname in reversed(self._files()):
            match = _FNAME_RE.match(fname)
            ts, kind, slug = match.group("ts"), match.group("kind"), match.group("slug")
            try:
                created = datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                created = ts
            try:
                size = os.path.getsize(os.path.join(self.dir, fname))
            except OSError:
                size = 0
            out.append({
                "id": fname,
                "created": created,
                "kind": kind,
                "target": slug,
                "size": size,
            })
        return out

    def load(self, report_id: str) -> Optional[Dict]:
        """Распаковать и вернуть отчёт целиком (или None при ошибке)."""
        if not _FNAME_RE.match(report_id or ""):
            return None
        try:
            with gzip.open(os.path.join(self.dir, report_id), "rb") as fh:
                return json.loads(fh.read().decode("utf-8"))
        except Exception:
            return None

    def total_size(self) -> int:
        """Суммарный размер архива на диске (байт)."""
        total = 0
        for fname in self._files():
            try:
                total += os.path.getsize(os.path.join(self.dir, fname))
            except OSError:
                pass
        return total

    # ---------- удаление ----------

    def _remove(self, fname: str) -> bool:
        try:
            os.remove(os.path.join(self.dir, fname))
            return True
        except OSError:
            return False

    def delete(self, report_id: str) -> bool:
        """Удалить один отчёт."""
        if not _FNAME_RE.match(report_id or ""):
            return False
        return self._remove(report_id)

    def clear(self) -> int:
        """Удалить все отчёты. Возвращает число удалённых."""
        removed = 0
        for fname in self._files():
            if self._remove(fname):
                removed += 1
        return removed


def format_size(size: int) -> str:
    """Человекочитаемый размер (КБ/МБ)."""
    if size < 1024:
        return f"{size} Б"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} КБ"
    return f"{size / (1024 * 1024):.2f} МБ"
