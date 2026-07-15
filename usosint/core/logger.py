"""Потокобезопасный логгер на основе очереди."""

import queue
import threading
from datetime import datetime


class AppLogger:
    """Централизованный логгер, безопасный для использования из нескольких потоков."""

    def __init__(self):
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._history = []

    def log(self, message: str, level: str = "INFO"):
        """Добавить сообщение в лог."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}"
        with self._lock:
            self._history.append(line)
        self._queue.put(line)

    def info(self, message: str):
        self.log(message, "INFO")

    def warning(self, message: str):
        self.log(message, "WARN")

    def error(self, message: str):
        self.log(message, "ERROR")

    def success(self, message: str):
        self.log(message, "OK")

    def get_queue(self) -> queue.Queue:
        """Вернуть очередь для чтения UI-потоком."""
        return self._queue

    def get_history(self) -> list:
        """Вернуть копию истории логов."""
        with self._lock:
            return list(self._history)

    def clear(self):
        """Очистить историю и очередь."""
        with self._lock:
            self._history.clear()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
