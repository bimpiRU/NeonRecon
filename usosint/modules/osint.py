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


class PhoneLookup:
    """Анализ номеров телефонов."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self, phone: str):
        """Запустить phone lookup."""
        self.logger.info(f"[OSINT] Phone Lookup для {phone}...")
        self.logger.warning(
            "[OSINT] Используйте полученные данные только в правомерных целях и в соответствии с законом."
        )

        # Валидация номера
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 10:
            self.logger.error("[OSINT] Некорректный номер телефона.")
            return

        # Эвристика оператора и региона по коду (демо)
        self.logger.info("[OSINT DEMO] Анализ номера:")
        if digits.startswith("79"):
            self.logger.info("  - Страна: Россия")
            if digits[2:4] in ["11", "12", "15", "16", "17"]:
                self.logger.info("  - Регион: Москва / Московская область")
            elif digits[2:4] in ["21", "22", "24"]:
                self.logger.info("  - Регион: Санкт-Петербург / Ленинградская область")
            else:
                self.logger.info("  - Регион: другой регион РФ")
            self.logger.info("  - Возможные операторы: МТС, Билайн, Мегафон, Tele2")
        elif digits.startswith("1") and len(digits) == 11:
            self.logger.info("  - Страна: США / Канада")
        else:
            self.logger.info("  - Страна: не определена")

        # Демо-поиск по открытым источникам
        self.logger.info("[OSINT DEMO] Поиск по открытым источникам:")
        self.logger.info("  - Проверка социальных сетей и мессенджеров требует API и соблюдения их условий.")
        self.logger.info("  - Проверка утечек баз данных возможна через легальные сервисы (например, HaveIBeenPwned).")
        self.logger.info("  - Для полноценного lookup используйте официальные API и получайте согласие субъекта.")
