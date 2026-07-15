#!/usr/bin/env python3
"""Точка входа NeonRecon (Universal Security & OSINT Assistant)."""

import os
import sys
import traceback

# Добавляем корень проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CRASH_LOG = os.path.join(os.path.expanduser("~"), "neonrecon_crash.log")


def _write_crash(text: str):
    """Записать текст ошибки в crash-лог (лучшее усилие, без исключений)."""
    for path in (CRASH_LOG, os.path.join("/sdcard", "neonrecon_crash.log")):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("=" * 60 + "\n")
                fh.write(text + "\n")
        except Exception:
            pass


def _excepthook(exc_type, exc_value, exc_tb):
    """Глобальный перехватчик необработанных исключений: пишет crash-лог."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    _write_crash(text)
    traceback.print_exception(exc_type, exc_value, exc_tb)


def _run_fallback(error_text: str):
    """Минимальный экран ошибки без KivyMD: показывает traceback на устройстве.

    Если основной интерфейс падает при старте (например, из-за окружения),
    пользователь увидит причину вместо молчаливого закрытия приложения.
    """
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView

    class CrashApp(App):
        def build(self):
            self.title = "NeonRecon — Startup Error"
            root = BoxLayout(orientation="vertical", padding=20, spacing=10)
            root.add_widget(Label(
                text="NeonRecon: ошибка запуска / startup error",
                size_hint_y=None, height=40, bold=True,
            ))
            scroll = ScrollView()
            lbl = Label(
                text=error_text,
                size_hint_y=None,
                halign="left",
                valign="top",
                font_size=12,
            )
            lbl.bind(texture_size=lambda inst, size: setattr(inst, "height", size[1]))
            lbl.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
            scroll.add_widget(lbl)
            root.add_widget(scroll)
            return root

    CrashApp().run()


def main():
    sys.excepthook = _excepthook
    try:
        from usosint.app import USOSINTApp
        app = USOSINTApp()
        app.run()
    except Exception:
        text = traceback.format_exc()
        _write_crash(text)
        traceback.print_exc()
        try:
            _run_fallback(text)
        except Exception:
            pass


if __name__ == "__main__":
    main()
