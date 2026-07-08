import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- 2. ДАНІ ВАШОГО БОТА І СЕРВЕРА ---
TOKEN = "8653250290:AAHfh7P94TajZXwVbLzPKKJywahtoKdszno"
SERVER_IP = "91.211.118.90"
SERVER_PORT = 27036

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# --- 3. ФУНКЦІЯ ОТРИМАННЯ ДАНИХ (ОНЛАЙН + НІКНЕЙМИ) ---
def get_cs_detailed_status():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(3.5)
        
        # Запит інформації про сервер (A2S_INFO)
        client.sendto(b'\xFF\xFF\xFF\xFFTSource Engine Query\x00', (SERVER_IP, SERVER_PORT))
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
            
        payload = payload[2:]
        players_count = payload if len(payload) >= 1 else 0
        max_players = payload if len(payload) >= 2 else 0
        
        # Блок отримання нікнеймів гравців (A2S_PLAYER)
        player_names = []
        if players_count > 0:
            try:
                client.sendto(b'\xFF\xFF\xFF\xFF\x55\xFF\xFF\xFF\xFF', (SERVER_IP, SERVER_PORT))
                data_ch, _ = client.recvfrom(4096)
                if len(data_ch) >= 9:
                    challenge = data_ch[5:9]
                    client.sendto(b'\xFF\xFF\xFF\xFF\x55' + challenge, (SERVER_IP, SERVER_PORT))
                    data_pl, _ = client.recvfrom(4096)
                    pl_payload = data_pl[6:]
                    while len(pl_payload) > 0:
                        pl_payload = pl_payload[1:]
                        name_end = pl_payload.find(b'\x00')
                        if name_end == -1: break
                        name = pl_payload[:name_end].decode('utf-8', errors='ignore').strip()
                        pl_payload = pl_payload[name_end + 1:]
                        pl_payload = pl_payload[8:]
                        if name and not name.startswith('HLTV'):
                            player_names.append(name)
            except:
                pass

        # Формування красивого великого тексту
        text = f"🇺🇦 *{server_name}*\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🟢 *СТАТУС СЕРВЕРА:* ОНЛАЙН\n\n"
        text += f"🗺 *Поточна карта:* {current_map}\n"
        text += f"👥 *Гравці на сервері:* *{players_count}/{max_players}*\n"
        text += f"🔗 *Айпі для підключення:* {SERVER_IP}:{SERVER_PORT}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if player_names:
            text += f"👤 *СПИСОК ГРАВЦІВ В ОНЛАЙНІ ({len(player_names)}):*\n"
            for i, name in enumerate(player_names, 1):
                text += f" {i}.  * {name} *\n"
        elif players_count > 0:
            text += f"👤 *СПИСОК ГРАВЦІВ:*\n_Гравці підключаються або оновлюються..._\n"
        else:
            text += f"💤 *СПИСОК ГРАВЦІВ:*\n_На сервері зараз немає гравців. Заходь грати!_\n"
            
        text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📢 *Щоб оновити, тисни знову* ➡️ /info"
        return text
    except:
        text = f"🔴 *СТАТУС СЕРВЕРА:* ОФЛАЙН\n\n❌ Сервер зараз недоступний або вимкнений.\nПеревірте працездатність хостингу."
        return text
# --- 4. ОБРОБКА КОМАНДИ /info ---
@bot.message_handler(commands=['info'])
def send_cs_status(message):
    status_text = get_cs_detailed_status()
    bot.reply_to(message, status_text, parse_mode="Markdown")

# --- 5. ЗАПУСК БОТА ТА ВЕБ-СЕРВЕРА ---
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True)
