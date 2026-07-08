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
TOKEN = "8653250290:AAFWG3CdV7-Oryk1s_XgfX6ePctQ67CTZ-E"
SERVER_IP = "91.211.118.90"
SERVER_PORT = 27036

# --- 3. БАЗА КАРТИНОК ДЛЯ КАРТ ---
# Сюди додавайте назви карт із вашого сервера та посилання на їхні фото
MAP_IMAGES = {
    "de_dust2": "https://vserb.ru",
    "de_inferno": "https://vserb.ru",
    "de_train": "https://vserb.ru",
    "de_nuke": "https://vserb.ru",
    "cs_mansion": "https://vserb.ru",
    "cs_assault": "https://vserb.ru",
    "awp_india": "https://vserb.ru"
}

# Картинка, якщо карти немає в списку MAP_IMAGES вище
DEFAULT_ONLINE_IMAGE = "https://vserb.ru"

# Картинка, яка надішлеться, якщо сервер вимкнений (Офлайн)
OFFLINE_IMAGE = "https://imgur.com"

# Ініціалізація бота
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# --- 4. ФУНКЦІЯ ЗАПИТУ ДО СЕРВЕРА CS 1.6 ---
def get_cs_status_direct():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(3.0)
        
        request = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        client.sendto(request, (SERVER_IP, SERVER_PORT))
        
        data, _ = client.recvfrom(4096)
        if len(data) < 5 or data[:4] != b'\xFF\xFF\xFF\xFF':
            return False, None, "❌ Отримано некоректну відповідь від сервера."
            
        payload = data[5:]
        
        server_name_end = payload.find(b'\x00')
        server_name = payload[:server_name_end].decode('utf-8', errors='ignore')
        payload = payload[server_name_end + 1:]
        
        map_end = payload.find(b'\x00')
        current_map = payload[:map_end].decode('utf-8', errors='ignore')
        payload = payload[map_end + 1:]
        
        for _ in range(2):
            end = payload.find(b'\x00')
            payload = payload[end + 1:]
            
        payload = payload[2:]
            
        if len(payload) >= 2:
            players = payload[0]
            max_players = payload[1]
        else:
            players, max_players = 0, 0
        
        text = f"🟢 *СЕРВЕР ОНЛАЙН*\n\n"
        text += f"🎮 Назва: {server_name}\n"
        text += f"🗺 Карта: {current_map}\n"
        text += f"👥 Гравці: *{players}/{max_players}*\n"
        
        return True, current_map, text
    except Exception as e:
        text = "🔴 *СЕРВЕР ОФЛАЙН*\n\n❌ Сервер зараз недоступний або вимкнений."
        return False, None, text

# --- 5. ОБРОБКА КОМАНДИ /info ---
@bot.message_handler(commands=['info'])
def send_cs_status(message):
    # Повідомляємо користувача, що бот завантажує фото
    try:
        bot.send_chat_action(message.chat.id, 'upload_photo')
    except:
        pass
    
    is_online, current_map, status_text = get_cs_status_direct()
    
    if is_online:
        # Шукаємо картинку карти у списку, якщо немає — беремо стандартну
        photo_url = MAP_IMAGES.get(current_map, DEFAULT_ONLINE_IMAGE)
    else:
        # Картинка офлайну
        photo_url = OFFLINE_IMAGE

    try:
        # Надсилаємо фото, а текст статусу буде описом під ним
        bot.send_photo(message.chat.id, photo_url, caption=status_text, parse_mode="Markdown")
    except Exception as e:
        # Якщо картинка не завантажилася, надсилаємо просто текст, щоб бот не падав
        bot.reply_to(message, status_text, parse_mode="Markdown")

# --- 6. ЗАПУСК БОТА ТА ВЕБ-СЕРВЕРА ---
if __name__ == "_-main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True)
