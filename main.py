import os
import socket
import struct
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# Мікро-веб-сервер для проходження перевірки Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- ДАНІ ВАШОГО БОТА І СЕРВЕРА ---
TOKEN = "8653250290:AAFWG3CdV7-Oryk1s_XgfX6ePctQ67CTZ-E"
SERVER_IP = "91.211.118.90"
SERVER_PORT = 27036

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# Словник з картинками карт
MAP_IMAGES = {
    "de_dust2": "https://githubusercontent.com",
    "de_dust2_2x2": "https://githubusercontent.com",
    "dedust2x2": "https://githubusercontent.com",
    "de_inferno": "https://githubusercontent.com",
    "de_nuke": "https://githubusercontent.com",
    "de_train": "https://githubusercontent.com",
    "cs_italy": "https://githubusercontent.com",
    "default": "https://githubusercontent.com"
}

# Отримання статусу сервера CS 1.6
def get_cs_status_direct():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(3.0)
        
        request = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        client.sendto(request, (SERVER_IP, SERVER_PORT))
        
        data, _ = client.recvfrom(4096)
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
            
        if len(payload) >= 4:
            players = payload[2]
            max_players = payload[3]
        else:
            players, max_players = 0, 0
            
        return {
            "success": True,
            "name": server_name,
            "map": current_map,
            "players": players,
            "max_players": max_players
        }
    except Exception:
        return {"success": False}

# Генерація повідомлення та красивих кнопок
def generate_status_message_and_keyboard():
    data = get_cs_status_direct()
    
    if not data["success"]:
        text = "❌ *Сервер зараз недоступний або вимкнений.*"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="🔄 Оновити", callback_data="refresh_status"))
        return text, markup, MAP_IMAGES["default"]
        
    p = data["players"]
    m = data["max_players"]
    percent = int((p / m) * 100) if m > 0 else 0
    filled = int((p / m) * 10) if m > 0 else 0
    bar = "🟩" * filled + "⬜" * (10 - filled)
    
    text = f"💣 *{data['name']}*\n❤️\n\n"
    text += f"🗺️ *Карта:* {data['map']}\n"
    text += f"👥 *Гравці:* {p}/{m}  {bar} *{percent}%*\n"
    text += f"🌐 *IP:* {SERVER_IP}:{SERVER_PORT}\n"
    text += f"🔌 *Сервер:* info\n\n"
    
    if p == 0:
        text += "🟡 *Сервер порожній*\nНа сервері поки нікого немає..."
    else:
        text += "🟢 *Гра в самому розпалі!* Заходь грати!"
        
    markup = telebot.types.InlineKeyboardMarkup()
    connect_url = f"steam://connect/{SERVER_IP}:{SERVER_PORT}"
    
    btn_connect = telebot.types.InlineKeyboardButton(text="🎮 Підключитися", url=connect_url)
    btn_refresh = telebot.types.InlineKeyboardButton(text="🔄 Оновити статус", callback_data="refresh_status")
    
    markup.add(btn_connect)
    markup.add(btn_refresh)
    
    map_clean = data["map"].lower().strip()
    photo_url = MAP_IMAGES.get(map_clean, MAP_IMAGES["default"])
    
    return text, markup, photo_url
    # Обробник команд
@bot.message_handler(func=lambda msg: msg.text in ['/info', 'info', '/info@cs16_status_server_bot', 'info@cs16_status_server_bot'])
def send_cs_status(message):
    text, markup, photo_url = generate_status_message_and_keyboard()
    try:
        bot.send_photo(message.chat.id, photo_url, caption=text, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_status")
def callback_inline(call):
    text, markup, photo_url = generate_status_message_and_keyboard()
    try:
        media = telebot.types.InputMediaPhoto(photo_url, caption=text, parse_mode="Markdown")
        bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=media, reply_markup=markup)
    except Exception:
        pass
    bot.answer_callback_query(call.id)

if name == "main":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True)
