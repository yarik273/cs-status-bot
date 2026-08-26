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
    """Отримує реальний онлайн через пряму IP-адресу API в обхід зламаного DNS на Railway"""
    try:
        # Замість vserver.space використовуємо пряму IP-адресу сервера моніторингу: 92.53.65.250
        # Передаємо заголовок Host, щоб веб-сервер моніторингу зрозумів запит
        url = "https://92.53.65"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Host": "vserver.space"  # Обов'язково для роботи через прямий IP
        }
        
        # Вимикаємо перевірку SSL (verify=False), оскільки сертифікат випущено на домен, а ми йдемо по IP
        response = requests.get(url, headers=headers, timeout=8.0, verify=False)
        data = response.json()
        
        if not data or data.get("status") == "offline" or data.get("online") is False:
            return {"status": "offline", "text": f"🔴 *Статус сервера*: OFFLINE ❌\n\nСервер {SERVER_IP}:{SERVER_PORT} зараз недоступний."}
            
        # Зчитуємо чисті дані сервера
        server_name = data.get("hostname", data.get("name", "VOLYNSKIY_PUBLIC")).lstrip('0Оo○◦ \t')
        current_map = data.get("mapname", data.get("map", "de_dust2"))
        players_count = int(data.get("players", data.get("players_online", 0)))
        max_players = int(data.get("maxplayers", data.get("max_players", 32)))
        
        text = f"⚙️ Моніторинг {server_name}\n\n"
        text += f"🖥️ {server_name}\n"
        text += f"🌐 IP: {SERVER_IP}:{SERVER_PORT}\n"
        text += f"🗺️ Карта: {current_map}\n"
        text += f"👥 Гравці: {players_count}/{max_players}\n\n"
        
        if players_count > 0:
            text += f"🎮 _На сервері зараз грає {players_count} людей. Приєднуйтесь!_"
        else:
            text += "💤 _На сервері зараз немає гравців. Станьте першим!_"
            
        return {"status": "online", "text": text}
        
    except Exception as e:
        # Якщо навіть прямий IP видасть збій, виводимо помилку для точного аналізу
        return {
            "status": "online", 
            "text": f"⚙️ Моніторинг VOLYNSKIY_PUBLIC\n\n🖥️ VOLYNSKIY_PUBLIC [UA]\n🌐 IP: {SERVER_IP}:{SERVER_PORT}\n🗺️ Карта: Не вдалося оновити\n👥 Гравці: Помилка отримання даних ❌\n\n⚠️ Помилка: {str(e)}"
        }

@bot.message_handler(commands=['info', 'server'])
def send_cs_status(message):
    data = get_cs_status_via_api()
    MAIN_BANNER_ID = "AgACAgIAAxkBAAOgak6BkYsMaEy0JS3SUaoIQmyWCoAAAv8caxvTMHBKqvUcUE0TuaIBAAMCAAN5AAM8BA"
    thread_id = message.message_thread_id
    
    try:
        bot.send_photo(chat_id=message.chat.id, photo=MAIN_BANNER_ID, caption=data["text"], message_thread_id=thread_id)
    except Exception:
        bot.send_message(chat_id=message.chat.id, text=data["text"], message_thread_id=thread_id, reply_to_message_id=message.message_id)

if __name__ == "__main__":
    # Тимчасово вимикаємо попередження від urllib3 про вимкнений verify=False, щоб не засмічувати логи
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram IP-Direct Bot started successfully...")
    bot.polling(none_stop=True)
    
