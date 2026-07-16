"""Модуль операционной безопасности."""

import os
import random
import subprocess

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.core.platform import check_tool, is_android, is_linux, is_root, sudo_prefix


class StealthMasking:
    """Смена hostname и MAC-адреса."""

    # OUI вендоров Apple и HP
    OUI_LIST = [
        "F0:18:98",  # Apple
        "AC:87:A3",  # Apple
        "3C:15:C2",  # Apple
        "00:1E:C9",  # HP
        "00:21:5A",  # HP
        "00:23:7D",  # HP
    ]

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def _random_mac(self) -> str:
        """Сгенерировать случайный MAC с OUI вендора Apple/HP."""
        oui = random.choice(self.OUI_LIST)
        tail = ":".join(f"{random.randint(0x00, 0xFF):02X}" for _ in range(3))
        return f"{oui}:{tail}"

    def _random_hostname(self) -> str:
        """Сгенерировать случайный hostname в офисном стиле."""
        vendors = ["DESKTOP", "WORKSTATION", "LAPTOP", "PC"]
        number = random.randint(1000, 9999)
        return f"{random.choice(vendors)}-{number}"

    def run(self):
        """Запустить stealth-маскировку."""
        self.logger.info("[OPSEC] Запуск stealth-маскировки...")

        if is_android():
            self.logger.warning("[OPSEC] Смена hostname/MAC недоступна на Android без root.")
            return

        if not is_linux():
            self.logger.warning("[OPSEC] Автоматическая смена hostname/MAC поддерживается только на Linux.")
            return

        if not is_root() and not sudo_prefix():
            self.logger.error(
                "[OPSEC] Нужен root или sudo: перезапустите приложение через sudo "
                "или нажмите «Запросить root»."
            )
            return

        prefix = sudo_prefix()
        new_hostname = self._random_hostname()
        new_mac = self._random_mac()
        iface = self._detect_interface()

        self.logger.info(f"[OPSEC] Новый hostname: {new_hostname}")
        self.logger.info(f"[OPSEC] Новый MAC: {new_mac}")
        self.logger.info(f"[OPSEC] Интерфейс: {iface}")

        # Смена hostname
        self.executor.run_simple(prefix + ["hostnamectl", "set-hostname", new_hostname])

        # Смена MAC
        if check_tool("ip"):
            self.executor.run_simple(prefix + ["ip", "link", "set", "dev", iface, "down"])
            self.executor.run_simple(prefix + ["ip", "link", "set", "dev", iface, "address", new_mac])
            self.executor.run_simple(prefix + ["ip", "link", "set", "dev", iface, "up"])
        elif check_tool("macchanger"):
            self.executor.run_simple(prefix + ["macchanger", "-m", new_mac, iface])
        else:
            self.logger.warning("[OPSEC] Не найдены утилиты ip/macchanger для смены MAC.")

        self.logger.success("[OPSEC] Stealth-маскировка завершена.")

    def _detect_interface(self) -> str:
        """Автоопределение активного сетевого интерфейса."""
        output = self.executor.run_simple(["ip", "-o", "-4", "route", "show", "to", "default"])
        if output and "dev" in output:
            parts = output.split()
            try:
                return parts[parts.index("dev") + 1]
            except (ValueError, IndexError):
                pass
        return "eth0"


class TorManager:
    """Управление Tor-туннелированием."""

    def __init__(self, logger: AppLogger, executor: CommandExecutor):
        self.logger = logger
        self.executor = executor

    def _systemd_available(self) -> bool:
        """Проверить, что systemd реально работает (в WSL/контейнерах — нет)."""
        import os
        return check_tool("systemctl") and os.path.isdir("/run/systemd/system")

    def _start_tor_direct(self) -> bool:
        """Запустить tor напрямую как демон (без systemd), от имени пользователя."""
        from usosint.core import storage
        base = storage.data_dir()
        if not base:
            self.logger.error("[OPSEC] Нет записываемой директории для данных tor.")
            return False
        data_dir = os.path.join(base, "tor-data")
        os.makedirs(data_dir, exist_ok=True)
        self.logger.info("[OPSEC] systemd недоступен — запуск tor напрямую...")
        self.executor.run_simple([
            "tor", "--RunAsDaemon", "1",
            "--DataDirectory", data_dir,
            "--SocksPort", "9050",
        ])
        # дать tor поднять цепочки
        import time
        time.sleep(6)
        probe = self.executor.run_simple(
            ["curl", "-s", "--max-time", "15", "--socks5-hostname", "127.0.0.1:9050",
             "https://api.ipify.org"],
            timeout=25,
        )
        return bool(probe) and "[ERROR]" not in probe and "." in probe

    def start(self):
        """Запустить Tor и проверить proxychains."""
        self.logger.info("[OPSEC] Включение Tor-туннелирования...")

        if is_android():
            self.logger.warning("[OPSEC] Tor недоступен на Android без root.")
            return

        if not check_tool("tor"):
            self.logger.error("[OPSEC] Утилита tor не найдена. Установите: sudo apt install tor")
            return

        # Запуск Tor: systemd, иначе напрямую
        if self._systemd_available():
            self.executor.run_simple(["systemctl", "start", "tor"])
            self.executor.run_simple(["systemctl", "enable", "tor"])
        else:
            self._start_tor_direct()

        # Проверка через proxychains
        if check_tool("proxychains4") and check_tool("curl"):
            self.logger.info("[OPSEC] Проверка цепочки proxychains4...")
            output = self.executor.run_simple(
                ["proxychains4", "curl", "-s", "--max-time", "20",
                 "https://check.torproject.org/api/ip"],
                timeout=40,
            )
            if output and "[ERROR]" not in output and "timeout" not in output:
                self.logger.success(f"[OPSEC] Tor активен. Внешний IP: {output}")
            else:
                self.logger.warning(f"[OPSEC] Не удалось проверить IP: {output}")
        else:
            self.logger.warning("[OPSEC] proxychains4 или curl не найдены.")

    def stop(self):
        """Остановить Tor."""
        self.logger.info("[OPSEC] Отключение Tor-туннелирования...")
        if self._systemd_available():
            self.executor.run_simple(["systemctl", "stop", "tor"])
            self.executor.run_simple(["systemctl", "disable", "tor"])
        else:
            self.executor.run_simple(["pkill", "-x", "tor"])
        self.logger.success("[OPSEC] Tor остановлен.")
