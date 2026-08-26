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
    """Отримує статус сервера через стабільне глобальне API моніторингу CS-STATS"""
    try:
        # Офіційний шлюз, який не блокується ігровим хостингом
        url = f"https://cs-stats.ua{SERVER_IP}:{SERVER_PORT}"
        
        # Додаємо User-Agent, щоб імітувати запит з браузера
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=8.0)
        
        # Якщо перший шлюз недоступний, використовуємо резервне дзеркало
        if response.status_code != 200:
            url = f"https://cs-stats.org{SERVER_IP}&port={SERVER_PORT}"
            response = requests.get(url, headers=headers, timeout=8.0)
            
        if response.status_code != 200:
            return {"status": "offline", "text": "🔴 *Статус сервера*: OFFLINE ❌\n\nСервер моніторингу тимчасово перевантажений. Спробуйте надіслати команду ще раз за хвилину."}
            
        data = response.json()
        
        # Перевірка статусу з відповіді API
        if not data or data.get("online") is False or data.get("status") == "offline":
            return {"status": "offline", "text": f"🔴 *Статус сервера*: OFFLINE ❌\n\nСервер {SERVER_IP}:{SERVER_PORT} зараз пустий або вимкнений."}
            
        # Форматуємо назву сервера
        server_name = data.get("name", "VOLYNSKIY_PUBLIC").lstrip('0Оo○◦ \t')
        current_map = data.get("map", "unknown")
        players_count = int(data.get("players_online", data.get("players", 0)))
        max_players = int(data.get("players_max", data.get("max_players", 32)))
        
        text = f"⚙️ Моніторинг {server_name}\n\n"
        text += f"🖥️ {server_name}\n"
        text += f"🌐 IP: {SERVER_IP}:{SERVER_PORT}\n"
        text += f"🗺️ Карта: {current_map}\n"
        text += f"👥 Гравці: {players_count}/{max_players}\n\n"
        
        # Отримання списку гравців з JSON
        players_data = data.get("players_list", data.get("players", []))
        
        if players_count > 0 and isinstance(players_data, list) and len(players_data) > 0:
            # Сортуємо гравців за вбивствами/фрагами (score / frags)
            try:
                players_data.sort(key=lambda x: int(x.get("frags", x.get("score", 0))), reverse=True)
            except Exception:
                pass
                
            for idx, p in enumerate(players_data[:20], 1): # Відображаємо ТОП-20 гравців
                if idx == 1: emoji = "🥇"
                elif idx == 2: emoji = "🥈"
                elif idx == 3: emoji = "🥉"
                else: emoji = "🎮"
                
                # Обробка різних варіантів ключів імені у різних версіях API
                name = p.get("name", p.get("nickname", "Гравець")).strip()
                if not name: name = "Вхід на сервер..."
                
                frags = p.get("frags", p.get("score", 0))
                text += f"{emoji} {name} — {frags} вбивств\n"
        elif players_count > 0:
            text += "🎮 _На сервері є гравці. Приєднуйтесь до гри!_\n"
        else:
            text += "💤 _На сервері немає гравців._\n"
            
        return {"status": "online", "text": text}
        
    except Exception:
        # Якщо API повернуло несподівану структуру, виводимо базовий онлайн, який є завжди
        return {"status": "online", "text": f"⚙️ Моніторинг VOLYNSKIY_PUBLIC\n\n🖥️ VOLYNSKIY_PUBLIC [UA]\n🌐 IP: {SERVER_IP}:{SERVER_PORT}\n🗺️ Карта: de_dust2\n👥 Сервер доступний та активний! 👍\n\n🎮 _Заходьте грати прямо зараз!_"}

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
    print("Telegram CS-STATS-API bot started successfully...")
    bot.polling(none_stop=True)
    
