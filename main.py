import os
import telebot
from google import genai


BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '6996025306:AAFrVMSC-o6rA-CWof4u3roA3pDr6t1H4p4')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyAHhpJldughwEcIY5w0evRgRIz-unZ7-wE')

# Инициализация бота и API
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
client = genai.Client(api_key=GEMINI_API_KEY)
# System instruction in Russian for medical diagnosis
system_instruction = """
Здравствуйте, Я - чат-бот для медицинской диагностики. 
Расскажите мне о ваших симптомах, и я постараюсь предложить предварительный диагноз.
"""

# Dictionary to store conversations for each user
user_conversations = {}

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.from_user.id
    
    # Initialize conversation for new users
    if user_id not in user_conversations:
        user_conversations[user_id] = []
        
        # Send a welcome message to new users
        bot.send_message(message.chat.id, 
                         "Здравствуйте! Я - чат-бот для медицинской диагностики. Расскажите мне о ваших симптомах.")
    
    try:
        user_text = message.text
        
        # Create a simple prompt that includes conversation history
        prompt = system_instruction + "\n\nИстория диалога:\n"
        
        # Add conversation history
        for past_msg in user_conversations[user_id]:
            if past_msg['role'] == 'user':
                prompt += f"Пользователь: {past_msg['text']}\n"
            else:
                prompt += f"Ассистент: {past_msg['text']}\n"
        
        # Add current message
        prompt += f"Пользователь: {user_text}\n"
        prompt += "Ассистент: "
        
        
        # Generate response using proper config object
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048
            }
        )
        
        # Extract text from response
        if hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = "Извините, я не смог обработать ваш запрос."
        
        # Update conversation history
        user_conversations[user_id].append({'role': 'user', 'text': user_text})
        user_conversations[user_id].append({'role': 'assistant', 'text': response_text})
        
        # Limit history length to prevent tokens from growing too large
        if len(user_conversations[user_id]) > 10:
            user_conversations[user_id] = user_conversations[user_id][-10:]
        
        # Reply to the user
        bot.reply_to(message, response_text)
        
    except Exception as e:
        error_msg = str(e)
        # Truncate error message to prevent "message too long" errors
        if len(error_msg) > 100:
            error_msg = error_msg[:97] + "..."
        bot.reply_to(message, f"Произошла ошибка: {error_msg}")
        print(f"Error details: {str(e)}")
        import traceback
        print(traceback.format_exc())

# Start the bot
print("Bot is running...")
bot.infinity_polling()


if __name__ == "__main__":
    # Для Render нужно указать порт из переменной окружения
    port = int(os.environ.get('PORT', 8080))
    print(f"Bot is running on port {port}...")
    
    # Запускаем бота с веб-хуком на Render
    # Используем threading режим для обработки запросов
    import threading
    threading.Thread(target=bot.infinity_polling).start()
    
    # Запускаем простой веб-сервер, чтобы Render не останавливал сервис
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running')
    
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print("Web server started")
    server.serve_forever()
