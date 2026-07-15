"""Модуль OSINT-разведки."""

import json
import re
import socket

import requests

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.core.platform import check_tool


class DnsHistory:
    """Проверка исторических IP-адресов домена."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, domain: str):
        """Запустить DNS History."""
        self.logger.info(f"[OSINT] DNS History для {domain}...")
        self.logger.warning(
            "[OSINT] Эмуляция запросов к SecurityTrails/ViewDNS. Для реальных данных требуется API-ключ."
        )

        # Текущий IP
        try:
            current_ip = socket.gethostbyname(domain)
            self.logger.info(f"[OSINT] Текущий IP: {current_ip}")
        except socket.gaierror:
            self.logger.warning(f"[OSINT] Не удалось разрешить домен: {domain}")

        # Попытка whois
        if check_tool("whois"):
            self.executor.run(["whois", domain], timeout=30)
        else:
            self.logger.info("[OSINT] whois не найден, используется демо-вывод.")

        # Демо-исторические данные (эмуляция)
        self.logger.info("[OSINT DEMO] Исторические IP (эмуляция):")
        self.logger.info("  - 203.0.113.10  (2022-01-15)")
        self.logger.info("  - 198.51.100.22 (2023-06-20)")
        self.logger.info("  - Проверьте Cloudflare-сертификат и DNS-записи на предмет утечки backend IP.")


class WaybackSearch:
    """Поиск архивных маршрутов через Wayback Machine."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, domain: str):
        """Запустить поиск архивных маршрутов."""
        self.logger.info(f"[OSINT] Поиск архивных маршрутов для {domain}...")

        url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=timestamp,original,statuscode,mimetype&collapse=urlkey&limit=50"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if len(data) <= 1:
                self.logger.info("[OSINT] Архивные записи не найдены.")
                return

            self.logger.success(f"[OSINT] Найдено записей: {len(data) - 1}")
            for row in data[1:20]:  # Показываем первые 20
                timestamp, original, statuscode, mimetype = row
                self.logger.info(f"  {timestamp} | {statuscode} | {original}")

        except requests.RequestException as exc:
            self.logger.error(f"[OSINT] Ошибка запроса к Wayback Machine: {exc}")
        except json.JSONDecodeError:
            self.logger.error("[OSINT] Некорректный ответ от Wayback Machine.")


class SubdomainEnum:
    """Сбор поддоменов."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, domain: str):
        """Запустить subfinder."""
        self.logger.info(f"[OSINT] Сбор поддоменов для {domain}...")

        if check_tool("subfinder"):
            self.executor.run(["subfinder", "-d", domain, "-silent"], timeout=120)
        else:
            self.logger.warning("[OSINT] subfinder не найден. Установите: sudo apt install subfinder")
            self.logger.info("[OSINT] Используется демо-режим с базовым DNS-перебором.")
            self._demo_enum(domain)

    def _demo_enum(self, domain: str):
        """Простой демо-перебор популярных поддоменов."""
        common = ["www", "mail", "ftp", "api", "dev", "staging", "admin", "panel", "cdn", "ns1", "ns2"]
        self.logger.info("[OSINT DEMO] Проверка распространённых поддоменов:")
        for sub in common:
            fqdn = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(fqdn)
                self.logger.info(f"  [FOUND] {fqdn} -> {ip}")
            except socket.gaierror:
                pass


_UA = {"User-Agent": "NeonRecon/0.5 (legal security research)"}

_REQUEST_TIMEOUT = 15


def _get_json(url: str, timeout: int = _REQUEST_TIMEOUT):
    """GET с JSON-ответом; исключения requests пробрасываются наверх."""
    response = requests.get(url, headers=_UA, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _locale() -> str:
    """Локаль для геокодера phonenumbers (zh и прочие -> en)."""
    from usosint.core.i18n import get_language
    lang = get_language()
    return lang if lang in ("ru", "en", "de", "es") else "en"


_DOH_ENDPOINTS = (
    # (url-шаблон, нужен ли Accept-заголовок dns-json)
    ("https://dns.google/resolve?name={name}&type={rtype}", False),
    ("https://8.8.8.8/resolve?name={name}&type={rtype}", False),
    ("https://cloudflare-dns.com/dns-query?name={name}&type={rtype}", True),
    ("https://1.1.1.1/dns-query?name={name}&type={rtype}", True),
)


def _doh_query(name: str, rtype: str, timeout: int = _REQUEST_TIMEOUT):
    """DNS-over-HTTPS запрос с перебором резолверов (dns.google, 8.8.8.8, CF, 1.1.1.1).

    Возвращает dict ответа или None, если все резолверы недоступны.
    """
    for template, needs_accept in _DOH_ENDPOINTS:
        headers = dict(_UA)
        if needs_accept:
            headers["Accept"] = "application/dns-json"
        try:
            resp = requests.get(
                template.format(name=name, rtype=rtype), headers=headers, timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, json.JSONDecodeError):
            continue
    return None


class CrtShEnum:
    """Пассивный сбор поддоменов через Certificate Transparency (crt.sh)."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, domain: str):
        """Запросить CT-логи и вывести уникальные имена сертификатов."""
        self.logger.info(f"[OSINT] crt.sh: сертификаты для *.{domain}...")
        try:
            data = _get_json(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=40)
        except requests.RequestException as exc:
            self.logger.error(f"[OSINT] Ошибка запроса crt.sh: {exc}")
            return
        except json.JSONDecodeError:
            self.logger.error("[OSINT] crt.sh вернул некорректный JSON.")
            return

        base = domain.lower()
        names = set()
        for entry in data:
            for name in str(entry.get("name_value", "")).splitlines():
                name = name.strip().lower()
                if name.startswith("*."):
                    name = name[2:]
                if name.endswith(base):
                    names.add(name)
        if not names:
            self.logger.info("[OSINT] Сертификаты не найдены.")
            return
        self.logger.success(f"[OSINT] Уникальных имён в CT-логах: {len(names)}")
        for name in sorted(names)[:40]:
            self.logger.info(f"  {name}")
        if len(names) > 40:
            self.logger.info(f"  ... и ещё {len(names) - 40}")


