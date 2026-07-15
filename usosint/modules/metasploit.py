"""Интеграция Metasploit Framework."""

import re

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.core.platform import check_tool, is_android, sudo_prefix

# Допустимые типы модулей и символы в пути (защита от инъекций)
_MODULE_RE = re.compile(r"^(exploit|auxiliary|post|payload|encoder|nop)/[A-Za-z0-9_\-/]+$")
# Опции вида KEY=VALUE, KEY — только буквы/цифры/подчёркивание;
# VALUE — без пробелов, ';', кавычек и обратных кавычек (защита от инъекции команд msfconsole)
_OPTION_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)=([^\s;'\"`]+)$")


class MsfManager:
    """Управление msfconsole: проверка, сканирование, запуск модулей."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def _unavailable(self) -> bool:
        """Проверить доступность msfconsole, залогировать причину."""
        if is_android():
            self.logger.warning("[MSF] Metasploit недоступен на Android.")
            return True
        if not check_tool("msfconsole"):
            self.logger.error(
                "[MSF] msfconsole не найден. Установите: "
                "sudo apt install metasploit-framework"
            )
            return True
        return False

    def check(self):
        """Проверить установку Metasploit и вывести версию."""
        self.logger.info("[MSF] Проверка установки Metasploit...")
        if self._unavailable():
            return
        out = self.executor.run_simple(["msfconsole", "--version"], timeout=60)
        self.logger.success(f"[MSF] Установлен: {out.strip()}")

    def vuln_scan(self, target: str):
        """Сканирование цели через db_nmap внутри msfconsole."""
        self.logger.info(f"[MSF] Vuln scan цели: {target}")
        if self._unavailable():
            return
        if not re.match(r"^[A-Za-z0-9.\-:]+$", target):
            self.logger.error("[MSF] Некорректная цель.")
            return
        self.executor.run(
            sudo_prefix() + [
                "msfconsole", "-q", "-x",
                f"db_nmap -sV -T4 {target}; exit",
            ],
            timeout=900,
            name="msf-scan",
        )

    def run_module(self, module: str, target: str, options: str = ""):
        """Запустить модуль Metasploit с указанием RHOSTS и опций.

        Args:
            module: путь модуля, напр. auxiliary/scanner/portscan/tcp.
            target: значение RHOSTS.
            options: строка опций KEY=VALUE через пробел (напр. "LPORT=4444 THREADS=8").
        """
        self.logger.info(f"[MSF] Запуск модуля: {module} → {target}")
        if self._unavailable():
            return
        if not _MODULE_RE.match(module):
            self.logger.error(
                "[MSF] Некорректный модуль. Ожидается формат: "
                "exploit/... или auxiliary/... (без пробелов и спецсимволов)."
            )
            return
        if not re.match(r"^[A-Za-z0-9.\-:/,]+$", target):
            self.logger.error("[MSF] Некорректная цель.")
            return

        commands = [f"use {module}", f"set RHOSTS {target}"]
        for token in options.split():
            m = _OPTION_RE.match(token)
            if m:
                commands.append(f"set {m.group(1).upper()} {m.group(2)}")
            else:
                self.logger.warning(f"[MSF] Пропущена некорректная опция: {token}")
        commands += ["run", "exit"]

        script = "; ".join(commands)
        self.executor.run(
            sudo_prefix() + ["msfconsole", "-q", "-x", script],
            timeout=900,
            name="msf-module",
        )
