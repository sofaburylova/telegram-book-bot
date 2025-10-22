import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Получаем токен из переменных окружения
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set!")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Создаем бота
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Обработчики команд
def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    update.message.reply_text(
        f"Привет, {user.first_name}! Я книжный бот. Чем могу помочь?"
    )

def help_command(update, context):
    """Обработчик команды /help"""
    help_text = """
Доступные команды:
/start - начать работу
/help - показать справку
    """
    update.message.reply_text(help_text)

def echo(update, context):
    """Эхо-обработчик для текстовых сообщений"""
    update.message.reply_text(f"Вы сказали: {update.message.text}")

# Регистрируем обработчики
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

# Webhook эндпоинт
@app.route('/webhook', methods=['POST'])
def webhook():
    """Эндпоинт для webhook от Telegram"""
    try:
        # Получаем обновление от Telegram
        update = Update.de_json(request.get_json(force=True), bot)
        
        # Обрабатываем обновление
        dispatcher.process_update(update)
        
        return 'ok'
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return 'error', 500

@app.route('/')
def home():
    """Главная страница для проверки работы"""
    return "Bot is running! Use /start in Telegram."

@app.route('/health')
def health():
    """Эндпоинт для проверки здоровья"""
    return 'OK'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Установка webhook (вызовите этот URL один раз)"""
    try:
        webhook_url = f"https://{request.host}/webhook"
        result = bot.set_webhook(webhook_url)
        return f"Webhook set to {webhook_url}: {result}"
    except Exception as e:
        return f"Error setting webhook: {e}"

@app.route('/remove_webhook', methods=['GET'])
def remove_webhook():
    """Удаление webhook"""
    try:
        result = bot.delete_webhook()
        return f"Webhook removed: {result}"
    except Exception as e:
        return f"Error removing webhook: {e}"

if __name__ == '__main__':
    # Получаем порт из переменных окружения (Render автоматически устанавливает PORT)
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем Flask приложение
    app.run(host='0.0.0.0', port=port, debug=False)