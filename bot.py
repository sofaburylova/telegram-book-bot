import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я книжный бот. Чем могу помочь?"
    )

async def echo(update, context):
    """Ответ на текстовые сообщения"""
    await update.message.reply_text(f"Вы написали: {update.message.text}")

def main():
    """Основная функция запуска бота"""
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    try:
        # Создаем и настраиваем приложение
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        logger.info("Бот запускается...")
        
        # Запускаем polling
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == '__main__':
    main()