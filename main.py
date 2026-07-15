#!/usr/bin/env python3
"""Точка входа NeonRecon (Universal Security & OSINT Assistant)."""

import os
import sys
import traceback

# Добавляем корень проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CRASH_LOG = os.path.join(os.path.expanduser("~"), "neonrecon_crash.log")


def _excepthook(exc_type, exc_value, exc_tb):
    """Глобальный перехватчик необработанных исключений: пишет crash-лог."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    try:
        with open(CRASH_LOG, "a", encoding="utf-8") as fh:
            fh.write("=" * 60 + "\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=fh)
    except Exception:
        pass
    traceback.print_exception(exc_type, exc_value, exc_tb)


def main():
    sys.excepthook = _excepthook
    from usosint.app import USOSINTApp
    app = USOSINTApp()
    app.run()


if __name__ == "__main__":
    main()
