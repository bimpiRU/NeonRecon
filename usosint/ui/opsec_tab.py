"""Вкладка OPSEC."""

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.modules.opsec import StealthMasking, TorManager
from usosint.ui.base_tab import BaseTab
from usosint.ui.theme import COLORS


class OpsecTab(BaseTab):
    """Вкладка операционной безопасности."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.title = "OPSEC"

        self.stealth = StealthMasking(logger, executor)
        self.tor_manager = TorManager(logger, executor)

        self.layout.add_widget(self.create_section_title("Операционная безопасность"))
        self.layout.add_widget(
            self.create_label(
                "⚠️ Используйте только на собственных системах или с разрешения владельца.",
                secondary=True,
            )
        )

        # Stealth-маскировка
        stealth_btn = self.create_button("Stealth-маскировка", self._on_stealth)
        self.layout.add_widget(stealth_btn)

        # Tor toggle
        tor_box = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56))
        tor_label = MDLabel(
            text="Tor-туннелирование",
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            size_hint_x=0.7,
        )
        from kivymd.uix.selectioncontrol import MDSwitch

        self.tor_switch = MDSwitch(
            active=False,
            size_hint_x=0.3,
        )
        self.tor_switch.bind(active=self._on_tor_toggle)
        tor_box.add_widget(tor_label)
        tor_box.add_widget(self.tor_switch)
        self.layout.add_widget(tor_box)

        self.status_label = self.create_label("Статус: готово", secondary=True)
        self.layout.add_widget(self.status_label)

    def _on_stealth(self, instance):
        self.log("Запуск stealth-маскировки...")
        self.run_in_thread(self.stealth.run)

    def _on_tor_toggle(self, instance, value):
        if value:
            self.log("Включение Tor-туннелирования...")
            self.run_in_thread(self.tor_manager.start)
        else:
            self.log("Отключение Tor-туннелирования...")
            self.run_in_thread(self.tor_manager.stop)
