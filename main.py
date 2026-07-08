import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- 2. ДАНІ ВАШОГО БОТА І СЕРВЕРА ---
TOKEN = "8653250290:AAHfh7P94TajZXwVbLzPKKJywahtoKdszno"
SERVER_IP = "91.211.118.90"
SERVER_PORT = 27036

# --- 3. БАЗА КАРТИНОК ДЛЯ КАРТ (ЛОКАЛЬНІ ФАЙЛИ) ---
MAP_IMAGES = {
    "cs_mansion": "images/cs_mansion.jpg",
    "cs_assault": "images/cs_assault.jpg",
    "de_westwood": "images/de_westwood.jpg",
    "de_nuke": "images/de_nuke.jpg",
    "de_dust2": "images/de_dust2.jpg",
    "de_dust2_2x2": "images/de_dust2_2x2.jpg",
    "de_dust2_3x3": "images/de_dust2_3x3.jpg",
    "de_inferno": "images/de_inferno.jpg",
    "de_aztec": "images/de_aztec.jpg",
    "de_train": "images/de_train.jpg",
    "de_tuscan": "images/de_tuscan.jpg",
    "fy_buzzkill2005": "images/fy_buzzkill2005.jpg",
    "aim_zone_esl": "images/aim_zone_esl.jpg",
    "aim_mortal_esl": "images/aim_mortal_esl.jpg"
}

DEFAULT_ONLINE_IMAGE = "images/default.jpg"
OFFLINE_IMAGE = "images/offline.jpg"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=status_text, parse_mode="Markdown")
        else:
            if os.path.exists(DEFAULT_ONLINE_IMAGE):
                with open(DEFAULT_ONLINE_IMAGE, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=status_text, parse_mode="Markdown")
            else:
                bot.reply_to(message, status_text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, status_text, parse_mode="Markdown")

# --- 6. ЗАПУСК БОТА ТА ВЕБ-СЕРВЕРА ---
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True)
    
