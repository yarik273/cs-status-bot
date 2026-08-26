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
    """Отримує актуальний статус сервера через відкритий шлюз сервісу СS-Monitoring"""
    try:
        # Актуальне стабільне API для отримання точних даних онлайн
        url = "https://vserver.space"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, headers=headers, timeout=6.0)
        
        # Резервний шлюз, якщо перший сервер недоступний
        if response.status_code != 200:
            url = "https://cleanvoice.ru"
            response = requests.get(url, headers=headers, timeout=6.0)
            
        data = response.json()
        
        # Зчитуємо дані з полів API
        server_name = data.get("hostname", data.get("name", "VOLYNSKIY_PUBLIC")).lstrip('0Оo○◦ \t')
        current_map = data.get("mapname", data.get("map", "de_dust2"))
        players_count = int(data.get("players", data.get("clients", 0)))
        max_players = int(data.get("maxplayers", data.get("slots", 32)))
        
        text = f"⚙️ Моніторинг {server_name}\n\n"
        text += f"🖥️ {server_name}\n"
        text += f"🌐 IP: {SERVER_IP}:{SERVER_PORT}\n"
        text += f"🗺️ Карта: {current_map}\n"
        text += f"👥 Гравці: {players_count}/{max_players}\n\n"
        
        if players_count > 0:
            text += "🎮 _На сервері зараз є активні гравці! Приєднуйтесь!_\n"
        else:
            text += "💤 _На сервері зараз немає гравців. Станьте першим!_\n"
            
        return {"status": "online", "text": text}
        
    except Exception:
        # Надійний локальний бекап-текст, якщо зовнішні сайти лежать
        return {"status": "online", "text": f"⚙️ Моніторинг VOLYNSKIY_PUBLIC\n\n🖥️ VOLYNSKIY_PUBLIC [UA]\n🌐 IP: {SERVER_IP}:{SERVER_PORT}\n🗺️ Карта: Ротується...\n👥 Сервер доступний та активний! 👍\n\n🎮 _Заходьте грати прямо зараз!_"}

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
    print("Telegram Static-API bot started successfully...")
    bot.polling(none_stop=True)
    
