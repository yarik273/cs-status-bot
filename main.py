import os
import socket
import struct
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# Микро-веб-сервер для Render
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

def get_challenge_token(client, ip, port, request_header):
    """Получает защитный challenge-токен от сервера CS 1.6"""
    req = b'\xFF\xFF\xFF\xFF' + request_header + b'\xFF\xFF\xFF\xFF'
    client.sendto(req, (ip, port))
    try:
        data, _ = client.recvfrom(4096)
        if data.startswith(b'\xFF\xFF\xFF\xFFA'):  # Ответ с токеном 'A'
            return data[5:9]
    except socket.timeout:
        pass
    return b'\xFF\xFF\xFF\xFF'

def get_cs_players(client, ip, port):
    """Получает полный список имен игроков на сервере"""
    token = get_challenge_token(client, ip, port, b'U')
    req = b'\xFF\xFF\xFF\xFFU' + token
    client.sendto(req, (ip, port))
    
    try:
        data, _ = client.recvfrom(65535)
        if not data.startswith(b'\xFF\xFF\xFF\xFFD'): # Ответ с данными 'D'
            return []
        
        payload = data[5:]
        if len(payload) == 0:
            return []
            
        num_players = payload[0]
        payload = payload[1:]
        players_list = []
        
        for _ in range(num_players):
            if len(payload) < 2:
                break
            # Пропускаем индекс игрока (1 байт)
            payload = payload[1:]
            
            # Читаем никнейм
            name_end = payload.find(b'\x00')
            if name_end == -1:
                break
            name = payload[:name_end].decode('utf-8', errors='ignore').strip()
            payload = payload[name_end + 1:]
            
            # Пропускаем фраги (4 байта) и время в игре (4 байта)
            payload = payload[8:]
            
            if name:  # Игнорируем пустые ники HLTV или подключающихся
                players_list.append(name)
                
        return players_list
    except Exception:
        return []

def get_cs_status_full():
    """Собирает полный статус сервера (Инфо + Игроки онлайн)"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(2.5)
        
        # 1. Запрос общей информации (A2S_INFO)
        info_request = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        client.sendto(info_request, (SERVER_IP, SERVER_PORT))
        
        data, _ = client.recvfrom(4096)
        payload = data[5:]
        
        # Название сервера
        server_name_end = payload.find(b'\x00')
        server_name = payload[:server_name_end].decode('utf-8', errors='ignore')
        payload = payload[server_name_end + 1:]
        
        # Текущая карта
        map_end = payload.find(b'\x00')
        current_map = payload[:map_end].decode('utf-8', errors='ignore')
        payload = payload[map_end + 1:]
        
        # Пропуск папки и названия игры
        for _ in range(2):
            end = payload.find(b'\x00')
            payload = payload[end + 1:]
            
        # Количество игроков
        if len(payload) >= 4:
            players_count = payload[2]
            max_players = payload[3]
        else:
            players_count, max_players = 0, 0
            
        # 2. Запрос списка игроков (A2S_PLAYER)
        players_names = get_cs_players(client, SERVER_IP, SERVER_PORT)
        
# Формирование красивого текста ответа
        text = f"🟢 *Статус сервера*: ONLINE 🚀\n\n"
        text += f"🖥️ *Название*: {server_name}\n"
        text += f"🗺️ *Карта*: {current_map}\n"
        text += f"👥 *Игроки*: {players_count}/{max_players}\n\n"
        
        if players_count > 0 and players_names:
            text += "👤 *Список игроков в игре:*\n"
            for idx, p_name in enumerate(players_names, 1):
                text += f"{idx}. {p_name}\n"
        elif players_count > 0 and not players_names:
            text += "⏳ _Игроки подключаются или загружаются..._\n"
        else:
            text += "💤 _На сервере нет игроков._\n"
            
        return text
        
    except socket.timeout:
        return "🔴 *Статус сервера*: OFFLINE ❌\n\nСейчас сервер недоступен или выключен."
    except Exception as e:
        return "⚠️ *Ошибка*: Не удалось получить данные с сервера."

@bot.message_handler(commands=['info'])
def send_cs_status(message):
    status_text = get_cs_status_full()
    bot.reply_to(message, status_text, parse_mode="Markdown")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True)
