"""Автоматический комплексный аудит цели (домен или IPv4).

Одна кнопка: пассивная разведка (IP-интел, DNS, crt.sh, Wayback) +
активные проверки, если инструменты доступны (nmap top-100, subfinder).
Весь вывод дублируется в сжатый отчёт (ReportStore).
"""

import os
import re
import socket
from typing import List, Optional, Tuple

from usosint.core.executor import CommandExecutor
from usosint.core.logger import AppLogger
from usosint.core.report_store import ReportStore, format_size
from usosint.modules.osint import CrtShEnum, DnsRecords, IpIntel, WaybackSearch

_IP_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


class _TeeLogger:
    """Обёртка логгера: дублирует каждое сообщение в список для отчёта."""

    def __init__(self, logger: AppLogger, sink: List[str]):
        self._logger = logger
        self._sink = sink

    def _tee(self, level: str, method, msg: str):
        self._sink.append(f"[{level}] {msg}")
        method(msg)

    def info(self, msg: str):
        self._tee("INFO", self._logger.info, msg)

    def warning(self, msg: str):
        self._tee("WARN", self._logger.warning, msg)

    def error(self, msg: str):
        self._tee("ERROR", self._logger.error, msg)

    def success(self, msg: str):
        self._tee("OK", self._logger.success, msg)


class AutoAudit:
    """Полный автоматический аудит цели с сохранением отчёта."""

    def __init__(
        self,
        logger: AppLogger,
        executor: CommandExecutor,
        store: Optional[ReportStore] = None,
    ):
        self.logger = logger
        self.executor = executor
        self.store = store or ReportStore()

    @staticmethod
    def classify(target: str) -> Tuple[Optional[str], str]:
        """Определить тип цели: ('ip' | 'domain' | None, нормализованная цель)."""
        t = target.strip().lower()
        t = re.sub(r"^https?://", "", t)
        t = t.split("/")[0].split("?")[0].split(":")[0].strip()
        if _IP_RE.match(t):
            try:
                if all(0 <= int(part) <= 255 for part in t.split(".")):
                    return "ip", t
            except ValueError:
                pass
            return None, t
        if _DOMAIN_RE.match(t):
            return "domain", t
        return None, t

    def run(self, target: str):
        """Выполнить полный аудит цели."""
        lines: List[str] = []
        tee = _TeeLogger(self.logger, lines)

        kind, t = self.classify(target)
        tee.info(f"[АВТОАУДИТ] Цель: {target}")
        if kind is None:
            tee.error(
                "[АВТОАУДИТ] Некорректная цель. Введите домен (example.com) "
                "или IPv4-адрес (1.2.3.4)."
            )
            return
        tee.warning(
            "[АВТОАУДИТ] Пассивные проверки не контактируют с целью. Активные "
            "(nmap/subfinder) — только в авторизованных сетях."
        )

        # --- IP-разведка ---
        ip = t if kind == "ip" else None
        if kind == "domain":
            tee.info(f"[ФАЗА 1] Разрешение домена {t}...")
            try:
                ip = socket.gethostbyname(t)
                tee.success(f"  {t} -> {ip}")
            except socket.gaierror:
                tee.error(f"  Домен {t} не разрешается; IP-фаза пропущена.")
        if ip:
            tee.info(f"[ФАЗА 2] IP-разведка {ip} (гео, провайдер, ASN, флаги)...")
            IpIntel(tee, self.executor).run(ip)

        # --- Доменные пассивные проверки ---
        if kind == "domain":
            tee.info("[ФАЗА 3] DNS-записи (DoH с резервными резолверами)...")
            DnsRecords(tee, self.executor).run(t)
            tee.info("[ФАЗА 4] Пассивные поддомены через Certificate Transparency...")
            CrtShEnum(tee, self.executor).run(t)
            tee.info("[ФАЗА 5] Архивные маршруты (Wayback Machine)...")
            WaybackSearch(tee, self.executor).run(t)

        # --- Активные проверки (только при наличии инструментов) ---
        scan_target = t if kind == "domain" else ip
        if self.executor.check_tool("nmap") and scan_target:
            tee.info(f"[ФАЗА 6] nmap top-100 портов (-T2, вежливый режим) по {scan_target}...")
            out = self.executor.run_simple(
                ["nmap", "-T2", "--top-ports", "100", scan_target], timeout=240
            )
            for line in out.splitlines()[:60]:
                tee.info(f"  {line}")
        else:
            tee.info("[ФАЗА 6] nmap недоступен на этом устройстве — фаза пропущена.")

        if kind == "domain" and self.executor.check_tool("subfinder"):
            tee.info(f"[ФАЗА 7] subfinder по {t}...")
            out = self.executor.run_simple(["subfinder", "-d", t, "-silent"], timeout=180)
            subs = [line.strip() for line in out.splitlines() if line.strip()][:40]
            tee.success(f"  Найдено поддоменов: {len(subs)}")
            for line in subs:
                tee.info(f"  {line}")
        elif kind == "domain":
            tee.info("[ФАЗА 7] subfinder недоступен — фаза пропущена.")

        # --- Сводка и сохранение ---
        blob = "\n".join(lines)
        ips = sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", blob)))
        tee.info(
            "[СВОДКА] Уникальных IP в результатах: "
            + (", ".join(ips[:15]) if ips else "не найдено")
        )
        try:
            report_id = self.store.save("autoaudit", t, f"Автоаудит {t}", lines)
            size = format_size(os.path.getsize(os.path.join(self.store.dir, report_id)))
            tee.success(f"[АВТОАУДИТ] Готово. Отчёт в архиве: {report_id} ({size}, gzip).")
        except Exception as exc:
            tee.error(f"[АВТОАУДИТ] Не удалось сохранить отчёт: {exc}")
