[app]
title = 语音计算器
package.name = voicecalc
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a

[buildozer]
log_level = 2

[android]
permissions = INTERNET
android.api = 33
minapi = 21
android.private_storage = True
android.allow_backup = True
android.androidx = 1
android.gradle_build_tool = gradle
