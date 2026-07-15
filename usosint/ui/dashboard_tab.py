"""Дашборд: обзор системы, инструментов и извлечённых сущностей."""

import platform
import re
import socket

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.ui.base_tab import BaseTab
from usosint.ui.theme import COLORS
from usosint.ui.widgets import StatusChip

MONITORED_TOOLS = [
    "nmap", "tor", "proxychains4", "bettercap", "tcpdump",
    "macchanger", "subfinder", "git", "whois",
]

_IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
_DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+(?:com|net|org|io|ru|su|info|biz|dev|app|me|cc|xyz|pro|gov|edu|de|es|cn|uk|fr)\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\+\d[\d\s\-()]{7,15}\d")


class DashboardTab(BaseTab):
    """Стартовая вкладка в стиле Maltego: статус среды и найденные сущности."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self._build()
        Clock.schedule_interval(self._refresh_entities, 2.0)

    # ---------- построение ----------

    def _build(self):
        # --- система ---
        sys_card = self.create_card(tr("sys_info"), icon="monitor-dashboard")
        grid = MDGridLayout(cols=2, spacing=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        local_ip = self._detect_ip()
        rows = [
            (tr("platform"), f"{platform.system()} {platform.release()}"),
            (tr("python_ver"), platform.python_version()),
            (tr("hostname"), socket.gethostname()),
            (tr("local_ip"), local_ip),
        ]
        for key, value in rows:
            grid.add_widget(self._info_label(key, secondary=True))
            grid.add_widget(self._info_label(str(value)))
        sys_card.add_widget(grid)

        # --- инструменты ---
        tools_card = self.create_card(tr("tools_status"), icon="tools")
        chips = MDGridLayout(
            cols=3,
            spacing=dp(6),
            size_hint_y=None,
            adaptive_height=True,
        )
        for tool in MONITORED_TOOLS:
            ok = self.executor.check_tool(tool)
            chips.add_widget(StatusChip(f"{tool}", ok=ok))
        tools_card.add_widget(chips)
        avail = sum(1 for t in MONITORED_TOOLS if self.executor.check_tool(t))
        self.tools_summary = (avail, len(MONITORED_TOOLS))

        # --- сущности ---
        ent_card = self.create_card(tr("entities"), icon="graph-outline")
        self.entities_grid = MDGridLayout(
            cols=2, spacing=dp(4), size_hint_y=None, adaptive_height=True
        )
        self.entities_empty = self.create_label(tr("entities_empty"), secondary=True)
        ent_card.add_widget(self.entities_empty)
        ent_card.add_widget(self.entities_grid)

        # --- быстрые действия ---
        qa_card = self.create_card(tr("quick_actions"), icon="lightning-bolt")
        qa_box = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(44))
        from usosint.modules.export import ExportManager
        self._export_manager = ExportManager(self.logger, self.executor)
        report_btn = self.create_button(
            tr("qa_report"),
            lambda *_: self.run_in_thread(self._export_manager.generate_local_report, name="report"),
            icon="file-document-outline",
        )
        report_btn.size_hint_x = None
        report_btn.width = dp(320)
        qa_box.add_widget(report_btn)
        qa_card.add_widget(qa_box)

    def _info_label(self, text: str, secondary: bool = False) -> MDLabel:
        return MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"] if secondary else COLORS["text_primary"],
            font_size=dp(12),
            size_hint_y=None,
            height=dp(22),
        )

    @staticmethod
    def _detect_ip() -> str:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ---------- сущности из логов ----------

    def _refresh_entities(self, dt):
        history = self.logger.get_history()
        text = "\n".join(history[-300:])
        entities = {
            tr("ent_ip"): sorted(set(_IP_RE.findall(text)))[:8],
            tr("ent_domain"): sorted(set(_DOMAIN_RE.findall(text)))[:8],
            tr("ent_email"): sorted(set(_EMAIL_RE.findall(text)))[:8],
            tr("ent_phone"): sorted(set(_PHONE_RE.findall(text)))[:4],
        }
        entities = {k: v for k, v in entities.items() if v}

        self.entities_grid.clear_widgets()
        if not entities:
            self.entities_empty.text = tr("entities_empty")
            self.entities_empty.height = dp(22)
            return
        self.entities_empty.text = ""
        self.entities_empty.height = 0

        for kind, values in entities.items():
            self.entities_grid.add_widget(self._info_label(f"{kind} ({len(values)})", secondary=True))
            box = MDBoxLayout(orientation="vertical", size_hint_y=None, adaptive_height=True)
            for value in values:
                box.add_widget(MDLabel(
                    text=value,
                    theme_text_color="Custom",
                    text_color=COLORS["neon_green"],
                    font_size=dp(11),
                    size_hint_y=None,
                    height=dp(18),
                ))
            self.entities_grid.add_widget(box)
