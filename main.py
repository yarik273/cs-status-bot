    markup = telebot.types.InlineKeyboardMarkup()
    connect_url = f"steam://connect/{SERVER_IP}:{SERVER_PORT}"
    
    btn_connect = telebot.types.InlineKeyboardButton(text="🎮 Підключитися", url=connect_url)
    btn_refresh = telebot.types.InlineKeyboardButton(text="🔄 Оновити статус", callback_data="refresh_status")
    
    markup.add(btn_connect)
    markup.add(btn_refresh)
    
    # Вибираємо картинку карти
    map_clean = data["map"].lower().strip()
    photo_url = MAP_IMAGES.get(map_clean, MAP_IMAGES["default"])
    
    return text, markup, photo_url

# Обробник, який розуміє всі варіанти команди (з рискою і без)
@bot.message_handler(func=lambda msg: msg.text in ['/info', 'info', '/info@cs16_status_server_bot', 'info@cs16_status_server_bot'])
def send_cs_status(message):
    text, markup, photo_url = generate_status_message_and_keyboard()
    try:
        bot.send_photo(message.chat.id, photo_url, caption=text, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_status")
def callback_inline(call):
    text, markup, photo_url = generate_status_message_and_keyboard()
    try:
        # Редагуємо картинку та текст прямо на місці
        media = telebot.types.InputMediaPhoto(photo_url, caption=text, parse_mode="Markdown")
        bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=media, reply_markup=markup)
    except Exception:
        pass
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Telegram bot started successfully...")
    bot.polling(none_stop=True)
