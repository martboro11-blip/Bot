import os
import re
import time
import threading
from dotenv import load_dotenv

from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from curl_cffi import requests

KV = '''
MDScreen:
    md_bg_color: 0.1, 0.1, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "16dp"
        spacing: "12dp"

        MDLabel:
            text: "🚀 OGame Bot Control"
            font_style: "H5"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: "40dp"

        MDTextField:
            id: email_input
            hint_text: "Gameforge E-Mail"
            mode: "rectangle"
            text_color_focus: 1, 1, 1, 1

        MDTextField:
            id: password_input
            hint_text: "Passwort"
            password: True
            mode: "rectangle"

        MDTextField:
            id: server_input
            hint_text: "Server URL (z.B. https://s1-de.ogame.gameforge.com)"
            text: "https://s1-de.ogame.gameforge.com"
            mode: "rectangle"

        MDBoxLayout:
            orientation: 'horizontal'
            spacing: "10dp"
            size_hint_y: None
            height: "50dp"

            MDRaisedButton:
                id: start_btn
                text: "BOT STARTEN"
                md_bg_color: 0.2, 0.7, 0.3, 1
                on_release: app.start_bot()

            MDRaisedButton:
                id: stop_btn
                text: "STOPP"
                disabled: True
                md_bg_color: 0.8, 0.2, 0.2, 1
                on_release: app.stop_bot()

        MDScrollView:
            MDLabel:
                id: log_output
                text: "[System bereit...]\n"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.8, 0.8, 0.8, 1
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
'''

class OGameBotEngine:
    def __init__(self, email, password, server_url, log_callback):
        self.email = email
        self.password = password
        self.server_url = server_url.rstrip('/')
        self.log = log_callback
        self.running = False
        self.session = requests.Session(impersonate="chrome120")

    def login(self):
        self.log("[+] Logge bei Gameforge ein...")
        login_url = "https://lobby.ogame.gameforge.com/api/users/login"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://lobby.ogame.gameforge.com',
            'Referer': 'https://lobby.ogame.gameforge.com/de_DE/',
            'Host': 'lobby.ogame.gameforge.com',
        }
        payload = {
            "identity": self.email,
            "password": self.password,
            "platform": "gameforge",
            "locale": "de_DE"
        }
        try:
            res = self.session.post(login_url, json=payload, headers=headers, timeout=15)
            if res.status_code not in [200, 201]:
                self.log(f"[!] Login abgelehnt ({res.status_code}).")
                return False
            
            token = res.json().get("token")
            if not token:
                self.log("[!] Kein Token erhalten.")
                return False

            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.log("[+] Gameforge Login erfolgreich!")

            acc_res = self.session.get("https://public-api.gameforge.com/ogame/game/v1/accounts", timeout=10)
            accounts = acc_res.json()
            target_acc = accounts[0] if accounts else None
            
            if not target_acc:
                self.log("[!] Kein Account gefunden.")
                return False

            acc_id = target_acc.get("id")
            srv_res = self.session.get(f"https://public-api.gameforge.com/ogame/game/v1/accounts/{acc_id}/login", timeout=10)
            
            if srv_res.status_code == 200:
                redirect_url = srv_res.json().get("url")
                if redirect_url:
                    self.session.get(redirect_url, timeout=10)
                    self.log("[+] Erfolgreich im Spiel eingeloggt!")
                    return True
        except Exception as e:
            self.log(f"[!] Fehler: {e}")
        return False

    def loop(self):
        self.running = True
        if self.login():
            while self.running:
                self.log("[⌛] Prüfe Account & Warteschlange...")
                time.sleep(60)
        self.running = False


class OGameApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def append_log(self, text):
        def update_label(dt):
            self.root.ids.log_output.text += f"\n{text}"
        Clock.schedule_once(update_label)

    def start_bot(self):
        email = self.root.ids.email_input.text
        password = self.root.ids.password_input.text
        server = self.root.ids.server_input.text

        if not email or not password:
            self.append_log("[!] Bitte E-Mail und Passwort eingeben.")
            return

        self.root.ids.start_btn.disabled = True
        self.root.ids.stop_btn.disabled = False
        
        self.bot = OGameBotEngine(email, password, server, self.append_log)
        self.bot_thread = threading.Thread(target=self.bot.loop, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        if hasattr(self, 'bot'):
            self.bot.running = False
        self.append_log("[!] Bot wird gestoppt...")
        self.root.ids.start_btn.disabled = False
        self.root.ids.stop_btn.disabled = True

if __name__ == "__main__":
    OGameApp().run()