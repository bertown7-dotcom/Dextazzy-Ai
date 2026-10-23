import threading
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.utils import get_color_from_hex, platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

if platform == "android":
    from jnius import autoclass

API_KEY = "ВСТАВЬ_НОВЫЙ_API_КЛЮЧ"
MODEL = "gemini-2.5-flash"

API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent"
)

SYSTEM_PROMPT = (
    "Ты Dextazzy AI, дружелюбный и шутливый матершинник "
    "ИИ-помощник. Отвечай быстро, коротко и по делу."
)

BG = "#101116"
PANEL = "#1B1C23"
INPUT_BG = "#252630"
BLUE = "#648CFF"
WHITE = "#F4F5F9"
MUTED = "#A0A3B2"

Window.clearcolor = get_color_from_hex(BG)

if platform == "android":
    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        WindowManager = autoclass("android.view.WindowManager$LayoutParams")
        PythonActivity.mActivity.getWindow().setSoftInputMode(
            WindowManager.SOFT_INPUT_ADJUST_RESIZE
        )
    except Exception as e:
        print("Keyboard setup:", e)

try:
    Window.softinput_mode = "resize"
except Exception:
    pass


def draw_rounded(widget, color, radius=18):
    with widget.canvas.before:
        Color(*get_color_from_hex(color))
        shape = RoundedRectangle(
            pos=widget.pos, size=widget.size, radius=[dp(radius)]
        )

    def update(*args):
        shape.pos = widget.pos
        shape.size = widget.size

    widget.bind(pos=update, size=update)
    return shape


