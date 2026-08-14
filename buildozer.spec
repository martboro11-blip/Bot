[app]
title = OGame Bot
package.name = ogamebot
package.domain = org.ogame
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

requirements = python3,kivy,kivymd,requests,urllib3,certifi,charset_normalizer,idna,curl_cffi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 1