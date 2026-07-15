"""Выполнение внешних команд в фоновых потоках."""

import shlex
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional

from usosint.core.logger import AppLogger


class CommandExecutor:
    """Запускает внешние команды в пуле потоков и перенаправляет вывод в логгер."""

    def __init__(self, logger: AppLogger, max_workers: int = 4):
        self.logger = logger
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = {}
        self._lock = threading.Lock()

    def check_tool(self, name: str) -> bool:
        """Проверить наличие утилиты в PATH."""
        return shutil.which(name) is not None

    def run(
        self,
        cmd: List[str],
        timeout: Optional[int] = None,
        shell: bool = False,
        realtime: bool = True,
        callback: Optional[Callable[[int], None]] = None,
    ):
        """Запустить команду в фоновом потоке.

        Args:
            cmd: список аргументов команды.
            timeout: таймаут в секундах.
            shell: выполнить через shell.
            realtime: выводить stdout/stderr в логгер в реальном времени.
            callback: функция, вызываемая по завершении с кодом возврата.
        """
        future = self._executor.submit(
            self._execute, cmd, timeout, shell, realtime, callback
        )
        return future

    def _execute(
        self,
        cmd: List[str],
        timeout: Optional[int],
        shell: bool,
        realtime: bool,
        callback: Optional[Callable[[int], None]],
    ):
        cmd_str = " ".join(shlex.quote(str(arg)) for arg in cmd)
        self.logger.info(f"[EXEC] {cmd_str}")

        try:
            if shell:
                process = subprocess.Popen(
                    cmd_str,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    text=True,
                    bufsize=1,
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

            with self._lock:
                self._running[id(process)] = process

            if realtime:
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        self.logger.info(line)

            try:
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.logger.warning("Команда превысила таймаут, завершаем принудительно...")
                process.kill()
                return_code = -1

            with self._lock:
                self._running.pop(id(process), None)

            if return_code == 0:
                self.logger.success(f"[DONE] {cmd_str}")
            elif return_code == -1:
                self.logger.error(f"[TIMEOUT] {cmd_str}")
            else:
                self.logger.error(f"[ERROR] {cmd_str} (code {return_code})")

            if callback:
                callback(return_code)

        except FileNotFoundError:
            self.logger.error(f"[NOT FOUND] Утилита не найдена: {cmd[0]}")
            if callback:
                callback(-127)
        except Exception as exc:
            self.logger.error(f"[EXCEPTION] {exc}")
            if callback:
                callback(-1)

    def run_simple(
        self,
        cmd: List[str],
        timeout: Optional[int] = 30,
        shell: bool = False,
    ) -> str:
        """Синхронно выполнить команду и вернуть stdout как строку.

        Используется для быстрых запросов из фоновых потоков.
        """
        cmd_str = " ".join(shlex.quote(str(arg)) for arg in cmd)
        self.logger.info(f"[EXEC-SYNC] {cmd_str}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=shell,
            )
            output = result.stdout.strip()
            if result.returncode != 0 and result.stderr:
                output += f"\n[STDERR] {result.stderr.strip()}"
            return output
        except FileNotFoundError:
            return f"[ERROR] Утилита не найдена: {cmd[0]}"
        except subprocess.TimeoutExpired:
            return "[ERROR] Превышен таймаут выполнения"
        except Exception as exc:
            return f"[ERROR] {exc}"

    def shutdown(self, wait: bool = True):
        """Остановить пул потоков."""
        self._executor.shutdown(wait=wait)
