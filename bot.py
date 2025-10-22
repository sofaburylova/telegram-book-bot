import logging
import sqlite3
import random
import os
import requests
import time

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_CHAT_ID = os.getenv('CHANNEL_CHAT_ID')

if not BOT_TOKEN or not CHANNEL_CHAT_ID:
    raise ValueError("❌ Не найдены переменные окружения!")

print(f"✅ Конфигурация загружена. Chat ID: {CHANNEL_CHAT_ID}")

# --- База данных ---
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
        print(f"✅ Добавлен в БД: {category} - {title}")
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

# --- Telegram API ---
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = reply_markup
    response = requests.post(url, json=data)
    return response.json()

def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = reply_markup
    response = requests.post(url, json=data)
    return response.json()

def answer_callback_query(callback_query_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    data = {'callback_query_id': callback_query_id}
    requests.post(url, json=data)

# --- Обработка команд ---
def handle_start(chat_id):
    keyboard = {
        'inline_keyboard': [
            [{'text': '🎬 Фильм', 'callback_data': 'category_фильмы'}],
            [{'text': '📺 Сериал', 'callback_data': 'category_сериалы'}],
            [{'text': '📚 Книга', 'callback_data': 'category_книги'}]
        ]
    }
    send_message(chat_id, 'Привет! Выбери категорию:', keyboard)

def handle_button(chat_id, message_id, callback_data):
    answer_callback_query(callback_data['id'])
    category = callback_data['data'].split('_')[1]
    
    random_post = get_random_post(category)
    if random_post:
        message_id, title = random_post
        channel_link = f"https://t.me/c/{str(CHANNEL_CHAT_ID)[4:]}/{message_id}"
        text = f"<b>🎉 Ваша рекомендация:</b>\n\n<a href='{channel_link}'>{title}</a>"
    else:
        text = f"😔 В категории '{category}' пока ничего нет. Используйте /add чтобы добавить посты!"
    
    edit_message(chat_id, message_id, text)

def handle_debug(chat_id):
    conn = sqlite3.connect('channel_posts.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) FROM posts GROUP BY category")
    results = cursor.fetchall()
    total = sum(count for _, count in results)
    
    if results:
        message = f"📊 Всего постов в БД: {total}\n" + "\n".join([f"• {cat}: {count}" for cat, count in results])
    else:
        message = "📊 В базе данных пока нет постов\nИспользуйте /add чтобы добавить"
    
    conn.close()
    send_message(chat_id, message)

def handle_manual(chat_id):
    text = (
        "📝 Чтобы добавить пост вручную:\n\n"
        "1. Найди пост в канале и скопируй ссылку на него\n"
        "2. Из ссылки возьми ID сообщения (последнее число)\n"
        "3. Пришли команду:\n"
        "<code>/add ID #категория Название</code>\n\n"
        "🔹 Примеры:\n"
        "<code>/add 123 #книги Между нами горы</code>\n"
        "<code>/add 456 #фильмы Интересный фильм</code>"
    )
    send_message(chat_id, text)

def handle_add(chat_id, args):
    if len(args) < 3:
        send_message(chat_id, "❌ Используйте: /add ID #категория Название")
        return
    
    try:
        message_id = int(args[0])
        category_hashtag = args[1].lower()
        title = ' '.join(args[2:])
        
        if category_hashtag == '#книги':
            category = 'книги'
        elif category_hashtag == '#фильмы':
            category = 'фильмы'
        elif category_hashtag == '#сериалы':
            category = 'сериалы'
        else:
            send_message(chat_id, "❌ Используйте #книги, #фильмы или #сериалы")
            return
        
        add_post_to_db(message_id, category_hashtag, title, category)
        send_message(chat_id, f"✅ Добавлено: {category} - {title}")
        
    except ValueError:
        send_message(chat_id, "❌ ID сообщения должен быть числом")

# --- Главный цикл ---
def process_update(update):
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        if text.startswith('/start'):
            handle_start(chat_id)
        elif text.startswith('/debug'):
            handle_debug(chat_id)
        elif text.startswith('/manual'):
            handle_manual(chat_id)
        elif text.startswith('/add'):
            args = text.split()[1:]
            handle_add(chat_id, args)
            
    elif 'callback_query' in update:
        callback = update['callback_query']
        chat_id = callback['message']['chat']['id']
        message_id = callback['message']['message_id']
        handle_button(chat_id, message_id, callback)

def main():
    print("🔄 Запуск бота...")
    init_db()
    print("✅ Бот запущен!")
    
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {'offset': offset, 'timeout': 30}
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    for update in data['result']:
                        process_update(update)
                        offset = update['update_id'] + 1
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()