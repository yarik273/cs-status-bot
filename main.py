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

def decode_text(byte_data):
    """Безопасно декодирует текст с сервера"""
    try:
        return byte_data.decode('utf-8').strip()
    except Exception:
        try:
            return byte_data.decode('cp1251', errors='ignore').strip()
        except Exception:
            return byte_data.decode('latin-1', errors='ignore').strip()

def get_challenge_token(client, ip, port, request_header):
    """Получает защитный challenge-токен от сервера CS 1.6"""
    req = b'\xFF\xFF\xFF\xFF' + request_header + b'\xFF\xFF\xFF\xFF'
    client.sendto(req, (ip, port))
    try:
        data, _ = client.recvfrom(4096)
        if data.startswith(b'\xFF\xFF\xFF\xFFA'):
            return data[5:9]
    except Exception:
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
            
        num_players = int(payload[0])
        payload = payload[1:]
        players_list = []
        
        for _ in range(num_players):
            if len(payload) < 2:
                break
            payload = payload[1:]  # Пропуск индекса
            
            name_end = payload.find(b'\x00')
            if name_end == -1:
                break
            name = decode_text(payload[:name_end])
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
        client.settimeout(4.0)
        
        info_request = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        client.sendto(info_request, (SERVER_IP, SERVER_PORT))
        
        data, _ = client.recvfrom(4096)
        payload = data[5:]
        
        # Чтение названия сервера
        server_name_end = payload.find(b'\x00')
        server_name = decode_text(payload[:server_name_end])
        server_name = server_name.lstrip('0Оo○◦ \t')
        payload = payload[server_name_end + 1:]
        
        # Чтение карты
        map_end = payload.find(b'\x00')
        current_map = decode_text(payload[:map_end])
        payload = payload[map_end + 1:]
        
        # Пропуск папки и названия игры
        for _ in range(2):
            end = payload.find(b'\x00')
            if end != -1:
                payload = payload[end + 1:]
               # Безопасное чтение игроков по фиксированным байтам
        if len(payload) >= 4:
            players_count = int(payload[2])
            max_players = int(payload[3])
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
                emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🎮"
                text += f"{emoji} {p['name']} — {p['frags']} вбивств\n"
        elif players_count > 0 and not players:
            text += "⏳ _Гравці підключаються до карти..._\n"
        else:
            text += "💤 _На сервері немає гравців._\n"
            
        return {"status": "online", "text": text}
        
    except socket.timeout:
        return {"status": "offline", "text": f"🔴 *Статус сервера*: OFFLINE ❌\n\nСервер {SERVER_IP}:{SERVER_PORT} зараз недоступний або вимкнений."}
    except Exception as e:
        return {"status": "error", "text": "⚠️ *Помилка*: Не вдалося зв'язатися з ігровим сервером."}

@bot.message_handler(commands=['info', 'server'])
def send_cs_status(message):
    data = get_cs_status_full()
    MAIN_BANNER_ID = "AgACAgIAAxkBAAOgak6BkYsMaEy0JS3SUaoIQmyWCoAAAv8caxvTMHBKqvUcUE0TuaIBAAMCAAN5AAM8BA"
    
    if data.get("status") == "online":
        try:
            bot.send_photo(message.chat.id, photo=MAIN_BANNER_ID, caption=data["text"], parse_mode="Markdown")
            return
        except Exception:
            pass
            
    bot.reply_to(message, data["text"], parse_mode="Markdown")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True) 
