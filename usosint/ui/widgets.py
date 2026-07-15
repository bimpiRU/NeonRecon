"""Переиспользуемые UI-компоненты: карточки, чипы, кнопки навигации."""

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon, MDLabel

from usosint.ui.theme import COLORS


class NeonCard(MDCard):
    """Карточка секции с неоновой рамкой и заголовком."""

    def __init__(self, title: str = "", icon: str = "", **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", (dp(14), dp(10), dp(14), dp(14)))
        kwargs.setdefault("spacing", dp(8))
        kwargs.setdefault("size_hint", (1, None))
        kwargs.setdefault("md_bg_color", COLORS["bg_card"])
        kwargs.setdefault("line_color", COLORS["border"])
        kwargs.setdefault("line_width", 1.0)
        kwargs.setdefault("radius", [dp(8)])
        kwargs.setdefault("elevation", 0)
        super().__init__(**kwargs)
        self.bind(minimum_height=self.setter("height"))

        if title:
            header = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(26),
                spacing=dp(8),
            )
            if icon:
                header.add_widget(MDIcon(
                    icon=icon,
                    theme_text_color="Custom",
                    text_color=COLORS["neon_green"],
                    font_size=dp(18),
                    size_hint=(None, None),
                    size=(dp(24), dp(24)),
                    pos_hint={"center_y": 0.5},
                ))
            header.add_widget(MDLabel(
                text=title,
                theme_text_color="Custom",
                text_color=COLORS["neon_blue"],
                font_style="Subtitle1",
                bold=True,
            ))
            self.add_widget(header)


class StatusChip(MDBoxLayout):
    """Маленький цветной индикатор состояния (инструмент/статус)."""

    def __init__(self, text: str, ok: bool = True, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(26))
        kwargs.setdefault("padding", (dp(8), 0, dp(8), 0))
        kwargs.setdefault("spacing", dp(6))
        super().__init__(**kwargs)

        color = COLORS["neon_green"] if ok else COLORS["neon_red"]
        self.add_widget(MDIcon(
            icon="check-circle" if ok else "close-circle",
            theme_text_color="Custom",
            text_color=color,
            font_size=dp(14),
            size_hint=(None, None),
            size=(dp(16), dp(16)),
            pos_hint={"center_y": 0.5},
        ))
        lbl = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=COLORS["text_primary"] if ok else COLORS["text_secondary"],
            font_size=dp(12),
            size_hint_x=None,
        )
        lbl.bind(texture_size=lambda inst, size: setattr(inst, "width", size[0]))
        self.add_widget(lbl)
        self.bind(minimum_width=self.setter("width"))


class NavButton(MDBoxLayout):
    """Кнопка боковой навигации с иконкой и подсветкой активного состояния."""

    def __init__(self, icon: str, text: str, callback, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48))
        kwargs.setdefault("padding", (dp(14), 0, dp(8), 0))
        kwargs.setdefault("spacing", dp(10))
        super().__init__(**kwargs)
        self._callback = callback
        self._active = False

        self.icon_widget = MDIcon(
            icon=icon,
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            font_size=dp(20),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5},
        )
        self.label_widget = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            font_size=dp(14),
        )
        self.add_widget(self.icon_widget)
        self.add_widget(self.label_widget)

    def set_text(self, text: str):
        self.label_widget.text = text

    def set_active(self, active: bool):
        self._active = active
        color = COLORS["neon_green"] if active else COLORS["text_secondary"]
        self.icon_widget.text_color = color
        self.label_widget.text_color = color
        self.label_widget.bold = active
        self.md_bg_color = COLORS["bg_card"] if active else (0, 0, 0, 0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if callable(self._callback):
                self._callback()
            return True
        return super().on_touch_down(touch)
