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
    """Отримує статус сервера через стороннє API (обхід бану IP на Railway)"""
    try:
        # Використовуємо стабільне API від відомого моніторингу GS4u
        url = f"https://gs4u.net{SERVER_IP}:{SERVER_PORT}/info.json"
        response = requests.get(url, timeout=5.0)
        
        if response.status_code != 200:
            return {"status": "offline", "text": f"🔴 *Статус сервера*: OFFLINE ❌\n\nСервер {SERVER_IP}:{SERVER_PORT} не відповідає на запити моніторингу."}
            
        data = response.json()
        
        # Перевіряємо чи онлайн сервер в базі моніторингу
        if data.get("online") == 0:
            return {"status": "offline", "text": f"🔴 *Статус сервера*: OFFLINE ❌\n\nСервер закритий або тимчасово вимкнений."}
            
        server_name = data.get("name", "CS 1.6 Server").lstrip('0Оo○◦ \t')
        current_map = data.get("map", "unknown")
        players_count = data.get("players", 0)
        max_players = data.get("maxplayers", 32)
        
        text = f"⚙️ Моніторинг {server_name}\n\n"
        text += f"🖥️ {server_name}\n"
        text += f"🌐 IP: {SERVER_IP}:{SERVER_PORT}\n"
        text += f"🗺️ Карта: {current_map}\n"
        text += f"👥 Гравці: {players_count}/{max_players}\n\n"
        
        # Спроба отримати список гравців через API
        players_url = f"https://gs4u.net{SERVER_IP}:{SERVER_PORT}/players.json"
        players_resp = requests.get(players_url, timeout=4.0)
        
        if players_resp.status_code == 200:
            players_data = players_resp.json().get("players", [])
            # Сортуємо за кількістю фрагів (score)
            players_data.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
            
            if players_count > 0 and players_data:
                for idx, p in enumerate(players_data[:20], 1): # Обмежуємо топ-20 гравців
                    if idx == 1: emoji = "🥇"
                    elif idx == 2: emoji = "🥈"
                    elif idx == 3: emoji = "🥉"
                    else: emoji = "🎮"
                    name = p.get("name", "Гравець")
                    frags = p.get("score", 0)
                    text += f"{emoji} {name} — {frags} вбивств\n"
            elif players_count > 0:
                text += "⏳ _Гравці підключаються до карти..._\n"
            else:
                text += "💤 _На сервері немає гравців._\n"
        else:
            if players_count > 0:
                text += "🎮 _На сервері є гравці, але список зараз оновлюється..._\n"
            else:
                text += "💤 _На сервері немає гравців._\n"
                
        return {"status": "online", "text": text}
        
    except Exception as e:
        return {"status": "error", "text": f"⚠️ *Помилка API*: Не вдалося отримати дані сервера з моніторингу. ({str(e)})"}

@bot.message_handler(commands=['info', 'server'])
def send_cs_status(message):
    # Викликаємо нову стабільну функцію через API
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
    print("Telegram API-based bot started successfully...")
    bot.polling(none_stop=True)
    
