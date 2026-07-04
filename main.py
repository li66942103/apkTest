from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

student_data = []

class ScoreLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=10, **kwargs)
        self.title = Label(text="语音学生计分计算器", font_size=24, size_hint_y=0.1)
        self.add_widget(self.title)

        self.voice_text = TextInput(readonly=True, hint_text="语音识别结果", size_hint_y=0.2)
        self.add_widget(self.voice_text)

        self.scroll = ScrollView(size_hint_y=0.5)
        self.score_label = Label(text="学生分数列表：\n", font_size=16)
        self.scroll.add_widget(self.score_label)
        self.add_widget(self.scroll)

        self.total_label = Label(text="", font_size=20, color=(1,0,0,1), size_hint_y=0.1)
        self.add_widget(self.total_label)

        self.record_btn = Button(text="点击语音录入分数", size_hint_y=0.1, background_color=(0,0.6,1,1))
        self.record_btn.bind(on_press=self.voice_input)
        self.add_widget(self.record_btn)

    def voice_input(self, instance):
        try:
            from android import speech
            r = speech.SpeechRecognizer()
            self.voice_text.text = "正在聆听，请说：姓名 语文 数学 英语"
            res_text = r.listen()
            self.voice_text.text = res_text
            parts = res_text.split()
            name = parts[0]
            s1 = float(parts[1])
            s2 = float(parts[2])
            s3 = float(parts[3])
            total = s1 + s2 + s3
            student_data.append({"name": name, "ch": s1, "math": s2, "en": s3, "total": total})
            self.refresh_list()
            from android import TTS
            tts = TTS()
            tts.speak(f"{name}总分是{total}")
        except Exception as e:
            self.voice_text.text = f"识别失败：{str(e)}"

    def refresh_list(self):
        text = "学生分数列表：\n"
        all_total = 0
        for stu in student_data:
            line = f"{stu['name']} 语文{stu['ch']} 数学{stu['math']} 英语{stu['en']} 总分：{stu['total']}\n"
            text += line
            all_total += stu["total"]
        self.score_label.text = text
        self.total_label.text = f"全部学生总分合计：{all_total}"

class VoiceScoreApp(App):
    def build(self):
        return ScoreLayout()

if __name__ == "__main__":
    VoiceScoreApp().run()