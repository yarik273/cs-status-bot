import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# Мікро-веб-сервер для проходження перевірки працездатності (Health Check)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()   

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- ДАНІ ВАШОГО БОТА І СЕРВЕРА ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")

SERVER_IP = "91.211.118.90"
SERVER_PORT = "27036"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

def get_cs_status_via_api():
    """Отримує статус сервера через універсальне Valve Info API (обхід будь-яких банів на Railway)"""
    try:
        # Використовуємо відкрите стабільне API моніторингу ігрових серверів
        url = f"https://gamecms.org{SERVER_IP}&port={SERVER_PORT}"
        response = requests.get(url, timeout=8.0)
        
        if response.status_code != 200:
            # Альтернативне джерело, якщо перше API тимчасово недоступне
            url = f"https://vserver.space{SERVER_IP}/{SERVER_PORT}"
            response = requests.get(url, timeout=8.0)
            
        if response.status_code != 200:
            return {"status": "offline", "text": f"🔴 *Статус сервера*: OFFLINE ❌\n\nІгровий сервер зараз недоступний або захист блокує запити інтернет-моніторингів."}
            
        data = response.json()
        
        # Перевірка чи успішно API отримало дані з нашого сервера
        if not data or not data.get("status") or data.get("status") == "offline":
            return {"status": "offline", "text": f"🔴 *Статус сервера*: OFFLINE ❌\n\nСервер {SERVER_IP}:{SERVER_PORT} не відповідає. Можливо, він вимкнений."}
            
        # Забираємо дані і очищаємо назву від зайвих символів на початку
        server_name = data.get("name", "CS 1.6 Server").lstrip('0Оo○◦ \t')
        current_map = data.get("map", "unknown")
        players_count = int(data.get("players", 0))
        max_players = int(data.get("max_players", 32))
        
        text = f"⚙️ Моніторинг {server_name}\n\n"
        text += f"🖥️ {server_name}\n"
        text += f"🌐 IP: {SERVER_IP}:{SERVER_PORT}\n"
        text += f"🗺️ Карта: {current_map}\n"
        text += f"👥 Гравці: {players_count}/{max_players}\n\n"
        
        # Отримуємо список гравців через проксі-API
        players_url = f"https://gamecms.org{SERVER_IP}&port={SERVER_PORT}"
        players_resp = requests.get(players_url, timeout=6.0)
        
        if players_resp.status_code == 200:
            players_data = players_resp.json().get("players", [])
            # Сортування за фрагами (score) від більшого до меншого
            players_data.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
            
            if players_count > 0 and players_data:
                for idx, p in enumerate(players_data[:20], 1): # Топ-20 активних гравців
                    if idx == 1: emoji = "🥇"
                    elif idx == 2: emoji = "🥈"
                    elif idx == 3: emoji = "🥉"
                    else: emoji = "🎮"
                    name = p.get("name", "Гравець").strip()
                    if not name: name = "Підключення..."
                    frags = p.get("score", 0)
                    text += f"{emoji} {name} — {frags} вбивств\n"
            elif players_count > 0:
                text += "⏳ _Гравці підключаються до карти..._\n"
            else:
                text += "💤 _На сервері немає гравців._\n"
        else:
            if players_count > 0:
                text += "🎮 _На сервері є гравці, але детальний список оновлюється..._\n"
            else:
                text += "💤 _На сервері немає гравців._\n"
                
        return {"status": "online", "text": text}
        
    except Exception as e:
        return {"status": "error", "text": f"⚠️ *Помилка моніторингу*: Сервер не зміг обробити дані. ({str(e)})"}

@bot.message_handler(commands=['info', 'server'])
def send_cs_status(message):
    data = get_cs_status_via_api()
    
    MAIN_BANNER_ID = "AgACAgIAAxkBAAOgak6BkYsMaEy0JS3SUaoIQmyWCoAAAv8caxvTMHBKqvUcUE0TuaIBAAMCAAN5AAM8BA"
    thread_id = message.message_thread_id
    
    if data.get("status") == "online":
        try:
            bot.send_photo(
                chat_id=message.chat.id, 
                photo=MAIN_BANNER_ID, 
                caption=data["text"], 
                message_thread_id=thread_id
            )
            return
        except Exception:
            pass
            
    bot.send_message(
        chat_id=message.chat.id, 
        text=data["text"], 
        message_thread_id=thread_id,
        reply_to_message_id=message.message_id
    )

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram Valve-API bot started successfully...")
    bot.polling(none_stop=True)
    
