# -*- coding: utf-8 -*-
"语音计算器 - Android版
支持中文显示和原生语音识别"

import os
import re
from kivy.core.text import LabelBase
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

# ========== 中文字体加载 ==========
FONT_PATHS = [
    '/system/fonts/NotoSansCJK-Regular.ttc',
    '/system/fonts/DroidSansFallback.ttf',
    '/system/fonts/NotoSansSC-Regular.otf',
    '/system/fonts/NotoSansHans-Regular.otf',
    '/system/fonts/MiSans-Regular.ttf',
    '/system/fonts/FZLanTingHeiS-R-GB.ttf',
    './cnfont.ttf',
]

font_loaded = False
for path in FONT_PATHS:
    if os.path.exists(path):
        try:
            LabelBase.register(name='cnfont', fn_regular=path)
            font_loaded = True
            break
        except Exception:
            continue

# ========== 语音识别 ==========
try:
    from jnius import autoclass
    from android.runnable import run_on_ui_thread
    from android import activity

    ANDROID_AVAILABLE = True
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
    AudioManager = autoclass('android.media.AudioManager')
    MediaPlayer = autoclass('android.media.MediaPlayer')
    Locale = autoclass('java.util.Locale')
except ImportError:
    ANDROID_AVAILABLE = False


class VoiceCalculator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=30, spacing=20, **kwargs)
        self.speech = None
        self.is_listening = False

        font_args = {'font_name': 'cnfont'} if font_loaded else {}

        self.result_label = Label(
            text='按下麦克风开始说话',
            font_size=36,
            size_hint_y=0.3,
            halign='center',
            **font_args
        )
        self.add_widget(self.result_label)

        self.speak_btn = Button(
            text='■ 点击录音',
            font_size=28,
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 1, 1),
            **font_args
        )
        self.speak_btn.bind(on_press=self.on_voice_start)
        self.add_widget(self.speak_btn)

        self.history_label = Label(
            text='',
            font_size=16,
            size_hint_y=0.4,
            halign='left',
            valign='top',
            **font_args
        )
        self.add_widget(self.history_label)

        self.history = []

        if ANDROID_AVAILABLE:
            self.setup_speech()
        else:
            self.result_label.text = '（桌面模式 - 无语音功能）'
            self.speak_btn.text = '手动输入'

    def setup_speech(self):
        "初始化Android语音识别"
        try:
            self.speech = SpeechRecognizer.createSpeechRecognizer(
                PythonActivity.mActivity
            )
            RecognitionListener = autoclass(
                'android.speech.RecognitionListener'
            )

            class SpeechListener(
                autoclass('java.lang.Object').__javaclass__
            ):
                def __init__(self, outer):
                    super().__init__()
                    self.outer = outer

                def onReadyForSpeech(self, params):
                    pass

                def onBeginningOfSpeech(self):
                    pass

                def onRmsChanged(self, rmsdB):
                    pass

                def onBufferReceived(self, buffer):
                    pass

                def onEndOfSpeech(self):
                    pass

                def onError(self, error):
                    Clock.schedule_once(
                        lambda dt: self.outer.on_speech_error(error)
                    )

                def onResults(self, results):
                    matches = results.getStringArrayList(
                        SpeechRecognizer.RESULTS_RECOGNITION
                    )
                    if matches and matches.size() > 0:
                        text = matches.get(0)
                        Clock.schedule_once(
                            lambda dt: self.outer.on_speech_result(text)
                        )

                def onPartialResults(self, results):
                    pass

                def onEvent(self, eventType, params):
                    pass

            self.listener = SpeechListener(self)
            self.speech.setRecognitionListener(self.listener)

        except Exception as e:
            self.result_label.text = '语音初始化失败: ' + str(e)
            self.speak_btn.text = '手动输入'

    def on_voice_start(self, instance):
        if not ANDROID_AVAILABLE or self.speech is None:
            from kivy.uix.textinput import TextInput
            from kivy.uix.popup import Popup

            layout = BoxLayout(orientation='vertical', spacing=10)

            font_args = {'font_name': 'cnfont'} if font_loaded else {}

            lbl = Label(
                text='请输入算式：',
                font_size=18,
                **font_args
            )
            hint = Label(
                text='例：35加28减12',
                font_size=14,
                color=(0.5, 0.5, 0.5, 1),
                **font_args
            )
            txt = TextInput(
                hint_text='35加28减12',
                font_size=20,
                multiline=False,
                **font_args
            )
            btn = Button(
                text='确认计算',
                font_size=20,
                background_color=(0, 0.7, 0, 1),
                **font_args
            )
            btn.bind(on_press=lambda x: self.calculate(txt.text))

            layout.add_widget(lbl)
            layout.add_widget(hint)
            layout.add_widget(txt)
            layout.add_widget(btn)

            popup = Popup(
                title='手动输入',
                content=layout,
                size_hint=(0.85, 0.5)
            )
            popup.open()
            return

        if self.is_listening:
            self.speech.stopListening()
            self.speak_btn.text = '■ 点击录音'
            self.speak_btn.background_color = (0.2, 0.6, 1, 1)
            self.is_listening = False
            return

        try:
            intent = autoclass('android.content.Intent')(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                Locale.CHINESE.toString()
            )
            intent.putExtra(
                RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                True
            )

            self.speech.startListening(intent)
            self.is_listening = True
            self.speak_btn.text = '■ 正在听...'
            self.speak_btn.background_color = (1, 0.3, 0.3, 1)
            self.result_label.text = '请说话...'

        except Exception as e:
            self.result_label.text = '启动语音失败: ' + str(e)

    def on_speech_result(self, text):
        self.speak_btn.text = '■ 点击录音'
        self.speak_btn.background_color = (0.2, 0.6, 1, 1)
        self.is_listening = False
        self.result_label.text = '识别结果：' + text
        self.calculate(text)

    def on_speech_error(self, error):
        self.speak_btn.text = '■ 点击录音'
        self.speak_btn.background_color = (0.2, 0.6, 1, 1)
        self.is_listening = False

        error_msgs = {
            1: '网络超时',
            2: '网络错误',
            3: '音频错误',
            4: '服务器错误',
            5: '客户端错误',
            6: '未检测到语音',
            7: '无匹配结果',
            8: '识别器忙',
            9: '权限不足（请授予麦克风权限）',
        }
        msg = error_msgs.get(error, f'未知错误({error})')
        self.result_label.text = '语音识别失败：' + msg

    def calculate(self, text):
        if not text or text.strip() == '':
            self.result_label.text = '没有识别到内容'
            return

        cn_map = {
            '零': '0', '一': '1', '二': '2', '两': '2',
            '三': '3', '四': '4', '五': '5',
            '六': '6', '七': '7', '八': '8', '九': '9',
            '十': '10',
        }

        expr = text.strip()
        expr = expr.replace('加', '+').replace('减', '-')
        expr = expr.replace('乘', '*').replace('乘以', '*')
        expr = expr.replace('除', '/').replace('除以', '/')
        expr = expr.replace('等于', '').replace('=','')

        for cn, num in cn_map.items():
            expr = expr.replace(cn, num)

        expr = expr.replace(' ', '')

        if not re.match(r'^[\d+\-*/().]+$', expr):
            self.result_label.text = (
                '无法计算：' + text + '\n请说类似"35加28减12"'
            )
            return

        try:
            result = eval(expr)
            result = round(result, 4)
            display = text + ' = ' + str(result)
            self.result_label.text = display
            self.history.append(display)
            self.history_label.text = (
                '历史记录：\n' + '\n'.join(self.history[-5:])
            )
            self.speak_result(str(result))

        except Exception as e:
            self.result_label.text = '计算出错：' + str(e)

    def speak_result(self, text):
        try:
            from jnius import autoclass
            TTS = autoclass('android.speech.tts.TextToSpeech')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            tts = TTS(
                PythonActivity.mActivity,
                autoclass('android.speech.tts.TextToSpeech')()
            )
            tts.speak(
                '等于' + text,
                TTS.QUEUE_FLUSH,
                None,
                'result'
            )
        except Exception:
            pass


class CalculatorApp(App):
    def build(self):
        return VoiceCalculator()

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    CalculatorApp().run()

