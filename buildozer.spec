[app]
title = Telema Gestion ECD
package.name = telemagestion
package.domain = org.telema

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy==2.3.1,charset_normalizer==3.3.2

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API Android cible / minimum (valeurs eprouvees avec python-for-android)
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
