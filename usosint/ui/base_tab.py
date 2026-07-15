"""Базовый класс вкладки."""

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.tab import MDTabsBase

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.ui.theme import COLORS


class BaseTab(MDFloatLayout, MDTabsBase):
    """Базовый класс для всех вкладок."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger
        self.executor = executor
        self.padding = dp(12)
        self.spacing = dp(12)

        # Основной контейнер
        self.layout = MDGridLayout(
            cols=1,
            spacing=dp(12),
            padding=dp(12),
            size_hint=(1, 1),
        )
        self.add_widget(self.layout)

    def log(self, message: str, level: str = "INFO"):
        """Записать сообщение в лог."""
        self.logger.log(message, level)

    def run_in_thread(self, target, *args, **kwargs):
        """Запустить функцию в фоновом потоке."""
        self.executor._executor.submit(target, *args, **kwargs)

    def create_button(self, text: str, callback, icon=None) -> MDRaisedButton:
        """Создать стилизованную кнопку."""
        btn = MDRaisedButton(
            text=text,
            md_bg_color=COLORS["neon_green"],
            text_color=COLORS["bg_dark"],
            font_size=dp(13),
            size_hint=(1, None),
            height=dp(48),
        )
        btn.bind(on_release=callback)
        return btn

    def create_section_title(self, text: str) -> MDLabel:
        """Создать заголовок секции."""
        return MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=COLORS["neon_blue"],
            font_style="H6",
            size_hint_y=None,
            height=dp(32),
        )

    def create_label(self, text: str, secondary=False) -> MDLabel:
        """Создать информационную метку."""
        return MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"] if secondary else COLORS["text_primary"],
            font_size=dp(12),
            size_hint_y=None,
            height=dp(24),
        )
