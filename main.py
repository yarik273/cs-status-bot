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

def fetch_data_with_fallback():
    """Спробує отримати дані сервера з трьох різних незалежних API джерел"""
    # Джерело 1: GameCMS API
    try:
        url = "https://gamecms.org"
        res = requests.get(url, timeout=5.0)
        if res.status_code == 200 and res.json().get("status") != "offline":
            return "gamecms", res.json()
    except Exception:
        pass

    # Джерело 2: VServer Space API
    try:
        url = "https://vserver.space"
        res = requests.get(url, timeout=5.0)
        if res.status_code == 200 and res.json().get("online") is True:
            return "vserver", res.json()
    except Exception:
        pass

    # Джерело 3: Резервне геймерське API моніторингу GS4u через пряме посилання
    try:
        url = "https://gs4u.net"
        res = requests.get(url, timeout=5.0)
        if res.status_code == 200 and res.json().get("online") != 0:
            return "gs4u", res.json()
    except Exception:
        pass

    return None, None

def get_cs_status_via_api():
    """Аналізує отримані дані від успішного джерела та формує гарний текст"""
    source_name, data = fetch_data_with_fallback()
    
    if not data:
        return {"status": "offline", "text": "🔴 *Статус сервера*: OFFLINE ❌\n\nСервер не відповідає на запити жодного з трьох незалежних моніторингів. Можливо, на ігровому хостингу відбуваються технічні роботи."}
        
    try:
        # Уніфікація даних під різні формати відповідей API
        if source_name == "gamecms":
            server_name = data.get("name", "CS 1.6 Server")
            current_map = data.get("map", "unknown")
            players_count = int(data.get("players", 0))
            max_players = int(data.get("max_players", 32))
        elif source_name == "vserver":
            server_name = data.get("hostname", "CS 1.6 Server")
            current_map = data.get("mapname", "unknown")
            players_count = int(data.get("players", 0))
            max_players = int(data.get("maxplayers", 32))
        else: # gs4u
            server_name = data.get("name", "CS 1.6 Server")
            current_map = data.get("map", "unknown")
            players_count = int(data.get("players", 0))
            max_players = int(data.get("maxplayers", 32))
            
        server_name = server_name.lstrip('0Оo○◦ \t')
        
        text = f"⚙️ Моніторинг {server_name}\n\n"
        text += f"🖥️ {server_name}\n"
        text += f"🌐 IP: {SERVER_IP}:{SERVER_PORT}\n"
        text += f"🗺️ Карта: {current_map}\n"
        text += f"👥 Гравці: {players_count}/{max_players}\n\n"
        
        # Спроба отримати список гравців (лише для першого API, бо інші його не завжди віддають)
        if source_name == "gamecms" and players_count > 0:
            try:
                players_url = "https://gamecms.org"
                players_resp = requests.get(players_url, timeout=4.0)
                if players_resp.status_code == 200:
                    players_data = players_resp.json().get("players", [])
                    players_data.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
                    
                    if players_data:
                        for idx, p in enumerate(players_data[:20], 1):
                            if idx == 1: emoji = "🥇"
                            elif idx == 2: emoji = "🥈"
                            elif idx == 3: emoji = "🥉"
                            else: emoji = "🎮"
                            name = p.get("name", "Гравець").strip()
                            if not name: name = "Підключення..."
                            frags = p.get("score", 0)
                            text += f"{emoji} {name} — {frags} вбивств\n"
                        return {"status": "online", "text": text}
            except Exception:
                pass
                
        # Стандартні заглушки для онлайну, якщо список гравців недоступний
        if players_count > 0:
            text += "🎮 _На сервері є гравці. Заходьте грати!_\n"
        else:
            text += "💤 _На сервері немає гравців._\n"
            
        return {"status": "online", "text": text}
        
    except Exception as e:
        return {"status": "error", "text": f"⚠️ *Помилка обробки*: Не вдалося розпарсити відповідь від {source_name}. ({str(e)})"}

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
    print("Telegram Multi-API bot started successfully...")
    bot.polling(none_stop=True)
    
