[app]
title = 语音学生计分计算器
package.name = voicescore
package.domain = com.marvis
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0.0
requirements = kivy,android,Pillow
fullscreen = 0
android.archs = arm64-v8a

[buildozer]
log_level = 2

[android]
permissions = RECORD_AUDIO, INTERNET
android_api = 33
minapi = 21
android.private_storage = True
android.copy_libs = 1
android.allow_backup = True
android.androidx = 1
android.gradle_build_tool = gradle
android.permissions_user_text = 本应用需要录音权限用于语音识别功能，需要网络权限用于语音服务。
