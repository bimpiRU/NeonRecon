"""Кроссплатформенное копирование в буфер обмена."""


def copy_to_clipboard(text: str) -> bool:
    """Скопировать текст в системный буфер. Возвращает True при успехе."""
    # 1. Kivy Clipboard (работает на desktop и android)
    try:
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(text)
        return True
    except Exception:
        pass
    # 2. tkinter fallback
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        pass
    return False
