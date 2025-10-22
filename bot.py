import os
import logging
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

# Обработчики команд
async def start(update, context):
    await update.message.reply_text('Привет! Я книжный бот. Чем могу помочь?')

async def help_command(update, context):
    await update.message.reply_text('Помощь: /start - начать работу')

async def echo(update, context):
    await update.message.reply_text(f'Вы сказали: {update.message.text}')

def run_bot():
    """Запуск бота в режиме polling"""
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN not set! Please check environment variables.")
        return
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        logging.info("Bot started successfully in polling mode!")
        application.run_polling()
    except Exception as e:
        logging.error(f"Error starting bot: {e}")

@app.route('/')
def home():
    return "Bot is running! Check logs for status."

@app.route('/health')
def health():
    return 'OK'

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    logging.info("Starting bot thread...")
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    logging.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)