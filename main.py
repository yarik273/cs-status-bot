import os
import socket
import threading
import struct
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
# Назви зліва чітко відповідають картам з вашого комп'ютера
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
    "de_tuscan": "images/de_tuscan.jpg",
    "fy_buzzkill2005": "images/fy_buzzkill2005.jpg",
    "aim_zone_esl": "images/aim_zone_esl.jpg",
    "aim_mortal_esl": "images/aim_mortal_esl.jpg"
}

# Дефолтні картинки, якщо карти немає у списку або сервер вимкнений
DEFAULT_ONLINE_IMAGE = "images/default.jpg"
OFFLINE_IMAGE = "images/offline.jpg"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# --- 4. ФУНКЦІЯ ЗАПИТУ ДО СЕРВЕРА (СТАТУС + ГРАВЦІ) ---
def get_cs_status_direct():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(2.5)
        
        # --- КРОК А: Отримання інформації про карту (A2S_INFO) ---
        request_info = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        client.sendto(request_info, (SERVER_IP, SERVER_PORT))
        
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
        players_count = payload if len(payload) >= 1 else 0
        max_players = payload if len(payload) >= 2 else 0
        
        # --- КРОК Б: Отримання нікнеймів гравців (A2S_PLAYER) ---
        player_names = []
        if players_count > 0:
            try:
                # ЗапитуємоChallenge-номер для GoldSource
                request_challenge = b'\xFF\xFF\xFF\xFF\x55\xFF\xFF\xFF\xFF'
                client.sendto(request_challenge, (SERVER_IP, SERVER_PORT))
                data_ch, _ = client.recvfrom(4096)
                
                if len(data_ch) >= 9 and data_ch == 0x41:
                    challenge = data_ch[5:9]
                    request_players = b'\xFF\xFF\xFF\xFF\x55' + challenge
                    client.sendto(request_players, (SERVER_IP, SERVER_PORT))
                    data_pl, _ = client.recvfrom(4096)
                    
                    if len(data_pl) > 5 and data_pl == 0x44:
                        pl_payload = data_pl[6:]
                        
                        while len(pl_payload) > 0:
                         pl_payload = pl_payload[1:] # Пропускаємо індекс
                            name_end = pl_payload.find(b'\x00')
                            if name_end == -1: break
                            name = pl_payload[:name_end].decode('utf-8', errors='ignore').strip()
                            pl_payload = pl_payload[name_end + 1:]
                            pl_payload = pl_payload[8:] # Пропускаємо фраги та час
                            
                            if name:
                                player_names.append(name)
            except Exception:
                pass

        # Формуємо красивий текст
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
    
    is_online, current_map, status_text = get_cs_status_direct()
    
    if is_online:
        photo_path = MAP_IMAGES.get(current_map, DEFAULT_ONLINE_IMAGE)
    else:
        photo_path = OFFLINE_IMAGE

    try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=status_text, parse_mode="Markdown")
        else:
            # Якщо якоїсь картинки не вистачає, надсилаємо дефолтну
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
    
