"""Интерактивная панель логов."""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField

from usosint.core.logger import AppLogger
from usosint.ui.theme import COLORS


class LogPanel(ScrollView):
    """Прокручиваемая панель для вывода логов."""

    text_input = ObjectProperty(None)

    def __init__(self, logger: AppLogger, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger
        self.bar_width = dp(8)
        self.bar_color = COLORS["neon_green"]
        self.bar_inactive_color = COLORS["border"]
        self.effect_cls = "ScrollEffect"
        self.do_scroll_x = False
        self.do_scroll_y = True

        self.text_input = MDTextField(
            multiline=True,
            readonly=True,
            size_hint_y=None,
            height=self.height,
            background_color=COLORS["bg_card"],
            foreground_color=COLORS["text_primary"],
            hint_text="Логи операций будут отображаться здесь...",
            helper_text_mode="persistent",
            font_size=dp(13),
            line_color_normal=COLORS["border"],
        )
        self.text_input.bind(minimum_height=self.text_input.setter("height"))
        self.add_widget(self.text_input)

        # Периодическое обновление из очереди логгера
        Clock.schedule_interval(self._poll_logs, 0.1)

    def _poll_logs(self, dt):
        """Забирать сообщения из очереди и отображать их."""
        q = self.logger.get_queue()
        updated = False
        while not q.empty():
            try:
                line = q.get_nowait()
                self.text_input.text += line + "\n"
                updated = True
            except Exception:
                break
        if updated:
            self.text_input.height = max(self.text_input.minimum_height, self.height)
            self.scroll_y = 0  # Автопрокрутка вниз

    def clear(self):
        """Очистить панель логов."""
        self.text_input.text = ""
        self.logger.clear()
