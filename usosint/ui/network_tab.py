"""Вкладка сетевого аудита."""

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.modules.network import MfpAudit, MitmAnalyzer, NetworkRecon
from usosint.ui.base_tab import BaseTab, TabHeader


class NetworkTab(BaseTab):
    """Вкладка сетевого аудита и проникновения."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.tab_id = "network"

        self.recon = NetworkRecon(logger, executor)
        self.mitm = MitmAnalyzer(logger, executor)
        self.mfp = MfpAudit(logger, executor)

        self.layout.add_widget(TabHeader("net_title", "net_warn"))

        card = self.create_card(tr("net_title"), icon="radar")
        card.add_widget(self.create_button(tr("recon_btn"), self._on_recon, icon="wifi-search"))
        card.add_widget(self.create_button(tr("mitm_btn"), self._on_mitm, icon="ear-hearing"))

        card.add_widget(self.create_label(tr("printer_label"), secondary=True))
        self.printer_input = self.create_input(tr("printer_hint"), tr("printer_helper"))
        card.add_widget(self.printer_input)
        card.add_widget(self.create_button(tr("pret_btn"), self._on_mfp, icon="printer-search"))

    def _on_recon(self, instance):
        self.log(f"{tr('launching')}: quiet recon...")
        self.run_in_thread(self.recon.run_quiet_recon, name="recon")

    def _on_mitm(self, instance):
        self.log(f"{tr('launching')}: MITM (15 min)...")
        self.run_in_thread(self.mitm.run, name="mitm")

    def _on_mfp(self, instance):
        target = self.printer_input.text.strip()
        self.log(f"{tr('launching')}: PRET {target or 'auto'}...")
        self.run_in_thread(self.mfp.run, target, name="pret")
