"""Вкладка OSINT-разведки: домены, IP, телефоны, e-mail, никнеймы."""

from usosint.core.executor import CommandExecutor
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.modules.osint import (
    CrtShEnum,
    DnsHistory,
    DnsRecords,
    EmailIntel,
    IpIntel,
    PhoneIntel,
    SubdomainEnum,
    UsernameIntel,
    WaybackSearch,
)
from usosint.ui.base_tab import BaseTab, TabHeader


class OsintTab(BaseTab):
    """Вкладка OSINT-разведки."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor, **kwargs):
        super().__init__(logger, executor, **kwargs)
        self.tab_id = "osint"

        self.dns_history = DnsHistory(logger, executor)
        self.dns_records = DnsRecords(logger, executor)
        self.crtsh = CrtShEnum(logger, executor)
        self.wayback = WaybackSearch(logger, executor)
        self.subdomains = SubdomainEnum(logger, executor)
        self.ip_intel = IpIntel(logger, executor)
        self.phone_intel = PhoneIntel(logger, executor)
        self.email_intel = EmailIntel(logger, executor)
        self.username_intel = UsernameIntel(logger, executor)

        self.layout.add_widget(TabHeader("osint_title", "osint_warn"))

        # --- Доменная разведка (пассивная) ---
        passive_card = self.create_card(tr("passive"), icon="magnify-scan")
        passive_card.add_widget(self.create_label(tr("domain_label"), secondary=True))
        self.domain_input = self.create_input(tr("domain_hint"), tr("domain_label"))
        passive_card.add_widget(self.domain_input)
        passive_card.add_widget(self.create_button(
            tr("dns_btn"), self._on_dns_history, icon="dns"
        ))
        passive_card.add_widget(self.create_button(
            tr("dnsrec_btn"), self._on_dns_records, icon="format-list-bulleted"
        ))
        passive_card.add_widget(self.create_button(
            tr("crtsh_btn"), self._on_crtsh, icon="certificate-outline"
        ))
        passive_card.add_widget(self.create_button(
            tr("wayback_btn"), self._on_wayback, icon="history"
        ))

        # --- IP-разведка ---
        ip_card = self.create_card(tr("ip_intel_title"), icon="ip-network-outline")
        self.ip_input = self.create_input(tr("ip_hint"), tr("ip_helper"))
        ip_card.add_widget(self.ip_input)
        ip_card.add_widget(self.create_button(
            tr("ip_btn"), self._on_ip_intel, icon="earth"
        ))

        # --- Телефон ---
        phone_card = self.create_card(tr("phone_intel_title"), icon="phone-search-outline")
        self.phone_input = self.create_input(tr("phone_hint"), tr("phone_helper"))
        phone_card.add_widget(self.phone_input)
        phone_card.add_widget(self.create_button(
            tr("phone_intel_btn"), self._on_phone_intel, icon="phone-search"
        ))

        # --- E-mail ---
        email_card = self.create_card(tr("email_intel_title"), icon="email-search-outline")
        self.email_input = self.create_input(tr("email_hint"), tr("email_helper"))
        email_card.add_widget(self.email_input)
        email_card.add_widget(self.create_button(
            tr("email_btn"), self._on_email_intel, icon="email-alert-outline"
        ))

        # --- Никнейм ---
        user_card = self.create_card(tr("username_intel_title"), icon="account-search-outline")
        self.username_input = self.create_input(tr("username_hint"), tr("username_helper"))
        user_card.add_widget(self.username_input)
        user_card.add_widget(self.create_button(
            tr("username_btn"), self._on_username_intel, icon="account-search"
        ))

        # --- Активный OSINT ---
        active_card = self.create_card(tr("active"), icon="radar")
        active_card.add_widget(self.create_button(
            tr("subdomains_btn"), self._on_subdomains, icon="lan"
        ))

    # ---------- домены ----------

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

    def _on_dns_records(self, instance):
        domain = self._get_domain()
        if domain:
            self.log(f"{tr('launching')}: DNS Records {domain}...")
            self.run_in_thread(self.dns_records.run, domain, name="dns-records")

    def _on_crtsh(self, instance):
        domain = self._get_domain()
        if domain:
            self.log(f"{tr('launching')}: crt.sh {domain}...")
            self.run_in_thread(self.crtsh.run, domain, name="crtsh")

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

    # ---------- идентификаторы ----------

    def _on_ip_intel(self, instance):
        ip = self.ip_input.text.strip()
        if not ip:
            self.log(tr("enter_ip"), "WARN")
            return
        self.log(f"{tr('launching')}: IP Intel {ip}...")
        self.run_in_thread(self.ip_intel.run, ip, name="ip-intel")

    def _on_phone_intel(self, instance):
        phone = self.phone_input.text.strip()
        if not phone:
            self.log(tr("enter_phone"), "WARN")
            return
        self.log(f"{tr('launching')}: Phone Intel {phone}...")
        self.run_in_thread(self.phone_intel.run, phone, name="phone-intel")

    def _on_email_intel(self, instance):
        email = self.email_input.text.strip()
        if not email:
            self.log(tr("enter_email"), "WARN")
            return
        self.log(f"{tr('launching')}: Email Intel {email}...")
        self.run_in_thread(self.email_intel.run, email, name="email-intel")

    def _on_username_intel(self, instance):
        username = self.username_input.text.strip()
        if not username:
            self.log(tr("enter_username"), "WARN")
            return
        self.log(f"{tr('launching')}: Username Search {username}...")
        self.run_in_thread(self.username_intel.run, username, name="username-intel")