class DnsRecords:
    """DNS-записи домена через DNS-over-HTTPS (dns.google)."""

    TYPES = ("A", "AAAA", "MX", "NS", "TXT")

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, domain: str):
        """Запросить основные типы записей через DoH с резервными резолверами."""
        self.logger.info(f"[OSINT] DNS-записи для {domain} (DoH)...")
        for rtype in self.TYPES:
            data = _doh_query(domain, rtype)
            if data is None:
                self.logger.error(f"[OSINT] DoH: все резолверы недоступны ({rtype}).")
                continue
            answers = data.get("Answer") or []
            if not answers:
                continue
            self.logger.info(f"  [{rtype}]")
            for ans in answers[:10]:
                self.logger.info(f"    {ans.get('data')}")


class IpIntel:
    """Разведка по IP: гео, провайдер, ASN, флаги анонимизации."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, ip: str):
        """Запросить ipwho.is (бесплатный HTTPS API без ключа)."""
        self.logger.info(f"[OSINT] IP-разведка для {ip}...")
        try:
            data = _get_json(f"https://ipwho.is/{ip}")
        except requests.RequestException as exc:
            self.logger.error(f"[OSINT] Ошибка запроса ipwho.is: {exc}")
            return
        except json.JSONDecodeError:
            self.logger.error("[OSINT] ipwho.is вернул некорректный JSON.")
            return
        if not data.get("success", True):
            self.logger.error(f"[OSINT] ipwho.is: {data.get('message', 'ошибка запроса')}")
            return

        conn = data.get("connection") or {}
        tz = data.get("timezone") or {}
        rows = [
            ("IP", data.get("ip")),
            ("Тип", data.get("type")),
            ("Страна", f"{data.get('country')} ({data.get('country_code')})"),
            ("Регион / город", f"{data.get('region')} / {data.get('city')}"),
            ("Координаты", f"{data.get('latitude')}, {data.get('longitude')}"),
            ("Провайдер", conn.get("isp")),
            ("Организация", conn.get("org")),
            ("ASN", conn.get("asn")),
            ("Часовой пояс", tz.get("id")),
        ]
        for key, value in rows:
            if value not in (None, "", "None / None", "None (None)"):
                self.logger.info(f"  {key}: {value}")
        sec = data.get("security") or {}
        flags = [k for k in ("vpn", "proxy", "tor", "relay") if sec.get(k)]
        self.logger.info(f"  Флаги анонимизации: {', '.join(flags) if flags else 'нет'}")


class PhoneIntel:
    """Глубокий анализ номера: валидация, регион, оператор, тип линии, OSINT-ссылки."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, raw: str):
        """Разобрать номер через libphonenumber и выдать векторы поиска."""
        self.logger.info(f"[OSINT] Phone Intelligence для {raw}...")
        self.logger.warning(
            "[OSINT] Данные — из открытых источников. Персональные данные защищены "
            "законом: используйте правомерно и с согласия субъекта."
        )
        try:
            import phonenumbers
            from phonenumbers import (
                PhoneNumberFormat,
                PhoneNumberType,
                carrier,
                geocoder,
                timezone,
            )
        except ImportError:
            self.logger.error("[OSINT] Требуется пакет phonenumbers: pip install phonenumbers")
            return

        try:
            number = phonenumbers.parse(raw, None)
        except phonenumbers.NumberParseException as exc:
            self.logger.error(f"[OSINT] Не удалось разобрать номер: {exc}")
            return

        possible = phonenumbers.is_possible_number(number)
        valid = phonenumbers.is_valid_number(number)
        self.logger.info(
            f"  Возможный: {'да' if possible else 'нет'} | Валидный: {'да' if valid else 'нет'}"
        )
        if not possible:
            return

        e164 = phonenumbers.format_number(number, PhoneNumberFormat.E164)
        national = phonenumbers.format_number(number, PhoneNumberFormat.NATIONAL)
        self.logger.info(f"  E.164: {e164}")
        self.logger.info(
            f"  Международный: {phonenumbers.format_number(number, PhoneNumberFormat.INTERNATIONAL)}"
        )
        self.logger.info(f"  Национальный: {national}")
        self.logger.info(f"  Код страны: +{number.country_code}")
        self.logger.info(f"  Регион: {geocoder.description_for_number(number, _locale()) or '—'}")
        oper = carrier.name_for_number(number, _locale()) or carrier.name_for_number(number, "en")
        self.logger.info(f"  Оператор: {oper or '—'}")
        self.logger.info(f"  Часовой пояс: {', '.join(timezone.time_zones_for_number(number)) or '—'}")

        type_names = {
            PhoneNumberType.MOBILE: "мобильный",
            PhoneNumberType.FIXED_LINE: "городской",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "городской/мобильный",
            PhoneNumberType.TOLL_FREE: "бесплатный (toll-free)",
            PhoneNumberType.PREMIUM_RATE: "платный (premium)",
            PhoneNumberType.VOIP: "VoIP",
            PhoneNumberType.PERSONAL_NUMBER: "персональный",
            PhoneNumberType.PAGER: "пейджер",
            PhoneNumberType.VOICEMAIL: "голосовая почта",
        }
        ntype = phonenumbers.number_type(number)
        self.logger.info(f"  Тип линии: {type_names.get(ntype, 'неизвестен')}")

        digits = e164.lstrip("+")
        self.logger.info("[OSINT] Публичные проверки (откройте в браузере вручную):")
        self.logger.info(f"  WhatsApp: https://wa.me/{digits}")
        self.logger.info(f"  Telegram: https://t.me/+{digits}")
        self.logger.info(f"  Viber: viber://chat?number=%2B{digits}")
        self.logger.info("[OSINT] Поисковые дорки для ручной проверки:")
        self.logger.info(f'  "{e164}" OR "{national}"')
        self.logger.info(f'  site:vk.com OR site:ok.ru OR site:facebook.com "{digits}"')
        self.logger.info(f'  site:avito.ru OR site:youla.ru "{digits[-10:]}"')
        self.logger.info(
            "[OSINT] Утечки — только через легальные сервисы с согласия владельца номера: "
            "haveibeenpwned.com, leakcheck.io"
        )


