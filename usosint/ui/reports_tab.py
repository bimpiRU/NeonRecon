"""Вкладка «Отчёты»: сжатый архив результатов (gzip, ротация)."""

from functools import partial

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.core.report_store import ReportStore, format_size
from usosint.ui.base_tab import BaseTab, TabHeader
from usosint.ui.theme import COLORS

_MAX_ROWS = 30
_MAX_DUMP_LINES = 120


class ReportsTab(BaseTab):
    """Архив сжатых отчётов: список, просмотр в логе, удаление."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.tab_id = "reports"
        self.store = ReportStore()

        self.layout.add_widget(TabHeader("rep_title", "rep_warn"))

        actions_card = self.create_card(tr("quick_actions"), icon="lightning-bolt")
        actions_card.add_widget(self.create_button(
            tr("rep_save_log"), self._on_save_log, icon="content-save-outline"
        ))
        actions_card.add_widget(self.create_button(
            tr("rep_clear"), self._on_clear, icon="delete-sweep-outline"
        ))

        self.archive_card = self.create_card(tr("rep_archive"), icon="archive-outline")
        self.summary_label = self.create_label("", secondary=True)
        self.archive_card.add_widget(self.summary_label)
        self.list_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            adaptive_height=True,
            spacing=dp(4),
        )
        self.archive_card.add_widget(self.list_box)
        self.refresh()

    # вызывается приложением при переключении на вкладку
    def on_show(self):
        self.refresh()

    # ---------- данные ----------

    def refresh(self):
        """Перечитать архив и перестроить список."""
        reports = self.store.list()
        total = self.store.total_size()
        self.summary_label.text = tr("rep_summary").format(
            count=len(reports), size=format_size(total)
        )
        self.list_box.clear_widgets()
        if not reports:
            self.list_box.add_widget(self.create_label(tr("rep_empty"), secondary=True))
            return
        for meta in reports[:_MAX_ROWS]:
            self.list_box.add_widget(self._make_row(meta))

    def _make_row(self, meta: dict) -> MDBoxLayout:
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6),
        )
        row.add_widget(MDLabel(
            text=(
                f"{meta['created']}  ·  {meta['kind']}  ·  "
                f"{meta['target']}  ·  {format_size(meta['size'])}"
            ),
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            font_size=dp(13),
        ))
        open_btn = MDFlatButton(
            text=tr("rep_open"),
            theme_text_color="Custom",
            text_color=COLORS["neon_green"],
            size_hint=(None, None),
            size=(dp(110), dp(32)),
            pos_hint={"center_y": 0.5},
            on_release=partial(self._on_open, meta),
        )
        del_btn = MDFlatButton(
            text="✕",
            theme_text_color="Custom",
            text_color=COLORS["neon_red"],
            size_hint=(None, None),
            size=(dp(40), dp(32)),
            pos_hint={"center_y": 0.5},
            on_release=partial(self._on_delete, meta),
        )
        row.add_widget(open_btn)
        row.add_widget(del_btn)
        return row

    # ---------- действия ----------

    def _on_open(self, meta: dict, *_):
        data = self.store.load(meta["id"])
        if not data:
            self.log(f"{tr('rep_open_error')}: {meta['id']}", "ERROR")
            return
        self.log(f"===== {data.get('title', meta['id'])} ({meta['id']}) =====")
        for line in data.get("lines", [])[-_MAX_DUMP_LINES:]:
            self.log(line)
        self.log(f"===== {tr('rep_end')} =====", "OK")

    def _on_delete(self, meta: dict, *_):
        if self.store.delete(meta["id"]):
            self.log(f"{tr('rep_deleted')}: {meta['id']}", "WARN")
        self.refresh()

    def _on_save_log(self, *_):
        lines = self.logger.get_history()
        if not lines:
            self.log(tr("rep_empty"), "WARN")
            return
        report_id = self.store.save("log", "session", tr("rep_log_title"), lines)
        self.log(f"{tr('rep_saved')}: {report_id}", "OK")
        self.refresh()

    def _on_clear(self, *_):
        removed = self.store.clear()
        self.log(f"{tr('rep_cleared')}: {removed}", "WARN")
        self.refresh()
