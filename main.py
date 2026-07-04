# -*- coding: utf-8 -*-
"""
试卷总分汇总计算器
运行时自动扫描设备字体目录适配中文显示
"""

import os
import re
from kivy.core.text import LabelBase
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.utils import platform

# ============================================================
# 自动扫描设备字体目录，找到能用的中文字体
# ============================================================
FONT_NAME = None

def _find_chinese_font():
    """加载中文字体：优先使用打包字体，否则扫描系统目录"""
    # 打包字体（最高优先级，保证中文一定能显示）
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cnfont.ttf')
    if os.path.exists(bundled):
        try:
            LabelBase.register(name='cnfont', fn_regular=bundled)
            return 'cnfont'
        except Exception:
            pass

    # 系统字体路径
    priority = [
        '/system/fonts/HarmonyOS_Sans_SC_Regular.ttf',
        '/system/fonts/HarmonyOS_Sans_SC.ttf',
        '/system/fonts/HarmonyOS_Sans.ttf',
        '/system/fonts/HwChinese.ttf',
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/MiSans-Regular.ttf',
    ]
    for path in priority:
        if os.path.exists(path):
            try:
                LabelBase.register(name='cnfont', fn_regular=path)
                return 'cnfont'
            except Exception:
                continue

    # 兜底：扫描整个字体目录
    exclude_kw = ['clock', 'emoji', 'condensed', 'thin', 'light',
                  'italic', 'bold', 'mono', 'arabic', 'thai', 'hebrew',
                  'lao', 'khmer', 'myanmar', 'tibetan', 'devanagari',
                  'bengali', 'gujarati', 'gurmukhi', 'kannada',
                  'malayalam', 'oriya', 'sinhala', 'tamil', 'telugu']
    for fd in ['/system/fonts']:
        if not os.path.isdir(fd):
            continue
        try:
            files = sorted(os.listdir(fd))
        except PermissionError:
            continue
        for fname in files:
            if not fname.endswith(('.ttf', '.ttc', '.otf')):
                continue
            if any(kw in fname.lower() for kw in exclude_kw):
                continue
            path = os.path.join(fd, fname)
            try:
                LabelBase.register(name='cnfont', fn_regular=path)
                return 'cnfont'
            except Exception:
                continue

    return None


FONT_NAME = _find_chinese_font()


def f(*args, **kwargs):
    """控件字体辅助"""
    if FONT_NAME:
        kwargs['font_name'] = FONT_NAME
    return kwargs


# ============================================================
IS_ANDROID = (platform == 'android')


