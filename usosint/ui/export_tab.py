"""Вкладка интеграции и экспорта."""

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.modules.export import ExportManager
from usosint.ui.base_tab import BaseTab, TabHeader


class ExportTab(BaseTab):
    """Вкладка интеграции и экспорта результатов."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.tab_id = "export"

        self.export_manager = ExportManager(logger, executor)

        self.layout.add_widget(TabHeader("exp_title", "exp_warn"))

        card = self.create_card(tr("exp_title"), icon="export")
        card.add_widget(self.create_button(
            tr("report_btn"), self._on_local_report, icon="file-document-outline"
        ))

        card.add_widget(self.create_label(tr("repo_label"), secondary=True))
        self.repo_input = self.create_input(tr("repo_hint"), tr("repo_helper"))
        card.add_widget(self.repo_input)
        card.add_widget(self.create_button(
            tr("sync_btn"), self._on_github_sync, icon="github"
        ))

    def _on_local_report(self, instance):
        self.log(f"{tr('launching')}: report...")
        self.run_in_thread(self.export_manager.generate_local_report, name="report")

    def _on_github_sync(self, instance):
        repo_url = self.repo_input.text.strip()
        self.log(f"{tr('launching')}: git sync...")
        self.run_in_thread(self.export_manager.github_sync, repo_url, name="git-sync")
