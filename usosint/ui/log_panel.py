"""Интерактивная панель логов с цветовой индикацией уровней и фильтрами."""

import re

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDIcon, MDLabel

from usosint.core.clipboard import copy_to_clipboard
from usosint.core.i18n import tr
from usosint.core.logger import AppLogger
from usosint.ui.theme import COLORS, LEVEL_COLORS

MAX_LINES = 400
_LINE_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s+\[(?P<level>[A-Z]+)\]\s?(?P<msg>.*)$")


def _hex(color_key: str) -> str:
    r, g, b, _ = COLORS[color_key]
    return f"{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"


class LogPanel(MDBoxLayout):
    """Панель логов: шапка с фильтрами + прокручиваемые цветные строки."""

    def __init__(self, logger: AppLogger, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", 0)
        super().__init__(**kwargs)
        self.logger = logger
        self._filter = "ALL"
        self._entries = []  # (level, line)
        self._chips = {}

        self._build_header()
        self._build_scroll()

        Clock.schedule_interval(self._poll_logs, 0.15)

    # ---------- построение ----------

    def _build_header(self):
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(34),
            padding=(dp(8), 0, dp(4), 0),
            spacing=dp(4),
            md_bg_color=COLORS["bg_panel"],
        )
        header.add_widget(MDIcon(
            icon="console-line",
            theme_text_color="Custom",
            text_color=COLORS["neon_green"],
            font_size=dp(16),
            size_hint_x=None,
            width=dp(22),
        ))
        self.title_label = MDLabel(
            text=tr("log_hint"),
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            font_size=dp(11),
            size_hint_x=None,
            width=dp(120),
        )
        header.add_widget(self.title_label)
        # распорка, чтобы кнопки фильтров не сжимали заголовок
        header.add_widget(MDBoxLayout(size_hint_x=1))

        for level in ("ALL", "OK", "INFO", "WARN", "ERROR"):
            btn = MDFlatButton(
                text=tr("filter_all") if level == "ALL" else level,
                theme_text_color="Custom",
                text_color=COLORS["bg_dark"] if level == "ALL" else COLORS["text_secondary"],
                md_bg_color=COLORS["neon_green"] if level == "ALL" else COLORS["bg_card"],
                font_size=dp(10),
                size_hint=(None, None),
                size=(dp(52), dp(24)),
                pos_hint={"center_y": 0.5},
            )
            btn.bind(on_release=lambda inst, lv=level: self._set_filter(lv))
            self._chips[level] = btn
            header.add_widget(btn)

        clear_btn = MDIconButton(
            icon="delete-sweep",
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            size_hint=(None, None),
            size=(dp(30), dp(30)),
        )
        clear_btn.bind(on_release=lambda *_: self.clear())
        copy_btn = MDIconButton(
            icon="content-copy",
            theme_text_color="Custom",
            text_color=COLORS["text_secondary"],
            size_hint=(None, None),
            size=(dp(30), dp(30)),
        )
        copy_btn.bind(on_release=lambda *_: self._copy())
        header.add_widget(clear_btn)
        header.add_widget(copy_btn)
        self.add_widget(header)

    def _build_scroll(self):
        self.scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(6),
            bar_color=COLORS["neon_green"],
            bar_inactive_color=COLORS["border"],
        )
        self.lines_layout = MDGridLayout(
            cols=1,
            size_hint_y=None,
            spacing=0,
            padding=(dp(10), dp(4), dp(6), dp(4)),
        )
        self.lines_layout.bind(minimum_height=self.lines_layout.setter("height"))
        self.scroll.add_widget(self.lines_layout)
        self.add_widget(self.scroll)

    # ---------- фильтрация ----------

    def _set_filter(self, level: str):
        self._filter = level
        for lv, chip in self._chips.items():
            active = lv == level
            chip.md_bg_color = COLORS["neon_green"] if active else COLORS["bg_card"]
            chip.text_color = COLORS["bg_dark"] if active else COLORS["text_secondary"]
        self._rerender()

    def _make_line_widget(self, level: str, line: str) -> MDLabel:
        color_key = LEVEL_COLORS.get(level, "text_primary")
        safe = line.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")
        lbl = MDLabel(
            text=f"[color={_hex(color_key)}]{safe}[/color]",
            markup=True,
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            font_size=dp(11),
            size_hint_y=None,
        )
        lbl.bind(texture_size=lambda inst, size: setattr(inst, "height", max(size[1], dp(16))))
        return lbl

    def _rerender(self):
        self.lines_layout.clear_widgets()
        shown = 0
        for level, line in self._entries:
            if self._filter != "ALL" and level != self._filter:
                continue
            self.lines_layout.add_widget(self._make_line_widget(level, line))
            shown += 1
        if shown:
            Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.05)

    # ---------- поток логов ----------

    def _poll_logs(self, dt):
        q = self.logger.get_queue()
        new_lines = []
        while not q.empty():
            try:
                new_lines.append(q.get_nowait())
            except Exception:
                break
        if not new_lines:
            return

        added = False
        for line in new_lines:
            m = _LINE_RE.match(line)
            level = m.group("level") if m else "INFO"
            self._entries.append((level, line))
            if self._filter in ("ALL", level):
                self.lines_layout.add_widget(self._make_line_widget(level, line))
                added = True

        # обрезка истории
        while len(self._entries) > MAX_LINES:
            self._entries.pop(0)
        while len(self.lines_layout.children) > MAX_LINES:
            self.lines_layout.remove_widget(self.lines_layout.children[-1])

        if added:
            Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.05)

    def clear(self):
        """Очистить панель логов."""
        self._entries.clear()
        self.lines_layout.clear_widgets()
        self.logger.clear()
        self.logger.info(tr("log_cleared"))

    def _copy(self):
        text = "\n".join(line for _, line in self._entries)
        if copy_to_clipboard(text):
            self.logger.info(tr("copied"))
