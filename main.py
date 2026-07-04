from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import re

class VoiceCalculator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=30, spacing=20, **kwargs)

        self.result_label = Label(
            text='等待语音输入...',
            font_size=36,
            size_hint_y=0.3,
            halign='center'
        )
        self.add_widget(self.result_label)

        self.speak_btn = Button(
            text='🎤 按住说话',
            font_size=28,
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.speak_btn.bind(on_press=self.on_voice_start)
        self.speak_btn.bind(on_release=self.on_voice_end)
        self.add_widget(self.speak_btn)

        self.history_label = Label(
            text='',
            font_size=16,
            size_hint_y=0.4,
            halign='left'
        )
        self.add_widget(self.history_label)

        self.history = []

    def on_voice_start(self, instance):
        instance.text = '🔴 正在听...'
        instance.background_color = (1, 0.3, 0.3, 1)

    def on_voice_end(self, instance):
        instance.text = '🎤 按住说话'
        instance.background_color = (0.2, 0.6, 1, 1)
        self.show_input_popup()

    def show_input_popup(self):
        layout = BoxLayout(orientation='vertical', spacing=10)

        lbl = Label(text='请输入语音识别结果：', font_size=18)
        hint = Label(text='例：35加28减12', font_size=14, color=(0.5,0.5,0.5,1))
        txt = TextInput(hint_text='35加28减12', font_size=20, multiline=False)
        btn = Button(text='确认计算', font_size=20, background_color=(0,0.7,0,1))
        btn.bind(on_press=lambda x: self.calculate(txt.text))

        layout.add_widget(lbl)
        layout.add_widget(hint)
        layout.add_widget(txt)
        layout.add_widget(btn)

        popup = Popup(title='语音输入', content=layout, size_hint=(0.85, 0.5))
        popup.open()

    def calculate(self, text):
        if not text or text.strip() == '':
            self.result_label.text = '没有识别到内容'
            return

        expr = text.replace('加', '+').replace('减', '-').replace('乘', '*').replace('除', '/')
        expr = expr.strip()

        if not re.match(r'^[\d+\-*/().\s]+$', expr):
            self.result_label.text = '无法识别，请重新说'
            return

        try:
            result = eval(expr)
            result = round(result, 4)
            display = text + ' = ' + str(result)
            self.result_label.text = '计算结果：' + display
            self.history.append(display)
            self.history_label.text = '历史记录：\n' + '\n'.join(self.history[-5:])
        except Exception as e:
            self.result_label.text = '计算出错：' + str(e)


class CalculatorApp(App):
    def build(self):
        return VoiceCalculator()

if __name__ == '__main__':
    CalculatorApp().run()