class EmailIntel:
    """Проверка e-mail: валидация, MX, утечки через легальные публичные API."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, email: str):
        """Проверить адрес по открытым агрегаторам утечек."""
        self.logger.info(f"[OSINT] Email Intelligence для {email}...")
        self.logger.warning(
            "[OSINT] Проверяйте только свои адреса или с согласия владельца: "
            "сведения об утечках — персональные данные."
        )
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
            self.logger.error("[OSINT] Некорректный e-mail.")
            return

        # XposedOrNot — бесплатный открытый агрегатор утечек
        try:
            resp = requests.get(
                f"https://api.xposedornot.com/v1/check-email/{email}",
                headers=_UA,
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_breaches = data.get("breaches") or []
                breaches = raw_breaches[0] if raw_breaches and isinstance(raw_breaches[0], list) else raw_breaches
                if breaches:
                    self.logger.warning(
                        f"[УТЕЧКИ] Адрес найден в {len(breaches)} утечках (XposedOrNot):"
                    )
                    for name in breaches[:15]:
                        self.logger.warning(f"  - {name}")
                else:
                    self.logger.success("[OSINT] XposedOrNot: в утечках не найден.")
            elif resp.status_code == 404:
                self.logger.success("[OSINT] XposedOrNot: в известных утечках не найден.")
            elif resp.status_code == 429:
                self.logger.warning("[OSINT] XposedOrNot: лимит запросов, повторите позже.")
            else:
                self.logger.info(f"[OSINT] XposedOrNot: HTTP {resp.status_code}")
        except requests.RequestException as exc:
            self.logger.error(f"[OSINT] XposedOrNot недоступен: {exc}")

        # LeakCheck public API
        try:
            data = _get_json(f"https://leakcheck.io/api/public?check={email}", timeout=20)
            if data.get("success"):
                found = data.get("found", 0)
                if found:
                    self.logger.warning(f"[УТЕЧКИ] LeakCheck: записей найдено: {found}")
                    for src in (data.get("sources") or [])[:10]:
                        self.logger.warning(f"  - {src.get('name')} ({src.get('date')})")
                else:
                    self.logger.success("[OSINT] LeakCheck: чисто.")
        except (requests.RequestException, json.JSONDecodeError) as exc:
            self.logger.info(f"[OSINT] LeakCheck недоступен: {exc}")

        # MX-проверка домена почты
        domain = email.split("@", 1)[1]
        data = _doh_query(domain, "MX")
        if data is None:
            self.logger.info("[OSINT] MX-проверка недоступна (все DoH-резолверы).")
        else:
            answers = data.get("Answer") or []
            if answers:
                self.logger.info(f"[OSINT] MX-записи {domain}:")
                for ans in answers[:5]:
                    self.logger.info(f"  {ans.get('data')}")
            else:
                self.logger.warning(f"[OSINT] MX-записи {domain} не найдены.")


class UsernameIntel:
    """Поиск публичных профилей по никнейму на популярных площадках."""

    SITES = {
        "GitHub": "https://github.com/{}",
        "GitLab": "https://gitlab.com/{}",
        "Reddit": "https://www.reddit.com/user/{}",
        "Telegram": "https://t.me/{}",
        "Instagram": "https://www.instagram.com/{}/",
        "TikTok": "https://www.tiktok.com/@{}",
        "X (Twitter)": "https://x.com/{}",
        "YouTube": "https://www.youtube.com/@{}",
        "VK": "https://vk.com/{}",
        "Pinterest": "https://www.pinterest.com/{}/",
        "Steam": "https://steamcommunity.com/id/{}",
        "Twitch": "https://www.twitch.tv/{}",
        "Habr": "https://habr.com/ru/users/{}/",
        "SoundCloud": "https://soundcloud.com/{}",
        "Docker Hub": "https://hub.docker.com/u/{}",
        "PyPI": "https://pypi.org/user/{}/",
        "Medium": "https://medium.com/@{}",
        "DeviantArt": "https://www.deviantart.com/{}",
        "Flickr": "https://www.flickr.com/people/{}",
    }

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, username: str):
        """Проверить HTTP-статусы публичных страниц профилей."""
        self.logger.info(f"[OSINT] Username Search: {username}...")
        self.logger.warning(
            "[OSINT] Проверяются только публичные страницы (эквивалент обычного визита "
            "в браузере). Ложные срабатывания проверяйте вручную."
        )
        username = username.strip().lstrip("@")
        if not re.match(r"^[\w.\-]{2,40}$", username):
            self.logger.error("[OSINT] Некорректный никнейм.")
            return

        found = 0
        for site, pattern in self.SITES.items():
            url = pattern.format(username)
            try:
                resp = requests.get(url, headers=_UA, timeout=10, allow_redirects=True)
                if resp.status_code == 200:
                    found += 1
                    self.logger.success(f"  [FOUND] {site}: {url}")
                elif resp.status_code == 404:
                    pass
                elif resp.status_code == 429:
                    self.logger.warning(f"  [RATE] {site}: лимит запросов, пропущено")
                else:
                    self.logger.info(f"  [????] {site}: HTTP {resp.status_code} — проверьте: {url}")
            except requests.RequestException:
                self.logger.info(f"  [ERR ] {site}: нет соединения")
        self.logger.info(f"[OSINT] Готово: профилей найдено {found} из {len(self.SITES)}.")
