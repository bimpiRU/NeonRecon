"""Вкладка OPSEC."""

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDSwitch

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.modules.opsec import StealthMasking, TorManager
from usosint.ui.base_tab import BaseTab, TabHeader
from usosint.ui.theme import COLORS


class OpsecTab(BaseTab):
    """Вкладка операционной безопасности."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.tab_id = "opsec"

        self.stealth = StealthMasking(logger, executor)
        self.tor_manager = TorManager(logger, executor)

        self.layout.add_widget(TabHeader("opsec_title", "opsec_warn"))

        card = self.create_card(tr("opsec_title"), icon="shield-lock")
        card.add_widget(self.create_button(
            tr("root_btn"), self._on_request_root, icon="account-key"
        ))
        card.add_widget(self.create_button(
            tr("stealth_btn"), self._on_stealth, icon="incognito"
        ))

        tor_box = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58))
        tor_label = MDLabel(
            text=tr("tor_toggle"),
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            font_size=dp(15),
            size_hint_x=0.75,
        )
        self.tor_switch = MDSwitch(active=False, size_hint_x=0.25)
        self.tor_switch.bind(active=self._on_tor_toggle)
        tor_box.add_widget(tor_label)
        tor_box.add_widget(self.tor_switch)
        card.add_widget(tor_box)

    def _on_stealth(self, instance):
        self.log(f"{tr('launching')}: stealth...")
        self.run_in_thread(self.stealth.run, name="stealth")

    def _on_request_root(self, instance):
        self.log(f"{tr('launching')}: sudo -v...")
        self.run_in_thread(self._request_root, name="root-request")

    def _request_root(self):
        """Проверить/запросить root-доступ через sudo -n (без интерактива)."""
        from usosint.core.platform import has_sudo, is_android, is_root
        if is_root():
            self.logger.success(tr("root_granted"))
            return
        if is_android():
            out = self.executor.run_simple(["su", "-c", "id"], timeout=10)
            if "uid=0" in out:
                self.logger.success(tr("root_granted"))
            else:
                self.logger.warning(tr("root_denied"))
            return
        if not has_sudo():
            self.logger.warning(tr("root_denied"))
            return
        out = self.executor.run_simple(["sudo", "-n", "true"], timeout=15)
        if "[ERROR]" not in out:
            self.logger.success(tr("root_granted"))
        else:
            self.logger.warning(tr("root_denied"))

    def _on_tor_toggle(self, instance, value):
        if value:
            self.log(f"{tr('launching')}: Tor ON")
            self.run_in_thread(self.tor_manager.start, name="tor-start")
        else:
            self.log(f"{tr('launching')}: Tor OFF")
            self.run_in_thread(self.tor_manager.stop, name="tor-stop")
