"""Вкладка интеграции и экспорта."""

from kivy.metrics import dp
from kivymd.uix.textfield import MDTextField

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.modules.export import ExportManager
from usosint.ui.base_tab import BaseTab


class ExportTab(BaseTab):
    """Вкладка интеграции и экспорта результатов."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.title = "Экспорт"

        self.export_manager = ExportManager(logger, executor)

        self.layout.add_widget(self.create_section_title("Интеграция и экспорт"))
        self.layout.add_widget(
            self.create_label(
                "⚠️ Убедитесь, что отчёты не содержат чувствительных данных перед отправкой.",
                secondary=True,
            )
        )

        self.layout.add_widget(self.create_button("Локальный отчёт", self._on_local_report))

        self.layout.add_widget(self.create_label("URL приватного репозитория (опционально):", secondary=True))
        self.repo_input = MDTextField(
            hint_text="https://github.com/user/private-repo.git",
            helper_text="Для автоматического git remote add",
            helper_text_mode="persistent",
            size_hint_y=None,
            height=dp(48),
        )
        self.layout.add_widget(self.repo_input)

        self.layout.add_widget(self.create_button("GitHub Синхронизация", self._on_github_sync))

    def _on_local_report(self, instance):
        self.log("Генерация локального отчёта...")
        self.run_in_thread(self.export_manager.generate_local_report)

    def _on_github_sync(self, instance):
        repo_url = self.repo_input.text.strip()
        self.log("Подготовка GitHub-синхронизации...")
        self.run_in_thread(self.export_manager.github_sync, repo_url)
