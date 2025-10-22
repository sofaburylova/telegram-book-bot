import logging
import sqlite3
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# --- КОНФИГУРАЦИЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_CHAT_ID = os.getenv('CHANNEL_CHAT_ID')

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения!")
if not CHANNEL_CHAT_ID:
    raise ValueError("❌ Не найден CHANNEL_CHAT_ID в переменных окружения!")

try:
    CHANNEL_CHAT_ID = int(CHANNEL_CHAT_ID)
except ValueError:
    raise ValueError("❌ CHANNEL_CHAT_ID должен быть числом!")

print(f"✅ Конфигурация загружена. Chat ID: {CHANNEL_CHAT_ID}")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('channel_posts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            hashtags TEXT,
            title TEXT,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных создана/проверена")

def add_post_to_db(message_id, hashtags, title, category):
    conn = sqlite3.connect('channel_posts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM posts WHERE message_id = ?', (message_id,))
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO posts (message_id, hashtags, title, category)
            VALUES (?, ?, ?, ?)
        ''', (message_id, hashtags, title, category))
        conn.commit()
        print(f"✅ Добавлен в БД: {category} - {title} (ID: {message_id})")
    conn.close()

def get_random_post(category):
    conn = sqlite3.connect('channel_posts.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT message_id, title FROM posts 
        WHERE category = ? 
        ORDER BY RANDOM() 
        LIMIT 1
    ''', (category,))
    result = cursor.fetchone()
    conn.close()
    return result

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🎬 Фильм", callback_data='category_фильмы')],
        [InlineKeyboardButton("📺 Сериал", callback_data='category_сериалы')],
        [InlineKeyboardButton("📚 Книга", callback_data='category_книги')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Привет! Я помогу выбрать, что посмотреть или почитать. Выбери категорию:',
        reply_markup=reply_markup
    )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    category = query.data.split('_')[1]
    random_post = get_random_post(category)
    
    if random_post:
        message_id, title = random_post
        channel_link = f"https://t.me/c/{str(CHANNEL_CHAT_ID)[4:]}/{message_id}"
        query.edit_message_text(
            text=f"<b>🎉 Ваша рекомендация:</b>\n\n<a href='{channel_link}'>{title}</a>",
            parse_mode='HTML'
        )
    else:
        query.edit_message_text(
            text=f"😔 В категории '{category}' пока ничего нет. Используйте /manual для инструкций!"
        )

def debug_command(update: Update, context: CallbackContext):
    conn = sqlite3.connect('channel_posts.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) FROM posts GROUP BY category")
    results = cursor.fetchall()
    total = sum(count for _, count in results)
    if results:
        message = f"📊 Всего постов в БД: {total}\n" + "\n".join([f"• {cat}: {count}" for cat, count in results])
    else:
        message = "📊 В базе данных пока нет постов\nИспользуйте /manual для инструкций"
    conn.close()
    update.message.reply_text(message)

def manual_add_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📝 Чтобы добавить пост вручную:\n\n"
        "1. Найди пост в канале и скопируй ссылку на него\n"
        "2. Из ссылки возьми ID сообщения (последнее число)\n"
        "3. Пришли команду:\n"
        "<code>/add ID #категория Название</code>\n\n"
        "🔹 Примеры:\n"
        "<code>/add 123 #книги Между нами горы</code>\n"
        "<code>/add 456 #фильмы Интересный фильм</code>",
        parse_mode='HTML'
    )

def add_post_command(update: Update, context: CallbackContext):
    if not context.args or len(context.args) < 3:
        update.message.reply_text(
            "❌ Неправильный формат. Используйте:\n"
            "<code>/add ID #категория Название</code>\n\n"
            "Пример:\n"
            "<code>/add 123 #книги Между нами горы</code>",
            parse_mode='HTML'
        )
        return
    try:
        message_id = int(context.args[0])
        category_hashtag = context.args[1].lower()
        title = ' '.join(context.args[2:])
        if category_hashtag == '#книги':
            category = 'книги'
        elif category_hashtag == '#фильмы':
            category = 'фильмы'
        elif category_hashtag == '#сериалы':
            category = 'сериалы'
        else:
            update.message.reply_text("❌ Используйте #книги, #фильмы или #сериалы")
            return
        add_post_to_db(message_id, category_hashtag, title, category)
        update.message.reply_text(f"✅ Добавлено: {category} - {title}\nID: {message_id}")
    except ValueError:
        update.message.reply_text("❌ ID сообщения должен быть числом")

def channel_post_handler(update: Update, context: CallbackContext):
    """Обрабатывает новые посты из канала"""
    message = update.channel_post
    if message and message.text:
        text = message.text
        lines = text.split('\n')
        
        hashtags = None
        title = None
        category = None

        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith('#книги'):
                category = 'книги'
                hashtags = line
            elif line_lower.startswith('#фильмы'):
                category = 'фильмы'
                hashtags = line
            elif line_lower.startswith('#сериалы'):
                category = 'сериалы'
                hashtags = line
            elif line and not line.startswith('#') and not title:
                title = line.strip()

        if category and title and hashtags:
            add_post_to_db(message.message_id, hashtags, title, category)
            logger.info(f"✅ Добавлен пост: {category} - {title}")

def main():
    print("🔄 Запуск бота...")
    
    init_db()
    
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("debug", debug_command))
    dispatcher.add_handler(CommandHandler("manual", manual_add_command))
    dispatcher.add_handler(CommandHandler("add", add_post_command))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.chat_type.channel, channel_post_handler))

    print("✅ Бот запущен! Нажмите Ctrl+C для остановки")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()