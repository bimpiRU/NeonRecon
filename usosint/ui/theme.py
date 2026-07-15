"""Тема оформления приложения."""

from kivy.metrics import dp
from kivy.properties import ListProperty
from kivymd.theming import ThemableBehavior

# Основная палитра
COLORS = {
    "bg_dark": (0.039, 0.039, 0.039, 1),       # #0A0A0A
    "bg_card": (0.071, 0.071, 0.071, 1),       # #121212
    "bg_input": (0.106, 0.106, 0.106, 1),      # #1B1B1B
    "neon_green": (0.0, 1.0, 0.615, 1),        # #00FF9D
    "neon_blue": (0.0, 0.722, 1.0, 1),         # #00B8FF
    "neon_red": (1.0, 0.2, 0.2, 1),            # #FF3333
    "text_primary": (0.95, 0.95, 0.95, 1),
    "text_secondary": (0.6, 0.6, 0.6, 1),
    "border": (0.2, 0.2, 0.2, 1),
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
