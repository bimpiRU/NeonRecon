#!/usr/bin/env python3
"""Точка входа Universal Security & OSINT Assistant."""

import os
import sys

# Добавляем корень проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usosint.app import USOSINTApp


def main():
    app = USOSINTApp()
    app.run()


if __name__ == "__main__":
    main()
