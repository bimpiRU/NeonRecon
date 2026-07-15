"""Выполнение внешних команд и python-задач в фоновых потоках.

Все задачи регистрируются в реестре: их видно в статус-баре и можно
остановить (включая дочерние процессы) через cancel/cancel_all.
"""

import os
import shlex
import shutil
import signal
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from usosint.core.logger import AppLogger

DEFAULT_TIMEOUT = 300  # секунд, защита от «вечных» процессов


class TaskInfo:
    """Информация о зарегистрированной задаче."""

    def __init__(self, task_id: int, name: str):
        self.id = task_id
        self.name = name
        self.started = time.time()
        self.process: Optional[subprocess.Popen] = None
        self.status = "running"  # running | done | error | cancelled


class CommandExecutor:
    """Запускает команды/функции в пуле потоков с учётом и отменой задач."""

    def __init__(self, logger: AppLogger, max_workers: int = 4):
        self.logger = logger
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._tasks: Dict[int, TaskInfo] = {}
        self._next_id = 1
        self._listeners: List[Callable[[], None]] = []

    # ---------- реестр задач ----------

    def add_listener(self, callback: Callable[[], None]):
        """Подписаться на изменение числа активных задач (вызывается из потоков!)."""
        self._listeners.append(callback)

    def _notify(self):
        for callback in list(self._listeners):
            try:
                callback()
            except Exception:
                pass

    def _register(self, name: str) -> TaskInfo:
        with self._lock:
            info = TaskInfo(self._next_id, name)
            self._next_id += 1
            self._tasks[info.id] = info
        self._notify()
        return info

    def _finish(self, info: TaskInfo, status: str):
        with self._lock:
            info.status = status
            self._tasks.pop(info.id, None)
        self._notify()

    def running_count(self) -> int:
        with self._lock:
            return len(self._tasks)

    def running_names(self) -> List[str]:
        with self._lock:
            return [t.name for t in self._tasks.values()]

    def cancel_all(self):
        """Принудительно остановить все процессы (с дочерними)."""
        with self._lock:
            tasks = list(self._tasks.values())
        for info in tasks:
            if info.process is not None:
                self._kill_process_tree(info.process)
                info.status = "cancelled"

    # ---------- запуск python-функций ----------

    def submit(self, fn: Callable, *args, name: Optional[str] = None, **kwargs):
        """Запустить python-функцию в фоновом потоке с регистрацией."""
        task_name = name or getattr(fn, "__name__", "task")
        info = self._register(task_name)

        def _wrapper():
            try:
                fn(*args, **kwargs)
                self._finish(info, "done")
            except Exception as exc:
                self.logger.error(f"[EXCEPTION] {task_name}: {exc}")
                self._finish(info, "error")

        return self._executor.submit(_wrapper)

    # ---------- запуск внешних команд ----------

    def check_tool(self, name: str) -> bool:
        """Проверить наличие утилиты в PATH."""
        return shutil.which(name) is not None

    @staticmethod
    def _popen_kwargs() -> dict:
        """Платформенные параметры для изоляции группы процессов."""
        # preexec_fn опасен в многопоточных приложениях и нестабилен на Android
        if os.name == "posix" and "ANDROID_STORAGE" not in os.environ:
            return {"preexec_fn": os.setsid}
        if os.name == "nt":
            return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
        return {}

    @staticmethod
    def _kill_process_tree(process: subprocess.Popen):
        """Убить процесс и всё его дерево."""
        try:
            if os.name == "posix" and "ANDROID_STORAGE" not in os.environ:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            elif os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                )
            else:
                # Android: без setsid группа совпадает с группой приложения —
                # killpg убил бы и само приложение, убиваем только процесс.
                process.kill()
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def run(
        self,
        cmd: List[str],
        timeout: Optional[int] = None,
        shell: bool = False,
        realtime: bool = True,
        callback: Optional[Callable[[int], None]] = None,
        name: Optional[str] = None,
    ):
        """Запустить команду в фоновом потоке.

        Args:
            cmd: список аргументов команды.
            timeout: таймаут в секундах (None → DEFAULT_TIMEOUT).
            shell: выполнить через shell.
            realtime: выводить stdout/stderr в логгер в реальном времени.
            callback: функция, вызываемая по завершении с кодом возврата.
            name: имя задачи для реестра/статус-бара.
        """
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        task_name = name or (cmd[0] if cmd else "cmd")
        info = self._register(task_name)
        return self._executor.submit(
            self._execute, cmd, timeout, shell, realtime, callback, info
        )

    def _execute(
        self,
        cmd: List[str],
        timeout: Optional[int],
        shell: bool,
        realtime: bool,
        callback: Optional[Callable[[int], None]],
        info: TaskInfo,
    ):
        cmd_str = " ".join(shlex.quote(str(arg)) for arg in cmd)
        self.logger.info(f"[EXEC] {cmd_str}")

        try:
            popen_args = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                errors="replace",
            )
            popen_args.update(self._popen_kwargs())
            if shell:
                process = subprocess.Popen(cmd_str, shell=True, **popen_args)
            else:
                process = subprocess.Popen(cmd, **popen_args)

            info.process = process

            if realtime and process.stdout is not None:
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        self.logger.info(line)

            try:
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.logger.warning("Команда превысила таймаут, завершаем принудительно...")
                self._kill_process_tree(process)
                return_code = -1

            status = "done"
            if info.status == "cancelled":
                self.logger.warning(f"[CANCELLED] {cmd_str}")
                status = "cancelled"
            elif return_code == 0:
                self.logger.success(f"[DONE] {cmd_str}")
            elif return_code == -1:
                self.logger.error(f"[TIMEOUT] {cmd_str}")
                status = "error"
            else:
                self.logger.error(f"[ERROR] {cmd_str} (code {return_code})")
                status = "error"

            self._finish(info, status)
            if callback:
                callback(return_code)

        except FileNotFoundError:
            self.logger.error(f"[NOT FOUND] Утилита не найдена: {cmd[0]}")
            self._finish(info, "error")
            if callback:
                callback(-127)
        except Exception as exc:
            self.logger.error(f"[EXCEPTION] {exc}")
            self._finish(info, "error")
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
                errors="replace",
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
        """Остановить все задачи и пул потоков."""
        self.cancel_all()
        self._executor.shutdown(wait=wait)
