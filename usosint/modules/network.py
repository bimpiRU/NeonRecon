"""Модуль сетевого аудита."""

import re
import subprocess

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.core.platform import check_tool, is_android, is_linux, is_root


class NetworkRecon:
    """Тихий сетевой recon."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def _detect_subnet(self) -> str:
        """Автоопределение локальной подсети."""
        output = self.executor.run_simple(["ip", "-4", "route", "show", "default"])
        match = re.search(r"src (\d+\.\d+\.\d+)\.\d+", output)
        if match:
            return f"{match.group(1)}.0/24"
        return "192.168.1.0/24"

    def run_quiet_recon(self):
        """Запустить скрытое nmap-сканирование."""
        self.logger.info("[NET] Запуск тихого Recon сети...")

        if is_android():
            self.logger.warning("[NET] Nmap недоступен на Android без root.")
            return

        if not check_tool("nmap"):
            self.logger.error("[NET] Nmap не найден. Установите: sudo apt install nmap")
            return

        subnet = self._detect_subnet()
        self.logger.info(f"[NET] Целевая подсеть: {subnet}")

        if is_root():
            cmd = ["nmap", "-sS", "-T2", "-Pn", subnet]
        else:
            self.logger.warning("[NET] Нет root — используется TCP-connect сканирование (-sT).")
            cmd = ["nmap", "-sT", "-T2", "-Pn", subnet]

        self.executor.run(cmd, timeout=300)


class MitmAnalyzer:
    """Пассивный MITM-анализ открытого трафика."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def run(self):
        """Запустить пассивный анализ на 15 минут."""
        self.logger.info("[NET] Запуск пассивного MITM-анализа (15 минут)...")

        if is_android():
            self.logger.warning("[NET] MITM-анализ недоступен на Android без root.")
            return

        if not is_root():
            self.logger.error("[NET] Требуются root-права для перехвата трафика.")
            return

        iface = self._detect_interface()
        self.logger.info(f"[NET] Интерфейс: {iface}")

        if check_tool("bettercap"):
            cmd = [
                "bettercap",
                "-iface", iface,
                "-eval",
                "set net.sniff.verbose true; "
                "set net.sniff.local true; "
                "net.sniff on; "
                "sleep 900; "
                "quit",
            ]
            self.executor.run(cmd, timeout=960)
        elif check_tool("tcpdump"):
            cmd = [
                "tcpdump",
                "-i", iface,
                "-A",
                "-s", "0",
                "tcp port 23 or tcp port 80",
                "-w", "/tmp/mitm_capture.pcap",
                "-G", "900",
                "-W", "1",
            ]
            self.executor.run(cmd, timeout=960)
        else:
            self.logger.error("[NET] Не найдены bettercap или tcpdump.")

    def _detect_interface(self) -> str:
        output = self.executor.run_simple(["ip", "-o", "-4", "route", "show", "to", "default"])
        if output and "dev" in output:
            parts = output.split()
            try:
                return parts[parts.index("dev") + 1]
            except (ValueError, IndexError):
                pass
        return "eth0"


class MfpAudit:
    """Аудит МФУ через PRET."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def _find_printers(self) -> list:
        """Обнаружить принтеры в локальной сети."""
        self.logger.info("[PRET] Поиск принтеров в локальной сети...")
        output = self.executor.run_simple(
            ["nmap", "-p", "9100", "--open", "-oG", "-", "192.168.1.0/24"],
            timeout=120,
        )
        printers = []
        for line in output.splitlines():
            if "9100/open" in line:
                match = re.search(r"Host: (\d+\.\d+\.\d+\.\d+)", line)
                if match:
                    printers.append(match.group(1))
        return printers

    def run(self, target: str = ""):
        """Запустить аудит МФУ."""
        self.logger.info("[PRET] Запуск аудита МФУ...")

        if is_android():
            self.logger.warning("[PRET] PRET недоступен на Android без root.")
            return

        if not check_tool("pret") and not check_tool("pret.py"):
            self.logger.warning(
                "[PRET] PRET не найден. Установите: git clone https://github.com/RUB-NDS/PRET.git"
            )
            self.logger.info("[PRET] Работа в демо-режиме: выполняется только обнаружение принтеров.")

        targets = [target] if target else self._find_printers()
        if not targets:
            self.logger.warning("[PRET] Принтеры не обнаружены.")
            return

        for printer in targets:
            self.logger.info(f"[PRET] Анализ принтера: {printer}")
            if check_tool("pret"):
                cmd = ["pret", printer, "ps", "--safe"]
                self.executor.run(cmd, timeout=120)
            elif check_tool("pret.py"):
                cmd = ["python", "pret.py", printer, "ps", "--safe"]
                self.executor.run(cmd, timeout=120)
            else:
                # Демо-режим: просто проверяем порт 9100
                self.logger.info(f"[PRET DEMO] Проверка порта 9100 на {printer}...")
                result = self.executor.run_simple(
                    ["nmap", "-p", "9100", "--open", printer],
                    timeout=30,
                )
                self.logger.info(result)