class DextazzyAI(App):
    def build(self):
        self.history = []
        self.busy = False

        self.root_box = BoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(10), dp(12), dp(8)],
            spacing=dp(8)
        )

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(60),
            padding=[dp(4), dp(2)]
        )

        title = Label(
            text="[b]Dextazzy AI[/b]",
            markup=True,
            color=get_color_from_hex(WHITE),
            font_size="23sp",
            halign="left",
            valign="middle",
            size_hint_y=0.65
        )
        title.bind(size=lambda w, s: setattr(w, "text_size", s))
        header.add_widget(title)

        subtitle = Label(
            text="Ваш ИИ-помощник",
            color=get_color_from_hex(MUTED),
            font_size="12sp",
            halign="left",
            valign="middle",
            size_hint_y=0.35
        )
        subtitle.bind(size=lambda w, s: setattr(w, "text_size", s))
        header.add_widget(subtitle)
        self.root_box.add_widget(header)

        self.scroll = ScrollView(
            do_scroll_x=False,
            bar_width=0,
            scroll_type=["content"],
            size_hint=(1, 1)
        )

        self.chat = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(12),
            padding=[dp(2), dp(8), dp(2), dp(12)]
        )
        self.chat.bind(minimum_height=self.chat.setter("height"))
        self.scroll.add_widget(self.chat)
        self.root_box.add_widget(self.scroll)

        self.status = Label(
            text="Готов к работе",
            size_hint_y=None,
            height=dp(20),
            color=get_color_from_hex(MUTED),
            font_size="12sp",
            halign="left",
            valign="middle"
        )
        self.status.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.root_box.add_widget(self.status)

        self.bottom = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            spacing=dp(9),
            padding=[dp(1), dp(2), dp(1), dp(2)]
        )

        self.input = TextInput(
            hint_text="Напишите сообщение...",
            multiline=False,
            font_size="16sp",
            padding=[dp(13), dp(15), dp(10), dp(10)],
            foreground_color=get_color_from_hex(WHITE),
            hint_text_color=get_color_from_hex(MUTED),
            cursor_color=get_color_from_hex(WHITE),
            selection_color=(0.25, 0.42, 0.85, 0.7),
            background_normal="",
            background_active="",
            background_color=get_color_from_hex(INPUT_BG),
            write_tab=False,
            size_hint_x=1
        )
        self.bottom.add_widget(self.input)

        self.send_button = Button(
            text="",
            size_hint=(None, 1),
            width=dp(56),
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            border=(0, 0, 0, 0)
        )

        with self.send_button.canvas.before:
            Color(*get_color_from_hex(BLUE))
            self.button_bg = RoundedRectangle(
                pos=self.send_button.pos,
                size=self.send_button.size,
                radius=[dp(17)]
            )

        with self.send_button.canvas.after:
            Color(1, 1, 1, 1)
            self.arrow_line = Line(points=[0, 0, 0, 0], width=dp(2.5))
            self.arrow_left = Line(points=[0, 0, 0, 0], width=dp(2.5))
            self.arrow_right = Line(points=[0, 0, 0, 0], width=dp(2.5))

        def update_send_button(*args):
            x, y = self.send_button.pos
            w, h = self.send_button.size
            self.button_bg.pos = (x, y)
            self.button_bg.size = (w, h)
            cx, cy = x + w / 2, y + h / 2
            self.arrow_line.points = [cx, cy - dp(10), cx, cy + dp(10)]
            self.arrow_left.points = [
                cx - dp(7), cy + dp(3), cx, cy + dp(10)
            ]
            self.arrow_right.points = [
                cx, cy + dp(10), cx + dp(7), cy + dp(3)
            ]

        self.send_button.bind(pos=update_send_button, size=update_send_button)
        update_send_button()
        self.send_button.bind(on_release=self.send_message)
        self.bottom.add_widget(self.send_button)
        self.root_box.add_widget(self.bottom)
        self.input.bind(on_text_validate=self.send_message)

        self.add_message("Здарова ёпта! Я Dextazzy AI. Чем подсобить?", "ai")
        Window.bind(size=self.on_window_resize)
        return self.root_box

    def on_window_resize(self, *args):
        Clock.schedule_once(self.scroll_to_bottom, 0.2)

    def scroll_to_bottom(self, *args):
        try:
            self.scroll.scroll_y = 0
        except Exception:
            pass

    def add_message(self, text, role):
        is_user = role == "user"

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(10),
            spacing=dp(6),
            padding=[dp(2), 0, dp(2), 0]
        )

        bubble = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            padding=[dp(13), dp(10)]
        )
        draw_rounded(bubble, BLUE if is_user else PANEL, 17)

        message = Label(
            text=text,
            markup=False,
            color=get_color_from_hex(WHITE),
            font_size="16sp",
            halign="left",
            valign="top",
            size_hint_y=None
        )
        bubble.add_widget(message)

        def update_message(*args):
            available = max(dp(120), self.scroll.width * 0.78)
            message.text_size = (available - dp(26), None)
            message.texture_update()
            message.height = max(dp(24), message.texture_size[1] + dp(2))
            bubble.width = available
            bubble.height = message.height + dp(20)
            row.height = bubble.height

        message.bind(texture_size=lambda *args: update_message())
        row.bind(width=lambda *args: update_message())

        if is_user:
            row.add_widget(Widget(size_hint_x=1))
            row.add_widget(bubble)
        else:
            row.add_widget(bubble)
            row.add_widget(Widget(size_hint_x=1))

        self.chat.add_widget(row)
        Clock.schedule_once(self.scroll_to_bottom, 0.15)

    def send_message(self, *args):
        if self.busy:
            return

        text = self.input.text.strip()
        if not text:
            return

        if not API_KEY or API_KEY == "ВСТАВЬ_НОВЫЙ_API_КЛЮЧ":
            self.status.text = "Добавь новый API-ключ в main.py"
            return

        self.input.text = ""
        self.add_message(text, "user")
        self.history.append({"role": "user", "parts": [{"text": text}]})

        self.busy = True
        self.send_button.disabled = True
        self.status.text = "Dextazzy AI думает..."

        threading.Thread(target=self.ask_ai, daemon=True).start()

    def ask_ai(self):
        try:
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": self.history[-12:],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 700}
            }
            response = requests.post(
                API_URL,
                params={"key": API_KEY},
                json=payload,
                timeout=45
            )

            if response.status_code != 200:
                try:
                    data = response.json()
                    error = data.get("error", {}).get("message", response.text)
                except Exception:
                    error = response.text
                answer = f"Ошибка API ({response.status_code}): {error}"
            else:
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    answer = "Модель не вернула ответ. Попробуй ещё раз."
                else:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    answer = "".join(
                        part.get("text", "") for part in parts if "text" in part
                    ).strip() or "Ответ оказался пустым."

            if not answer.startswith("Ошибка API"):
                self.history.append({"role": "model", "parts": [{"text": answer}]})

        except requests.exceptions.Timeout:
            answer = "Сервер отвечает слишком долго. Попробуй ещё раз."
        except requests.exceptions.RequestException as exc:
            answer = f"Ошибка подключения: {exc}"
        except Exception as exc:
            answer = f"Ошибка: {exc}"

        Clock.schedule_once(lambda dt: self.finish_answer(answer))

    def finish_answer(self, answer):
        self.add_message(answer, "ai")
        self.status.text = "Готов к работе"
        self.busy = False
        self.send_button.disabled = False
        self.scroll_to_bottom()


if __name__ == "__main__":
    DextazzyAI().run()
