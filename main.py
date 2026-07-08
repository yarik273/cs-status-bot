import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
# Підключаємо нову сучасну бібліотеку для читання GoldSource серверів
import openserverrequests

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

# --- 3. БАЗА КАРТИНОК ДЛЯ КАРТ ---
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

# --- 4. НАДІЙНА ФУНКЦІЯ ЗАПИТУ ЧЕРЕЗ OPENSERVERREQUESTS ---
def get_cs_status_modern():
    try:
        # Робимо запит до CS 1.6 (GoldSource протокол)
        server = openserverrequests.GoldSource(SERVER_IP, SERVER_PORT, timeout=4.0)
        info = server.get_info()
        players_data = server.get_players()
        
        server_name = info.get('hostname', 'CS 1.6 Server')
        current_map = info.get('map', 'unknown')
        players_count = info.get('players', 0)
        max_players = info.get('max_players', 32)
        
        # Збираємо список нікнеймів
        player_names = []
        if players_data and 'players' in players_data:
            for p in players_data['players']:
                name = p.get('name', '').strip()
                if name: # Прибираємо порожні ніки
                    player_names.append(name)
                    
        text = f"🟢 *СЕРВЕР ОНЛАЙН*\n\n"
        text += f"🎮 Назва: {server_name}\n"
        text += f"🗺 Карта: {current_map}\n"
        text += f"👥 Гравці: *{players_count}/{max_players}*\n\n"
        
        if player_names:
            text += "👤 *Список гравців в онлайні:*\n"
            for i, name in enumerate(player_names, 1):
                text += f"{i}. {name}\n"
        elif players_count > 0:
            text += "⏳ _Оновлюю список гравців..._\n"
        else:
            text += "💤 _На сервері зараз немає гравців._\n"
            
        return True, current_map, text
        
    except Exception as e:
        text = "🔴 *СЕРВЕР ОФЛАЙН*\n\n❌ Сервер зараз недоступний або вимкнений."
        return False, None, text

# --- 5. ОБРОБКА КОМАНДИ /info ---
@bot.message_handler(commands=['info'])
def send_cs_status(message):
    try:
        bot.send_chat_action(message.chat.id, 'upload_photo')
    except:
        pass
    
    is_online, current_map, status_text = get_cs_status_modern()
    
    if is_online:
        photo_path = MAP_IMAGES.get(current_map, DEFAULT_ONLINE_IMAGE)
    else:
        photo_path = OFFLINE_IMAGE

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
