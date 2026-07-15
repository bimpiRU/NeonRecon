"""Вкладка сетевого аудита."""

from kivy.metrics import dp
from kivymd.uix.textfield import MDTextField

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.modules.network import MfpAudit, MitmAnalyzer, NetworkRecon
from usosint.ui.base_tab import BaseTab


class NetworkTab(BaseTab):
    """Вкладка сетевого аудита и проникновения."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.title = "Сетевой аудит"

        self.recon = NetworkRecon(logger, executor)
        self.mitm = MitmAnalyzer(logger, executor)
        self.mfp = MfpAudit(logger, executor)

        self.layout.add_widget(self.create_section_title("Сетевой аудит и проникновение"))
        self.layout.add_widget(
            self.create_label(
                "⚠️ MITM и сканирование разрешены только в авторизованных сетях.",
                secondary=True,
            )
        )

        self.layout.add_widget(self.create_button("Тихий Recon сети", self._on_recon))
        self.layout.add_widget(self.create_button("Пассивный MITM-анализ", self._on_mitm))

        # PRET target input
        self.layout.add_widget(self.create_label("Целевой принтер (IP):", secondary=True))
        self.printer_input = MDTextField(
            hint_text="192.168.1.10",
            helper_text="Оставьте пустым для автообнаружения",
            helper_text_mode="persistent",
            size_hint_y=None,
            height=dp(48),
        )
        self.layout.add_widget(self.printer_input)
        self.layout.add_widget(self.create_button("Аудит МФУ (PRET)", self._on_mfp))

    def _on_recon(self, instance):
        self.log("Запуск тихого recon сети...")
        self.run_in_thread(self.recon.run_quiet_recon)

    def _on_mitm(self, instance):
        self.log("Запуск пассивного MITM-анализа на 15 минут...")
        self.run_in_thread(self.mitm.run)

    def _on_mfp(self, instance):
        target = self.printer_input.text.strip()
        self.log(f"Запуск аудита МФУ: {target or 'автообнаружение'}...")
        self.run_in_thread(self.mfp.run, target)
