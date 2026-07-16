"""Генерация локальных отчётов."""

import os
from datetime import datetime
from typing import Optional

from usosint.core.logger import AppLogger
from usosint.core.platform import ensure_dir, get_desktop_path, platform_label


class ReportGenerator:
    """Собирает логи в финальный отчёт."""

    def __init__(self, logger: AppLogger):
        self.logger = logger

    def generate(self, output_path: Optional[str] = None) -> str:
        """Создать FINAL_REPORT.txt на рабочем столе или по указанному пути.

        На Android рабочего стола нет — отчёт пишется в директорию данных
        приложения (core.storage). Если и она недоступна, возвращается "".
        """
        if output_path is None:
            try:
                desktop = ensure_dir(get_desktop_path())
                output_path = os.path.join(desktop, "FINAL_REPORT.txt")
            except OSError:
                from usosint.core import storage
                base = storage.data_dir()
                if not base:
                    self.logger.error("Не удалось сохранить отчёт: нет записываемой директории")
                    return ""
                output_path = os.path.join(base, "FINAL_REPORT.txt")

        header = [
            "=" * 70,
            "Universal Security & OSINT Assistant — FINAL REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Platform: {platform_label()}",
            "=" * 70,
            "",
            "DISCLAIMER: This report was generated for authorized security audit",
            "and OSINT research only. See DISCLAIMER.md for legal notice.",
            "",
            "=" * 70,
            "",
        ]

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(header))
                for line in self.logger.get_history():
                    f.write(line + "\n")
                f.write("\n" + "=" * 70 + "\nEND OF REPORT\n")
            self.logger.success(f"Отчёт сохранён: {output_path}")
            return output_path
        except Exception as exc:
            self.logger.error(f"Не удалось сохранить отчёт: {exc}")
            return ""
