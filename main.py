# 加载系统微软雅黑字体
from kivy.core.text import LabelBase
LabelBase.register(name="cnfont", fn_regular=r"C:\Windows\Fonts\msyh.ttc")

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput as PopText

student_data = []
IS_ANDROID = False
try:
    from android import speech, TTS
    IS_ANDROID = True
except ImportError:
    pass

class ScoreLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=10, **kwargs)
        # 所有文字控件强制 font_name="cnfont"
        self.title = Label(text="语音学生计分计算器", font_size=24, size_hint_y=0.1, font_name="cnfont")
        self.add_widget(self.title)

        self.voice_text = TextInput(readonly=True, hint_text="语音识别结果", size_hint_y=0.2, font_name="cnfont")
        self.add_widget(self.voice_text)

        self.scroll = ScrollView(size_hint_y=0.5)
        self.score_label = Label(text="学生分数列表：\n", font_size=16, font_name="cnfont")
        self.scroll.add_widget(self.score_label)
        self.add_widget(self.scroll)

        self.total_label = Label(text="", font_size=20, color=(1,0,0,1), size_hint_y=0.1, font_name="cnfont")
        self.add_widget(self.total_label)

        self.record_btn = Button(text="点击语音录入分数", size_hint_y=0.1, background_color=(0,0.6,1,1), font_name="cnfont")
        self.record_btn.bind(on_press=self.voice_input)
        self.add_widget(self.record_btn)

    def voice_input(self, instance):
        if IS_ANDROID:
            try:
                r = speech.SpeechRecognizer()
                self.voice_text.text = "正在聆听，请说：姓名 语文 数学 英语"
                res_text = r.listen()
                self.parse_score_text(res_text)
            except Exception as e:
                self.voice_text.text = f"识别失败：{str(e)}"
        else:
            content = BoxLayout(orientation="vertical")
            txt = PopText(hint_text="输入格式：张三 90 85 96", font_name="cnfont")
            btn = Button(text="确认提交", size_hint_y=0.3, font_name="cnfont")
            popup = Popup(title="电脑模拟语音输入", content=content, size_hint=(0.8,0.4))
            # Popup标题也要设置中文字体
            popup.title_font = "cnfont"
            def submit(x):
                self.parse_score_text(txt.text)
                popup.dismiss()
            btn.bind(on_press=submit)
            content.add_widget(txt)
            content.add_widget(btn)
            popup.open()

    def parse_score_text(self, res_text):
        self.voice_text.text = res_text
        parts = res_text.strip().split()
        if len(parts) != 4:
            self.voice_text.text = "格式错误！示例：小明 92 88 95"
            return
        try:
            name = parts[0]
            s1 = float(parts[1])
            s2 = float(parts[2])
            s3 = float(parts[3])
        except ValueError:
            self.voice_text.text = "分数必须是数字！"
            return

        total = s1 + s2 + s3
        student_data.append({"name": name, "ch": s1, "math": s2, "en": s3, "total": total})
        self.refresh_list()

        if IS_ANDROID:
            tts = TTS()
            tts.speak(f"{name}总分是{total}")

    def refresh_list(self):
        text = "学生分数列表：\n"
        all_total = 0
        for stu in student_data:
            line = f"{stu['name']} 语文{stu['ch']} 数学{stu['math']} 英语{stu['en']}\n总分：{stu['total']}\n"
            text += line
            all_total += stu["total"]
        self.score_label.text = text
        self.total_label.text = f"全部学生总分合计：{all_total}"

class VoiceScoreApp(App):
    def build(self):
        return ScoreLayout()

if __name__ == "__main__":
    VoiceScoreApp().run()
