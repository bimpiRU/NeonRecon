"""Модуль интеграции и экспорта."""

import os
import subprocess
from datetime import datetime

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.core.platform import ensure_dir, get_desktop_path, is_windows
from usosint.core.reports import ReportGenerator


class ExportManager:
    """Управление экспортом отчётов и синхронизацией."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor
        self.report_gen = ReportGenerator(logger)

    def generate_local_report(self):
        """Сгенерировать локальный отчёт на рабочем столе."""
        self.logger.info("[EXPORT] Генерация локального отчёта...")
        path = self.report_gen.generate()
        if path:
            self.logger.success(f"[EXPORT] Отчёт сохранён: {path}")

    def github_sync(self, repo_url: str = ""):
        """Подготовить git-репозиторий для синхронизации."""
        self.logger.info("[EXPORT] Подготовка GitHub-синхронизации...")

        # Сначала сгенерируем отчёт
        report_path = self.report_gen.generate()
        if not report_path:
            self.logger.error("[EXPORT] Не удалось создать отчёт.")
            return

        reports_dir = os.path.dirname(report_path)
        self.logger.info(f"[EXPORT] Рабочая директория: {reports_dir}")

        # Проверяем наличие git
        if not self.executor.check_tool("git"):
            self.logger.error("[EXPORT] Git не найден. Установите: sudo apt install git")
            return

        # Инициализация репозитория
        git_dir = os.path.join(reports_dir, ".git")
        if not os.path.exists(git_dir):
            self.executor.run_simple(["git", "init"], timeout=30)
            self.logger.info("[EXPORT] Git-репозиторий инициализирован.")
        else:
            self.logger.info("[EXPORT] Git-репозиторий уже существует.")

        # Добавление отчёта
        self.executor.run_simple(["git", "add", "FINAL_REPORT.txt"], timeout=30)

        # Коммит
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.executor.run_simple(
            ["git", "commit", "-m", f"Security report {timestamp}"],
            timeout=30,
        )
        self.logger.success("[EXPORT] Локальный коммит создан.")

        # Если указан URL репозитория — добавляем remote
        if repo_url:
            self.logger.info(f"[EXPORT] Добавление remote: {repo_url}")
            self.executor.run_simple(
                ["git", "remote", "remove", "origin"],
                timeout=10,
            )
            self.executor.run_simple(
                ["git", "remote", "add", "origin", repo_url],
                timeout=10,
            )
            self.logger.info("[EXPORT] Команды для отправки в приватный репозиторий:")
            self.logger.info(f"  cd {reports_dir}")
            self.logger.info("  git branch -M main")
            self.logger.info("  git push -u origin main")
        else:
            self.logger.info("[EXPORT] Remote не указан. Для отправки выполните вручную:")
            self.logger.info(f"  cd {reports_dir}")
            self.logger.info("  git remote add origin <URL_приватного_репозитория>")
            self.logger.info("  git branch -M main")
            self.logger.info("  git push -u origin main")
