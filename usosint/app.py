"""Корневой виджет приложения."""

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.tab import MDTabs

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.ui.export_tab import ExportTab
from usosint.ui.log_panel import LogPanel
from usosint.ui.network_tab import NetworkTab
from usosint.ui.opsec_tab import OpsecTab
from usosint.ui.osint_tab import OsintTab
from usosint.ui.theme import COLORS, apply_theme


class USOSINTApp(MDApp):
    """Главное приложение Universal Security & OSINT Assistant."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Universal Security & OSINT Assistant"
        self.logger = AppLogger()
        self.executor = CommandExecutor(self.logger)
        self.disclaimer_dialog = None

    def build(self):
        apply_theme(self)

        root = MDBoxLayout(orientation="vertical", spacing=0)

        # Вкладки
        tabs = MDTabs(
            background_color=COLORS["bg_dark"],
            text_color_active=COLORS["neon_green"],
            text_color_normal=COLORS["text_secondary"],
            indicator_color=COLORS["neon_green"],
            size_hint_y=0.75,
        )

        tabs.add_widget(OpsecTab(self.logger, self.executor))
        tabs.add_widget(NetworkTab(self.logger, self.executor))
        tabs.add_widget(OsintTab(self.logger, self.executor))
        tabs.add_widget(ExportTab(self.logger, self.executor))

        root.add_widget(tabs)

        # Панель логов
        log_panel = LogPanel(self.logger, size_hint_y=0.25)
        root.add_widget(log_panel)

        # Показать дисклеймер после первого запуска
        Clock.schedule_once(lambda dt: self.show_disclaimer(), 0.5)

        return root

    def show_disclaimer(self):
        """Показать стартовый дисклеймер."""
        disclaimer_text = (
            "Universal Security & OSINT Assistant предназначен исключительно для легального аудита "
            "безопасности систем, принадлежащих вам или на которые у вас есть письменное разрешение "
            "владельца.\n\n"
            "Запрещается использовать ПО для несанкционированного доступа, перехвата чужого трафика, "
            "сбора персональных данных без согласия и иной неправомерной деятельности.\n\n"
            "Используя приложение, вы принимаете на себя полную ответственность за соблюдение "
            "применимого законодательства."
        )

        self.disclaimer_dialog = MDDialog(
            title="⚠️ Юридический дисклеймер",
            text=disclaimer_text,
            size_hint=(0.9, None),
            height=dp(400),
            buttons=[
                MDFlatButton(
                    text="ОТКАЗАТЬСЯ",
                    theme_text_color="Custom",
                    text_color=COLORS["neon_red"],
                    on_release=self.exit_app,
                ),
                MDRaisedButton(
                    text="ПРИНИМАЮ",
                    md_bg_color=COLORS["neon_green"],
                    text_color=COLORS["bg_dark"],
                    on_release=self.dismiss_disclaimer,
                ),
            ],
        )
        self.disclaimer_dialog.open()

    def dismiss_disclaimer(self, *args):
        """Закрыть дисклеймер."""
        if self.disclaimer_dialog:
            self.disclaimer_dialog.dismiss()
        self.logger.info("Дисклеймер принят. Приложение готово к работе.")

    def exit_app(self, *args):
        """Завершить приложение."""
        self.stop()

    def on_stop(self):
        """Очистка при завершении."""
        self.executor.shutdown(wait=False)
