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
TOKEN = "8653250290:AAHfh7P94TajZXwVbLzPKKJywahtoKdszno"
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
        if data.startswith(b'\xFF\xFF\xFF\xFFA'):
            return data[5:9]
    except socket.timeout:
        pass
    return b'\xFF\xFF\xFF\xFF'

def get_cs_players(client, ip, port):
    """Получает список игроков с количеством их убийств (фрагов)"""
    token = get_challenge_token(client, ip, port, b'U')
    req = b'\xFF\xFF\xFF\xFFU' + token
    client.sendto(req, (ip, port))
    
    try:
        data, _ = client.recvfrom(65535)
        if not data.startswith(b'\xFF\xFF\xFF\xFFD'):
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
            payload = payload[1:]
            
            name_end = payload.find(b'\x00')
            if name_end == -1:
                break
            name = payload[:name_end].decode('utf-8', errors='ignore').strip()
            payload = payload[name_end + 1:]
            
            if len(payload) < 8:
                break
            frags = struct.unpack('<i', payload[:4])[0]
            payload = payload[8:]
            
            if name:
                players_list.append({"name": name, "frags": frags})
                
        players_list.sort(key=lambda x: x["frags"], reverse=True)
        return players_list
    except Exception:
        return []

def get_cs_status_full():
    """Собирает статус сервера в красивом стиле"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(2.5)
        
        info_request = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        client.sendto(info_request, (SERVER_IP, SERVER_PORT))
        
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
            players_count = payload[2]
            max_players = payload[3]
        else:
            players_count, max_players = 0, 0
            
        players = get_cs_players(client, SERVER_IP, SERVER_PORT)
        
        text = f"⚙️ *Моніторинг {server_name}*\n\n"
        text += f"🖥️ *{server_name}*\n"
        text += f"🌐 *IP*: {SERVER_IP}:{SERVER_PORT}\n"
        text += f"🗺️ *Карта*: {current_map}\n"
        text += f"👥 *Гравці*: {players_count}/{max_players}\n\n"
        
        if players_count > 0 and players:
            for idx, p in enumerate(players, 1):
                if idx == 1:
                    emoji = "🥇"
                elif idx == 2:
                    emoji = "🥈"
                elif idx == 3:
                    emoji = "🥉"
                else:
                    emoji = "🎮"
                text += f"{emoji} {p['name']} — {p['frags']} вбивств\n"
        elif players_count > 0 and not players:
            text += "⏳ _Гравці підключаються до карти..._\n"
        else:
            text += "💤 _На сервері немає гравців._\n"
            
        return text
        
    except socket.timeout:
        return f"🔴 *Статус сервера*: OFFLINE ❌\n\nСервер {SERVER_IP}:{SERVER_PORT} зараз недоступний або вимкнений."
    except Exception as e:
        return "⚠️ *Помилка*: Не вдалося зв'язатися з ігровим сервером."

@bot.message_handler(commands=['info', 'server'])
def send_cs_status(message):
    status_text = get_cs_status_full()
    bot.reply_to(message, status_text, parse_mode="Markdown")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True)
