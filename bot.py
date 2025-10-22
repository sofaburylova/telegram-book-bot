import os
import logging
import threading
import asyncio
from flask import Flask
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Обработчики команд
async def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я книжный бот. Чем могу помочь?"
    )

async def help_command(update, context):
    """Обработчик команды /help"""
    help_text = """
Доступные команды:
/start - начать работу
/help - показать справку
    """
    await update.message.reply_text(help_text)

async def echo(update, context):
    """Эхо-обработчик для текстовых сообщений"""
    await update.message.reply_text(f"Вы сказали: {update.message.text}")

def run_bot():
    """Запуск бота в режиме polling"""
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    try:
        # Создаем приложение
        application = Application.builder().token(TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        logger.info("Бот запускается в режиме polling...")
        
        # Запускаем бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

@app.route('/')
def home():
    return "Бот работает! Напишите /start в Telegram."

@app.route('/health')
def health():
    return 'OK'

def run_flask():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Запускаем Flask в основном потоке
    run_flask()