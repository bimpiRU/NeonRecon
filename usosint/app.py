"""Корневой виджет приложения: header + sidebar + content + status bar."""

import time

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDIcon, MDLabel
from kivymd.uix.menu import MDDropdownMenu

from usosint.core import config
from usosint.core.executor import CommandExecutor
from usosint.core.i18n import LANGUAGES, get_language, set_language, tr
from usosint.core.logger import AppLogger
from usosint.core.platform import platform_label
from usosint.ui.dashboard_tab import DashboardTab
from usosint.ui.export_tab import ExportTab
from usosint.ui.log_panel import LogPanel
from usosint.ui.network_tab import NetworkTab
from usosint.ui.opsec_tab import OpsecTab
from usosint.ui.osint_tab import OsintTab
from usosint.ui.reports_tab import ReportsTab
from usosint.ui.theme import COLORS, apply_theme
from usosint.ui.widgets import BottomNavButton, NavButton

APP_VERSION = "0.6"

NAV_ITEMS = [
    ("dashboard", "view-dashboard", "nav_dashboard"),
    ("opsec", "shield-lock", "nav_opsec"),
    ("network", "radar", "nav_network"),
    ("osint", "magnify-scan", "nav_osint"),
    ("reports", "archive-outline", "nav_reports"),
    ("export", "export", "nav_export"),
]


