"""Вкладка сетевого аудита."""

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.modules.metasploit import MsfManager
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
        self.msf = MsfManager(logger, executor)

        self.layout.add_widget(TabHeader("net_title", "net_warn"))

        card = self.create_card(tr("net_title"), icon="radar")
        card.add_widget(self.create_button(tr("recon_btn"), self._on_recon, icon="wifi-search"))
        card.add_widget(self.create_button(tr("mitm_btn"), self._on_mitm, icon="ear-hearing"))

        card.add_widget(self.create_label(tr("printer_label"), secondary=True))
        self.printer_input = self.create_input(tr("printer_hint"), tr("printer_helper"))
        card.add_widget(self.printer_input)
        card.add_widget(self.create_button(tr("pret_btn"), self._on_mfp, icon="printer-search"))

        # --- Metasploit ---
        msf_card = self.create_card(tr("msf_title"), icon="bug")
        msf_card.add_widget(self.create_warn_label(tr("msf_warn")))
        msf_card.add_widget(self.create_button(
            tr("msf_check_btn"), self._on_msf_check, icon="shield-check"
        ))
        msf_card.add_widget(self.create_label(tr("msf_target_label"), secondary=True))
        self.msf_target_input = self.create_input(tr("msf_target_hint"), tr("msf_target_label"))
        msf_card.add_widget(self.msf_target_input)
        msf_card.add_widget(self.create_button(
            tr("msf_scan_btn"), self._on_msf_scan, icon="target"
        ))
        msf_card.add_widget(self.create_label(tr("msf_module_label"), secondary=True))
        self.msf_module_input = self.create_input(tr("msf_module_hint"), tr("msf_extra_label"))
        msf_card.add_widget(self.msf_module_input)
        self.msf_extra_input = self.create_input(tr("msf_extra_label"), tr("msf_extra_label"))
        msf_card.add_widget(self.msf_extra_input)
        msf_card.add_widget(self.create_button(
            tr("msf_run_btn"), self._on_msf_run, icon="rocket-launch"
        ))

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

    def _get_msf_target(self) -> str:
        target = self.msf_target_input.text.strip()
        if not target:
            self.log(tr("msf_target_label"), "WARN")
        return target

    def _on_msf_check(self, instance):
        self.log(f"{tr('launching')}: msf check...")
        self.run_in_thread(self.msf.check, name="msf-check")

    def _on_msf_scan(self, instance):
        target = self._get_msf_target()
        if target:
            self.log(f"{tr('launching')}: MSF scan {target}...")
            self.run_in_thread(self.msf.vuln_scan, target, name="msf-scan")

    def _on_msf_run(self, instance):
        target = self._get_msf_target()
        module = self.msf_module_input.text.strip()
        extra = self.msf_extra_input.text.strip()
        if not module:
            self.log(tr("msf_module_label"), "WARN")
            return
        if target:
            self.log(f"{tr('launching')}: MSF {module} → {target}...")
            self.run_in_thread(self.msf.run_module, module, target, extra, name="msf-run")
