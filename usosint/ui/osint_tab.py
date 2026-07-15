"""Вкладка OSINT-разведки."""

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.modules.osint import DnsHistory, PhoneLookup, SubdomainEnum, WaybackSearch
from usosint.ui.base_tab import BaseTab


class OsintTab(BaseTab):
    """Вкладка OSINT-разведки."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.title = "OSINT"

        self.dns_history = DnsHistory(logger, executor)
        self.wayback = WaybackSearch(logger, executor)
        self.subdomains = SubdomainEnum(logger, executor)
        self.phone_lookup = PhoneLookup(logger, executor)

        self.layout.add_widget(self.create_section_title("OSINT-разведка"))
        self.layout.add_widget(
            self.create_label(
                "⚠️ Соблюдайте законы о защите персональных данных.",
                secondary=True,
            )
        )

        # --- Пассивный OSINT ---
        self.layout.add_widget(self.create_section_title("Пассивный OSINT"))

        self.layout.add_widget(self.create_label("Домен:", secondary=True))
        self.domain_input = MDTextField(
            hint_text="example.com",
            helper_text="Целевой домен",
            helper_text_mode="persistent",
            size_hint_y=None,
            height=dp(48),
        )
        self.layout.add_widget(self.domain_input)

        dns_btn = self.create_button("DNS History", self._on_dns_history)
        self.layout.add_widget(dns_btn)

        wayback_btn = self.create_button("Архивные маршруты (Wayback)", self._on_wayback)
        self.layout.add_widget(wayback_btn)

        # --- Активный OSINT ---
        self.layout.add_widget(self.create_section_title("Активный OSINT"))
        subfinder_btn = self.create_button("Сбор поддоменов", self._on_subdomains)
        self.layout.add_widget(subfinder_btn)

        # --- Анализ идентификаторов ---
        self.layout.add_widget(self.create_section_title("Анализ идентификаторов"))
        self.layout.add_widget(self.create_label("Номер телефона:", secondary=True))
        self.phone_input = MDTextField(
            hint_text="+79991234567",
            helper_text="Формат: +79123456789",
            helper_text_mode="persistent",
            size_hint_y=None,
            height=dp(48),
        )
        self.layout.add_widget(self.phone_input)
        phone_btn = self.create_button("Phone Lookup", self._on_phone_lookup)
        self.layout.add_widget(phone_btn)

    def _on_dns_history(self, instance):
        domain = self.domain_input.text.strip()
        if not domain:
            self.log("Введите домен для DNS History", "WARN")
            return
        self.log(f"Запрос DNS History для {domain}...")
        self.run_in_thread(self.dns_history.run, domain)

    def _on_wayback(self, instance):
        domain = self.domain_input.text.strip()
        if not domain:
            self.log("Введите домен для Wayback", "WARN")
            return
        self.log(f"Поиск архивных маршрутов для {domain}...")
        self.run_in_thread(self.wayback.run, domain)

    def _on_subdomains(self, instance):
        domain = self.domain_input.text.strip()
        if not domain:
            self.log("Введите домен для сбора поддоменов", "WARN")
            return
        self.log(f"Запуск subfinder для {domain}...")
        self.run_in_thread(self.subdomains.run, domain)

    def _on_phone_lookup(self, instance):
        phone = self.phone_input.text.strip()
        if not phone:
            self.log("Введите номер телефона", "WARN")
            return
        self.log(f"Phone Lookup для {phone}...")
        self.run_in_thread(self.phone_lookup.run, phone)
