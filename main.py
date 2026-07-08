import os
import socket
import struct
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# Микро-веб-сервер для прохождения проверки Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- ДАННЫЕ ВАШЕГО БОТА И СЕРВЕРА ---
TOKEN = "8653250290:AAFWG3CdV7-Oryk1s_XgfX6ePctQ67CTZ-E"
SERVER_IP = "91.211.118.90"
SERVER_PORT = 27036

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# Прямой запрос к серверу CS 1.6 без использования сторонней библиотеки valve
def get_cs_status_direct():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(3.0)
        
        # Отправляем стандартный A2S_INFO запрос для CS 1.6
        request = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        client.sendto(request, (SERVER_IP, SERVER_PORT))
        
        data, _ = client.recvfrom(4096)
        payload = data[5:]
        
        # Считываем имя сервера
        server_name_end = payload.find(b'\x00')
        server_name = payload[:server_name_end].decode('utf-8', errors='ignore')
        payload = payload[server_name_end + 1:]
        
        # Считываем текущую карту
        map_end = payload.find(b'\x00')
        current_map = payload[:map_end].decode('utf-8', errors='ignore')
        payload = payload[map_end + 1:]
        
        # Пропускаем папку игры и название игры
        for _ in range(2):
            end = payload.find(b'\x00')
            payload = payload[end + 1:]
            
        # Считываем количество игроков и максимум
        if len(payload) >= 4:
            players = payload[2]
            max_players = payload[3]
        else:
            players, max_players = 0, 0
        
        text = f"🎮 *Статус сервера CS 1.6*:\n\n"
        text += f"📌 Назва: {server_name}\n"
        text += f"🗺️ Карта: {current_map}\n"
        text += f"👥 Гравці: {players}/{max_players}\n"
        return text
    except Exception as e:
        return "❌ Сервер зараз недоступний або вимкнений."

@bot.message_handler(commands=['info'])
def send_cs_status(message):
    status_text = get_cs_status_direct()
    bot.reply_to(message, status_text, parse_mode="Markdown")

if  __name__ == "__main__":
    # Запуск веб-сервера для Render в отдельном потоке
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    
    # Запуск самого телеграм-бота
    bot.polling(none_stop=True)