class ScoreCalculator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(12), **kwargs)

        # 标题
        self.add_widget(Label(
            text='试卷总分计算器',
            size_hint_y=None, height=dp(50),
            font_size=sp(24),
            halign='center', valign='middle',
            **f()
        ))

        # 总分
        self.total_label = Label(
            text='0',
            size_hint_y=0.25,
            font_size=sp(72),
            bold=True,
            halign='center', valign='middle',
            **f()
        )
        self.add_widget(self.total_label)

        # 提示
        self.hint_label = Label(
            text='点击下方按钮开始' if FONT_NAME else '（未找到中文字体，可能会显示异常）',
            size_hint_y=None, height=dp(36),
            font_size=sp(16),
            halign='center', valign='middle',
            color=(0.4, 0.4, 0.4, 1),
            **f()
        )
        self.add_widget(self.hint_label)

        # 麦克风按钮
        self.mic_btn = Button(
            text='🎤  点击录音',
            size_hint_y=0.18,
            font_size=sp(28),
            background_color=(0.2, 0.6, 1, 1),
            background_normal='',
            **f()
        )
        self.mic_btn.bind(on_press=self.on_mic_press)
        self.add_widget(self.mic_btn)

        # 辅助按钮
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(56), spacing=dp(12)
        )
        undo_btn = Button(
            text='撤销上一步', font_size=sp(18),
            background_color=(0.6, 0.6, 0.6, 1), background_normal='', **f()
        )
        undo_btn.bind(on_press=self.undo)
        btn_row.add_widget(undo_btn)

        clear_btn = Button(
            text='清零', font_size=sp(18),
            background_color=(0.9, 0.4, 0.3, 1), background_normal='', **f()
        )
        clear_btn.bind(on_press=self.clear)
        btn_row.add_widget(clear_btn)
        self.add_widget(btn_row)

        # 历史
        self.history_label = Label(
            text='暂无记录',
            size_hint_y=0.3,
            font_size=sp(14),
            halign='left', valign='top',
            color=(0.3, 0.3, 0.3, 1),
            **f()
        )
        self.add_widget(self.history_label)

        self.total = 0
        self.history = []
        self.is_listening = False

        if IS_ANDROID:
            self.init_android_speech()

    # ========== Android 语音 ==========

    def init_android_speech(self):
        try:
            from jnius import autoclass
            self.RecognizerIntent = autoclass('android.speech.RecognizerIntent')
            self.SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
            self.Locale = autoclass('java.util.Locale')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.speech = self.SpeechRecognizer.createSpeechRecognizer(
                PythonActivity.mActivity
            )

            class Listener(autoclass('java.lang.Object').__javaclass__):
                def __init__(self, outer):
                    super().__init__()
                    self.outer = outer

                def onReadyForSpeech(self, p): pass
                def onBeginningOfSpeech(self): pass
                def onRmsChanged(self, r): pass
                def onBufferReceived(self, b): pass
                def onEndOfSpeech(self): pass
                def onPartialResults(self, p): pass
                def onEvent(self, e, p): pass

                def onError(self, error):
                    Clock.schedule_once(lambda dt: self.outer.on_speech_error(error))

                def onResults(self, results):
                    matches = results.getStringArrayList(
                        self.outer.SpeechRecognizer.RESULTS_RECOGNITION
                    )
                    if matches and matches.size() > 0:
                        Clock.schedule_once(
                            lambda dt: self.outer.on_speech_result(matches.get(0))
                        )

            self.speech.setRecognitionListener(Listener(self))
        except Exception as e:
            self.hint_label.text = '语音不可用: ' + str(e)

    def on_mic_press(self, instance):
        if not IS_ANDROID:
            self.show_text_input()
            return

        if self.is_listening:
            try:
                self.speech.stopListening()
            except:
                pass
            self.mic_btn.text = '🎤  点击录音'
            self.mic_btn.background_color = (0.2, 0.6, 1, 1)
            self.is_listening = False
            return

        try:
            intent = self.RecognizerIntent(
                self.RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )
            intent.putExtra(
                self.RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                self.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            intent.putExtra(
                self.RecognizerIntent.EXTRA_LANGUAGE,
                self.Locale.CHINESE.toString()
            )
            self.speech.startListening(intent)
            self.is_listening = True
            self.mic_btn.text = '🔴  正在听...'
            self.mic_btn.background_color = (1, 0.2, 0.2, 1)
            self.hint_label.text = '请说出分数...'
        except Exception as e:
            self.hint_label.text = '启动失败: ' + str(e)

    def on_speech_result(self, text):
        self.mic_btn.text = '🎤  点击录音'
        self.mic_btn.background_color = (0.2, 0.6, 1, 1)
        self.is_listening = False
        self.process_input(text)

    def on_speech_error(self, error):
        self.mic_btn.text = '🎤  点击录音'
        self.mic_btn.background_color = (0.2, 0.6, 1, 1)
        self.is_listening = False
        msgs = {
            1: '网络超时', 2: '网络错误', 3: '音频错误',
            4: '服务器错误', 5: '客户端错误', 6: '未检测到语音',
            7: '无匹配结果', 8: '识别器忙', 9: '请授权麦克风权限',
        }
        self.hint_label.text = msgs.get(error, f'识别失败({error})')

    # ========== 桌面端文本输入 ==========

    def show_text_input(self):
        box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        box.add_widget(Label(
            text='输入分数（一次一个，或算式如 23+15）：',
            font_size=sp(16), halign='left', **f()
        ))
        box.add_widget(Label(
            text='支持：数字 / 加 / 减 / 乘 / 除',
            font_size=sp(13), color=(0.5, 0.5, 0.5, 1), **f()
        ))

        txt = TextInput(
            hint_text='例如: 23',
            font_size=sp(22), multiline=False, **f()
        )
        box.add_widget(txt)

        btn_layout = BoxLayout(
            orientation='horizontal', size_hint_y=None, height=dp(52), spacing=dp(8)
        )
        cancel_btn = Button(
            text='取消', font_size=sp(18),
            background_color=(0.6, 0.6, 0.6, 1), **f()
        )
        ok_btn = Button(
            text='确认', font_size=sp(18),
            background_color=(0, 0.7, 0, 1), **f()
        )
        popup = Popup(
            title='手动输入', content=box,
            size_hint=(0.85, 0.45), auto_dismiss=False
        )
        cancel_btn.bind(on_press=popup.dismiss)
        ok_btn.bind(on_press=lambda x: (self.process_input(txt.text), popup.dismiss()))
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(ok_btn)
        box.add_widget(btn_layout)
        popup.open()

    # ========== 核心计算 ==========

    def process_input(self, text):
        text = text.strip()
        if not text:
            return

        expr = text
        expr = expr.replace('加', '+').replace('加上', '+')
        expr = expr.replace('减', '-').replace('减去', '-')
        expr = expr.replace('乘', '*').replace('乘以', '*')
        expr = expr.replace('除', '/').replace('除以', '/')
        expr = expr.replace('等于', '').replace('=', '')

        cn = {'零': '0', '一': '1', '二': '2', '两': '2', '三': '3',
              '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9'}
        for k, v in cn.items():
            expr = expr.replace(k, v)
        expr = expr.replace(' ', '')

        # 纯数字 → 累加
        if re.match(r'^\d+$', expr):
            num = int(expr)
            self.total += num
            self.history.append(('+' + expr, num))
        elif re.match(r'^[\d+\-*/().]+$', expr):
            try:
                result = eval(expr)
                result = round(result, 4)
                self.total = result
                self.history = [(expr, result)]
            except Exception:
                self.hint_label.text = '计算错误: ' + text
                return
        else:
            self.hint_label.text = '无法识别: ' + text
            return

        self.update_display()

    def update_display(self):
        self.total_label.text = str(
            int(self.total) if self.total == int(self.total) else self.total
        )
        self.hint_label.text = ''
        lines = []
        for expr, val in self.history:
            v = int(val) if val == int(val) else val
            lines.append(f'{expr}  →  {v}')
        self.history_label.text = '\n'.join(lines) if lines else '暂无记录'

    def undo(self, instance):
        if not self.history:
            self.hint_label.text = '没有可撤销的步骤'
            return
        _, val = self.history.pop()
        self.total -= val
        self.update_display()

    def clear(self, instance):
        self.total = 0
        self.history.clear()
        self.total_label.text = '0'
        self.hint_label.text = '已清零'
        self.history_label.text = '暂无记录'


class CalculatorApp(App):
    def build(self):
        self.title = '试卷总分计算器'
        return ScoreCalculator()

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    CalculatorApp().run()
