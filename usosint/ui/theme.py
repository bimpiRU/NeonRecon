"""Тема оформления приложения."""

from kivy.properties import ListProperty
from kivymd.theming import ThemableBehavior

# Основная палитра
COLORS = {
    "bg_dark": (0.031, 0.035, 0.043, 1),       # #08090B — фон приложения
    "bg_panel": (0.051, 0.059, 0.075, 1),      # #0D0F13 — панели/сайдбар
    "bg_card": (0.067, 0.078, 0.098, 1),       # #11141A — карточки
    "bg_input": (0.09, 0.102, 0.125, 1),       # #171A20 — поля ввода
    "neon_green": (0.0, 1.0, 0.615, 1),        # #00FF9D
    "neon_blue": (0.0, 0.722, 1.0, 1),         # #00B8FF
    "neon_red": (1.0, 0.25, 0.25, 1),          # #FF4040
    "neon_amber": (1.0, 0.72, 0.1, 1),         # #FFB81A
    "neon_purple": (0.69, 0.45, 1.0, 1),       # #B073FF
    "text_primary": (0.93, 0.95, 0.96, 1),
    "text_secondary": (0.55, 0.60, 0.64, 1),
    "border": (0.16, 0.19, 0.23, 1),
    "border_glow": (0.0, 1.0, 0.615, 0.35),
}

# Цвета уровней логов
LEVEL_COLORS = {
    "INFO": "text_primary",
    "OK": "neon_green",
    "WARN": "neon_amber",
    "ERROR": "neon_red",
}

# Палитра для KivyMD темы
THEME_PALETTE = {
    "primary_palette": "Teal",
    "primary_hue": "A400",
    "theme_style": "Dark",
    "accent_palette": "LightBlue",
}


def apply_theme(app):
    """Применить тёмную футуристическую тему к приложению."""
    app.theme_cls.primary_palette = THEME_PALETTE["primary_palette"]
    app.theme_cls.primary_hue = THEME_PALETTE["primary_hue"]
    app.theme_cls.theme_style = THEME_PALETTE["theme_style"]
    app.theme_cls.accent_palette = THEME_PALETTE["accent_palette"]


class NeonThemable(ThemableBehavior):
    """Миксин для виджетов с неоновой темой."""
    neon_green = ListProperty(COLORS["neon_green"])
    neon_blue = ListProperty(COLORS["neon_blue"])
    bg_card = ListProperty(COLORS["bg_card"])
