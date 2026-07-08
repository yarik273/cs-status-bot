import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from valve.source.a2s import ServerQuerier

# Ñïåöèàëüíûé âåá-ñåðâåð äëÿ ïðîõîæäåíèÿ ïðîâåðêè Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    # Render ïåðåäàåò ïîðò â ïåðåìåííûå ñðåäû, áåðåì åãî èëè ñòàíäàðòíûé 10000
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(# Ðåæèì ëîãèðîâàíèÿ äëÿ Render
          f"Web server started on port {port}")
    server.serve_forever()

# --- ÄÀÍÍÛÅ ÂÀØÅÃÎ ÁÎÒÀ È ÑÅÐÂÅÐÀ ---
TOKEN = "8653250290:AAFWG3CdV7-0ryk1s_XgfX6ePctQ67CTZ-E"
SERVER_IP = "91.211.118.90"
SERVER_PORT = 27036

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['info'])
def send_cs_status(message):
    try:
        with ServerQuerier((SERVER_IP, int(SERVER_PORT))) as server:
            info = server.info()
            text = f"?? *Ñòàòóñ ñåðâåðà CS 1.6*:\n\n"
            text += f"?? Íàçâà: {info['server_name']}\n"
            text += f"??? Êàðòà: {info['map_name']}\n"
            text += f"?? Ãðàâö³: {info['player_count']}/{info['max_players']}\n"
            bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "? Ñåðâåð çàðàç íåäîñòóïíèé àáî âèìêíåíèé.")

if name == "main":
    # Çàïóñêàåì âåá-ñåðâåð, êîòîðûé òðåáóåò Render äëÿ ñòàòóñà Live
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Çàïóñêàåì ñàìîãî áîòà Telegram
    print("Telegram bot started...")
    bot.polling(none_stop=True)
