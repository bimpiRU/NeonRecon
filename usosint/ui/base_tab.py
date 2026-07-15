"""Базовый класс вкладки: прокручиваемый контейнер с карточками."""

from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.ui.theme import COLORS
from usosint.ui.widgets import NeonCard


class BaseTab(ScrollView):
    """Прокручиваемая вкладка с набором карточек-секций."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger
        self.executor = executor
        self.do_scroll_x = False
        self.bar_width = dp(6)
        self.bar_color = COLORS["neon_green"]
        self.bar_inactive_color = COLORS["border"]

        self.layout = MDGridLayout(
            cols=1,
            spacing=dp(12),
            padding=(dp(14), dp(14), dp(14), dp(14)),
            size_hint_y=None,
        )
        self.layout.bind(minimum_height=self.layout.setter("height"))
        self.add_widget(self.layout)

    # ---------- утилиты ----------

    def log(self, message: str, level: str = "INFO"):
        """Записать сообщение в лог."""
        self.logger.log(message, level)

    def run_in_thread(self, target, *args, name=None, **kwargs):
        """Запустить функцию в фоновом потоке (регистрируется в реестре задач)."""
        self.executor.submit(target, *args, name=name, **kwargs)

    # ---------- фабрики виджетов ----------

    def create_card(self, title: str = "", icon: str = "") -> NeonCard:
        """Создать карточку и добавить на вкладку."""
        card = NeonCard(title=title, icon=icon)
        self.layout.add_widget(card)
        return card

    def create_button(self, text: str, callback, icon: str = "") -> MDRaisedButton:
        """Создать стилизованную кнопку."""
        btn = MDRaisedButton(
            text=text,
            icon=icon,
            md_bg_color=COLORS["neon_green"],
            text_color=COLORS["bg_dark"],
            font_size=dp(13),
            size_hint=(1, None),
            height=dp(44),
            elevation=0,
        )
        btn.bind(on_release=callback)
        return btn

    def create_section_title(self, text: str) -> MDLabel:
        """Создать заголовок секции внутри карточки."""
        return MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=COLORS["neon_blue"],
            font_style="Subtitle2",
            bold=True,
            size_hint_y=None,
            height=dp(26),
        )

    def create_label(self, text: str, secondary=False) -> MDLabel:
        """Создать информационную метку."""
        return MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"] if secondary else COLORS["text_primary"],
            font_size=dp(12),
            size_hint_y=None,
            height=dp(22),
        )

    def create_warn_label(self, text: str) -> MDLabel:
        """Метка-предупреждение (янтарная)."""
        return MDLabel(
            text="⚠ " + text,
            theme_text_color="Custom",
            text_color=COLORS["neon_amber"],
            font_size=dp(12),
            size_hint_y=None,
            height=dp(22),
        )

    def create_input(self, hint: str, helper: str = "") -> MDTextField:
        """Стилизованное поле ввода."""
        field = MDTextField(
            hint_text=hint,
            helper_text=helper,
            helper_text_mode="persistent",
            size_hint_y=None,
            height=dp(48),
            font_size=dp(14),
        )
        return field


class TabHeader(MDBoxLayout):
    """Шапка вкладки: заголовок + строка предупреждения."""

    def __init__(self, title_key: str, warn_key: str, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("spacing", dp(4))
        super().__init__(**kwargs)
        self.add_widget(MDLabel(
            text=tr(title_key),
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            font_style="H6",
            bold=True,
            size_hint_y=None,
            height=dp(30),
        ))
        warn = MDLabel(
            text="⚠ " + tr(warn_key),
            theme_text_color="Custom",
            text_color=COLORS["neon_amber"],
            font_size=dp(12),
            size_hint_y=None,
            height=dp(22),
        )
        self.add_widget(warn)
        self.height = dp(56)
