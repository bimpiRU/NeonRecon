"""Вкладка OSINT-разведки."""

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.modules.osint import DnsHistory, PhoneLookup, SubdomainEnum, WaybackSearch
from usosint.ui.base_tab import BaseTab, TabHeader


class OsintTab(BaseTab):
    """Вкладка OSINT-разведки."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.tab_id = "osint"

        self.dns_history = DnsHistory(logger, executor)
        self.wayback = WaybackSearch(logger, executor)
        self.subdomains = SubdomainEnum(logger, executor)
        self.phone_lookup = PhoneLookup(logger, executor)

        self.layout.add_widget(TabHeader("osint_title", "osint_warn"))

        # --- Пассивный OSINT ---
        passive_card = self.create_card(tr("passive"), icon="magnify-scan")
        passive_card.add_widget(self.create_label(tr("domain_label"), secondary=True))
        self.domain_input = self.create_input(tr("domain_hint"), tr("domain_label"))
        passive_card.add_widget(self.domain_input)
        passive_card.add_widget(self.create_button(
            tr("dns_btn"), self._on_dns_history, icon="dns"
        ))
        passive_card.add_widget(self.create_button(
            tr("wayback_btn"), self._on_wayback, icon="history"
        ))

        # --- Активный OSINT ---
        active_card = self.create_card(tr("active"), icon="radar")
        active_card.add_widget(self.create_button(
            tr("subdomains_btn"), self._on_subdomains, icon="lan"
        ))

        # --- Анализ идентификаторов ---
        ids_card = self.create_card(tr("ids_title"), icon="card-account-details")
        ids_card.add_widget(self.create_label(tr("phone_label"), secondary=True))
        self.phone_input = self.create_input(tr("phone_hint"), tr("phone_helper"))
        ids_card.add_widget(self.phone_input)
        ids_card.add_widget(self.create_button(
            tr("phone_btn"), self._on_phone_lookup, icon="phone-search"
        ))

    def _get_domain(self) -> str:
        domain = self.domain_input.text.strip()
        if not domain:
            self.log(tr("enter_domain"), "WARN")
        return domain

    def _on_dns_history(self, instance):
        domain = self._get_domain()
        if domain:
            self.log(f"{tr('launching')}: DNS History {domain}...")
            self.run_in_thread(self.dns_history.run, domain, name="dns-history")

    def _on_wayback(self, instance):
        domain = self._get_domain()
        if domain:
            self.log(f"{tr('launching')}: Wayback {domain}...")
            self.run_in_thread(self.wayback.run, domain, name="wayback")

    def _on_subdomains(self, instance):
        domain = self._get_domain()
        if domain:
            self.log(f"{tr('launching')}: subfinder {domain}...")
            self.run_in_thread(self.subdomains.run, domain, name="subfinder")

    def _on_phone_lookup(self, instance):
        phone = self.phone_input.text.strip()
        if not phone:
            self.log(tr("enter_phone"), "WARN")
            return
        self.log(f"{tr('launching')}: Phone Lookup {phone}...")
        self.run_in_thread(self.phone_lookup.run, phone, name="phone-lookup")
