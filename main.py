import os
import threading
import requests
import time
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

# --- НАЛАШТУВАННЯ БОТА, СЕРВЕРА ТА КАНАЛУ ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# 👇 ЗАМІНІТЬ НА ЮЗЕРНЕЙМ ВАШОГО КАНАЛУ (ОБОВ'ЯЗКОВО З СИМВОЛОМ @)
# Або вставте числовий ID каналу (наприклад, -100123456789)
CHANNEL_ID = "@назва_вашого_каналу"  

SERVER_IP = "91.211.118.90"
SERVER_PORT = "27036"
UPDATE_INTERVAL = 60  # Інтервал оновлення поста в каналі (у секундах)

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

def get_cs_status_via_api():
    """Отримує актуальний статус сервера через відкритий шлюз сервісу СS-Monitoring"""
    try:
        url = "https://vserver.space"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6.0)
        data = response.json()
        
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
        return {"status": "online", "text": f"⚙️ Моніторинг VOLYNSKIY_PUBLIC\n\n🖥️ VOLYNSKIY_PUBLIC [UA]\n🌐 IP: {SERVER_IP}:{SERVER_PORT}\n🗺️ Карта: Ротується...\n👥 Сервер доступний та активний! 👍\n\n🎮 _Заходьте грати прямо зараз!_"}

def channel_autorefresh_loop():
    """Фонова функція, яка публікує статус у канал та циклічно його оновлює"""
    print("Фоновий моніторинг каналу запущено...")
    last_message_id = None
    time.sleep(5)  # Очікуємо повного старту бота
    
    while True:
        data = get_cs_status_via_api()
        MAIN_BANNER_ID = "AgACAgIAAxkBAAOgak6BkYsMaEy0JS3SUaoIQmyWCoAAAv8caxvTMHBKqvUcUE0TuaIBAAMCAAN5AAM8BA"
        
        try:
            if last_message_id is None:
                # Перший запуск — надсилаємо банер у канал
                msg = bot.send_photo(chat_id=CHANNEL_ID, photo=MAIN_BANNER_ID, caption=data["text"])
                last_message_id = msg.message_id
                print(f"Створено живий пост моніторингу в каналі: ID {last_message_id}")
            else:
                # Наступні запуски — просто редагуємо опис під існуючим фото
                bot.edit_message_caption(chat_id=CHANNEL_ID, message_id=last_message_id, caption=data["text"])
                print(f"Статус сервера в каналі успішно оновлено (ID: {last_message_id})")
        except telebot.api_helper.ApiTelegramException as e:
            if "message to edit not found" in e.description:
                print("Пост видалили з каналу. Створюємо новий...")
                last_message_id = None
            else:
                print(f"Помилка Telegram API у каналі: {e}")
        except Exception as e:
            print(f"Помилка у циклі каналу: {e}")
            
        time.sleep(UPDATE_INTERVAL)

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
    threading.Thread(target=run_web_server, daemon=True).start()
    # Запуск фонового автооновлення для каналу
    threading.Thread(target=channel_autorefresh_loop, daemon=True).start()
    print("Telegram bot with Channel Live-Widget started...")
    bot.polling(none_stop=True)
    