class USOSINTApp(MDApp):
    """Главное приложение NeonRecon (Universal Security & OSINT Assistant)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "NeonRecon — Universal Security & OSINT Assistant"
        self.logger = AppLogger()
        self.executor = CommandExecutor(self.logger)
        self.disclaimer_dialog = None
        self._started_at = time.time()
        self._current_tab = "dashboard"
        self._tabs = {}
        self._nav_buttons = {}

        lang = config.get("language", "ru")
        set_language(lang)
        self._mobile = None
        self._bottom_nav_buttons = {}

    # ---------- построение ----------

    @staticmethod
    def _mobile_width() -> bool:
        """Узкая ширина окна — переключаемся на мобильную раскладку."""
        return Window.width < dp(940)

    def _is_mobile(self) -> bool:
        from usosint.core.platform import is_android
        return is_android() or self._mobile_width()

    def build(self):
        apply_theme(self)
        Window.clearcolor = COLORS["bg_dark"]
        try:
            from usosint.core.platform import is_android
            if not is_android():
                Window.size = (1360, 860)
                Window.minimum_width = 1024
                Window.minimum_height = 700
        except Exception:
            pass

        root = MDBoxLayout(orientation="vertical", spacing=0)
        root.add_widget(self._build_header())
        root.add_widget(MDBoxLayout(
            size_hint_y=None, height=dp(1), md_bg_color=COLORS["border"],
        ))

        self._body = MDBoxLayout(orientation="horizontal", spacing=0)
        self.sidebar = self._build_sidebar()
        self._body.add_widget(self.sidebar)

        right = MDBoxLayout(orientation="vertical", spacing=0)
        self.content_area = MDBoxLayout(orientation="vertical", size_hint_y=0.72)
        right.add_widget(self.content_area)
        right.add_widget(LogPanel(self.logger, size_hint_y=0.28))
        self._body.add_widget(right)
        root.add_widget(self._body)

        root.add_widget(MDBoxLayout(
            size_hint_y=None, height=dp(1), md_bg_color=COLORS["border"],
        ))
        self.bottom_nav = self._build_bottom_nav()
        root.add_widget(self._build_statusbar())

        self._mobile = None
        self._root_ref = root
        self._apply_layout_mode()
        Window.bind(width=lambda *_: self._apply_layout_mode())

        self._switch_tab("dashboard")
        self.executor.add_listener(self._on_tasks_changed)
        Clock.schedule_interval(self._tick, 1.0)
        Clock.schedule_once(lambda dt: self.show_disclaimer(), 0.5)
        return root

    def _apply_layout_mode(self):
        """Переключить раскладку desktop <-> mobile по ширине окна/платформе."""
        mobile = self._is_mobile()
        if mobile == self._mobile:
            return
        self._mobile = mobile
        root = self._root_ref
        if mobile:
            if self.sidebar.parent is not None:
                self._body.remove_widget(self.sidebar)
            if self.bottom_nav.parent is None:
                # вставляем над статус-баром (children в Kivy — в обратном порядке)
                root.add_widget(self.bottom_nav, index=1)
            self.subtitle_label.text = ""
        else:
            if self.sidebar.parent is None:
                self._body.add_widget(self.sidebar, index=1)
            if self.bottom_nav.parent is not None:
                root.remove_widget(self.bottom_nav)
            self.subtitle_label.text = tr("app_subtitle")

    def _build_bottom_nav(self) -> MDBoxLayout:
        bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(58),
            md_bg_color=COLORS["bg_panel"],
        )
        self._bottom_nav_buttons = {}
        for tab_id, icon, _title_key in NAV_ITEMS:
            btn = BottomNavButton(
                icon=icon,
                callback=lambda tid=tab_id: self._switch_tab(tid),
            )
            self._bottom_nav_buttons[tab_id] = btn
            bar.add_widget(btn)
        return bar

    def _build_header(self) -> MDBoxLayout:
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(68),
            padding=(dp(18), 0, dp(12), 0),
            spacing=dp(12),
            md_bg_color=COLORS["bg_panel"],
        )
        header.add_widget(MDIcon(
            icon="hexagon-slice-6",
            theme_text_color="Custom",
            text_color=COLORS["neon_green"],
            font_size=dp(34),
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={"center_y": 0.5},
        ))
        title_box = MDBoxLayout(orientation="vertical", spacing=0)
        title_box.add_widget(MDLabel(
            text=f"[b]{tr('app_title')}[/b]  [color=00FF9D]v{APP_VERSION}[/color]",
            markup=True,
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            font_size=dp(21),
        ))
        title_box.add_widget(MDLabel(
            text=tr("app_subtitle"),
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            font_size=dp(12),
        ))
        header.add_widget(title_box)
        self.subtitle_label = title_box.children[0]

        # чип платформы
        header.add_widget(MDLabel(
            text=platform_label(),
            theme_text_color="Custom",
            text_color=COLORS["neon_blue"],
            font_size=dp(13),
            size_hint_x=None,
            width=dp(110),
            halign="right",
        ))

        # выбор языка
        self.lang_button = MDFlatButton(
            text=LANGUAGES[get_language()],
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            font_size=dp(13),
            size_hint=(None, None),
            size=(dp(130), dp(40)),
            pos_hint={"center_y": 0.5},
            on_release=self._open_lang_menu,
        )
        header.add_widget(self.lang_button)
        return header

    def _build_sidebar(self) -> MDBoxLayout:
        sidebar = MDBoxLayout(
            orientation="vertical",
            size_hint_x=None,
            width=dp(228),
            spacing=dp(4),
            padding=(0, dp(14), 0, 0),
            md_bg_color=COLORS["bg_panel"],
        )
        for tab_id, icon, title_key in NAV_ITEMS:
            btn = NavButton(
                icon=icon,
                text=tr(title_key),
                callback=lambda tid=tab_id: self._switch_tab(tid),
            )
            btn.title_key = title_key
            self._nav_buttons[tab_id] = btn
            sidebar.add_widget(btn)
        # распорка прижимает кнопки к верху
        sidebar.add_widget(MDBoxLayout(size_hint_y=1))
        return sidebar

    def _build_statusbar(self) -> MDBoxLayout:
        bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(38),
            padding=(dp(16), 0, dp(16), 0),
            spacing=dp(18),
            md_bg_color=COLORS["bg_panel"],
        )
        self.status_dot = MDIcon(
            icon="circle",
            theme_text_color="Custom",
            text_color=COLORS["neon_green"],
            font_size=dp(12),
            size_hint=(None, None),
            size=(dp(16), dp(16)),
            pos_hint={"center_y": 0.5},
        )
        bar.add_widget(self.status_dot)
        self.status_text = MDLabel(
            text=tr("st_ready"),
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            font_size=dp(13),
        )
        bar.add_widget(self.status_text)
        self.session_text = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            font_size=dp(13),
            size_hint_x=None,
            width=dp(240),
            halign="right",
        )
        bar.add_widget(self.session_text)
        self.stop_button = MDFlatButton(
            text=tr("stop_all"),
            theme_text_color="Custom",
            text_color=COLORS["neon_red"],
            font_size=dp(13),
            size_hint=(None, None),
            size=(dp(130), dp(30)),
            pos_hint={"center_y": 0.5},
            on_release=self._stop_all_tasks,
        )
        bar.add_widget(self.stop_button)
        return bar

    # ---------- навигация ----------

    def _switch_tab(self, tab_id: str):
        self._current_tab = tab_id
        if tab_id not in self._tabs:
            factory = {
                "dashboard": DashboardTab,
                "opsec": OpsecTab,
                "network": NetworkTab,
                "osint": OsintTab,
                "reports": ReportsTab,
                "export": ExportTab,
            }[tab_id]
            self._tabs[tab_id] = factory(self.logger, self.executor)

        tab = self._tabs[tab_id]
        self.content_area.clear_widgets()
        self.content_area.add_widget(tab)
        # плавное появление содержимого
        from kivy.animation import Animation
        tab.opacity = 0
        Animation.cancel_all(tab, "opacity")
        Animation(opacity=1, duration=0.18, t="out_quad").start(tab)
        if hasattr(tab, "on_show"):
            try:
                tab.on_show()
            except Exception:
                pass
        for tid, btn in self._nav_buttons.items():
            btn.set_active(tid == tab_id)
        for tid, btn in self._bottom_nav_buttons.items():
            btn.set_active(tid == tab_id)

    # ---------- статус-бар ----------

    def _on_tasks_changed(self):
        Clock.schedule_once(lambda dt: self._refresh_status(), 0)

    def _refresh_status(self):
        count = self.executor.running_count()
        if count:
            names = ", ".join(self.executor.running_names()[:3])
            self.status_text.text = f"{tr('st_tasks')}: {count} · {names}"
            self.status_dot.text_color = COLORS["neon_amber"]
        else:
            self.status_text.text = tr("st_ready")
            self.status_dot.text_color = COLORS["neon_green"]

    def _tick(self, dt):
        elapsed = int(time.time() - self._started_at)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        self.session_text.text = f"{tr('st_session')} {h:02d}:{m:02d}:{s:02d}"

    def _stop_all_tasks(self, *_):
        self.executor.cancel_all()
        self.logger.warning(tr("stopped_all"))

    # ---------- язык ----------

    def _open_lang_menu(self, *_):
        items = [
            {
                "text": name,
                "viewclass": "OneLineListItem",
                "on_release": lambda code=code: self._select_language(code),
            }
            for code, name in LANGUAGES.items()
        ]
        self._lang_menu = MDDropdownMenu(
            caller=self.lang_button,
            items=items,
            width_mult=3,
        )
        self._lang_menu.open()

    def _select_language(self, code: str):
        self._lang_menu.dismiss()
        if code == get_language():
            return
        set_language(code)
        config.set_value("language", code)
        # пересобираем интерфейс с новыми строками
        self._tabs.clear()
        self.root.clear_widgets()
        rebuilt = self.build()
        for child in list(self.root.children):
            self.root.remove_widget(child)
        self.root.add_widget(rebuilt)

    # ---------- дисклеймер ----------

    def show_disclaimer(self):
        """Показать стартовый дисклеймер (один раз, пока не принят)."""
        if config.get("disclaimer_accepted"):
            self.logger.info(tr("disclaimer_ok"))
            return
        self.disclaimer_dialog = MDDialog(
            title="⚠ " + tr("disclaimer_title"),
            text=tr("disclaimer_text"),
            size_hint=(0.92, None),
            height=dp(480),
            buttons=[
                MDFlatButton(
                    text=tr("decline"),
                    theme_text_color="Custom",
                    text_color=COLORS["neon_red"],
                    on_release=self.exit_app,
                ),
                MDRaisedButton(
                    text=tr("accept"),
                    md_bg_color=COLORS["neon_green"],
                    text_color=COLORS["bg_dark"],
                    on_release=self.dismiss_disclaimer,
                ),
            ],
        )
        self.disclaimer_dialog.open()

    def dismiss_disclaimer(self, *args):
        """Закрыть дисклеймер и запомнить согласие."""
        if self.disclaimer_dialog:
            self.disclaimer_dialog.dismiss()
        config.set_value("disclaimer_accepted", True)
        self.logger.info(tr("disclaimer_ok"))

    def exit_app(self, *args):
        """Завершить приложение."""
        self.stop()

    def on_stop(self):
        """Очистка при завершении."""
        self.executor.shutdown(wait=False)
