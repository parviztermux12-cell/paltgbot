import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
import logging
import json
import os
import re
import zipfile
import asyncio
import aiohttp
from datetime import datetime, date, timedelta
from io import BytesIO
import threading

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8709660042:AAFqXswl8OwE1qewm4KMrQVgDMjV34iTro4"
PAYMENT_PROVIDER_TOKEN = ""

CEREBRAS_API_KEYS = [
    "csk-fek5v5dn9cxj853hfk9cw3hvc24wwn3ddme63tmet8w96dmw",
    "csk-yh2rcf28e6tv9t9tfeynhd5xmfep8xcyc446h3tj3y5yc64j"
]
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODEL = "llama3.1-8b"

REQUIRED_CHANNEL_ID = -1003851572008
REQUIRED_CHANNEL_LINK = "https://t.me/izzzy_vpn"

# Лимиты
DAILY_BOTS_LIMIT = 2  # обычный пользователь
DAILY_BOTS_LIMIT_VIP = 30  # VIP
VIP_PRICES = {"week": 100, "month": 300, "year": 1800}  # Цены в Telegram Stars

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# ===== ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ =====
user_data_file = "codespace_users.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

user_data = load_json(user_data_file)

def save_all():
    save_json(user_data_file, user_data)

def get_user(user_id):
    uid = str(user_id)
    if uid not in user_data:
        user_data[uid] = {
            "bots_today": 0,
            "total_bots": 0,
            "last_reset_date": str(date.today()),
            "vip_until": None,
            "current_key_index": 0
        }
    
    if user_data[uid]["last_reset_date"] != str(date.today()):
        user_data[uid]["bots_today"] = 0
        user_data[uid]["last_reset_date"] = str(date.today())
        save_all()
    
    if user_data[uid].get("vip_until"):
        vip_until = datetime.fromisoformat(user_data[uid]["vip_until"])
        if vip_until < datetime.now():
            user_data[uid]["vip_until"] = None
            save_all()
    
    return user_data[uid]

def get_daily_limit(user_id):
    user = get_user(user_id)
    return DAILY_BOTS_LIMIT_VIP if user.get("vip_until") else DAILY_BOTS_LIMIT

def get_max_bots_per_day(user_id):
    user = get_user(user_id)
    return DAILY_BOTS_LIMIT_VIP if user.get("vip_until") else DAILY_BOTS_LIMIT

# ===== ПРОВЕРКА ПОДПИСКИ =====
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ===== ЗАПРОС К CEREBRAS =====
async def cerebras_request(messages, user_id=None, max_tokens=2000, temperature=0.7):
    if user_id:
        user = get_user(user_id)
        start_index = user.get("current_key_index", 0)
    else:
        start_index = 0

    for attempt in range(len(CEREBRAS_API_KEYS)):
        key_index = (start_index + attempt) % len(CEREBRAS_API_KEYS)
        api_key = CEREBRAS_API_KEYS[key_index]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    CEREBRAS_URL,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": CEREBRAS_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if user_id:
                            user["current_key_index"] = key_index
                            save_all()
                        return result["choices"][0]["message"]["content"]
                    elif response.status == 429:
                        await asyncio.sleep(1)
                        continue
        except Exception as e:
            logger.error(f"Ошибка Cerebras: {e}")
            continue
    return None

# ===== ГЕНЕРАЦИЯ КОДА БОТА =====
async def generate_bot_code(description: str, user_id: int) -> dict:
    """Генерирует полный код Telegram бота на Python"""
    
    prompt = f"""Ты профессиональный разработчик Telegram ботов на Python. 
Создай телеграм бота по описанию: "{description}"

Требования:
1. Используй библиотеку python-telegram-bot (версия 20.x)
2. Раздели код на модули:
   - main.py (главный файл)
   - config.py (настройки)
   - handlers/ (обработчики команд и сообщений)
   - keyboards/ (клавиатуры и кнопки)
   - utils/ (вспомогательные функции)
   - database/ (работа с БД)
   - logs/ (логирование)

3. Добавь базу данных SQLite с примером использования
4. Добавь инструкцию по установке и запуску (README.md)
5. Добавь файл requirements.txt со всеми зависимостями
6. Код должен быть чистым, с комментариями на русском
7. Добавь обработку ошибок и логирование

Верни ответ в формате JSON:
{{
    "bot_name": "Название бота",
    "description": "Краткое описание",
    "files": {{
        "main.py": "код",
        "config.py": "код",
        "handlers/start.py": "код",
        "keyboards/menu.py": "код",
        "utils/helpers.py": "код",
        "database/db.py": "код",
        "requirements.txt": "зависимости",
        "README.md": "инструкция"
    }}
}}

Код должен быть рабочим и профессиональным."""

    messages = [
        {"role": "system", "content": "Ты эксперт по разработке Telegram ботов. Отвечай только валидным JSON. Весь код пиши на Python."},
        {"role": "user", "content": prompt}
    ]
    
    response = await cerebras_request(messages, user_id, max_tokens=8000, temperature=0.7)
    
    if response:
        try:
            response = re.sub(r'```json\n?', '', response)
            response = re.sub(r'```\n?', '', response)
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON ошибка: {e}")
            return None
    return None

# ===== СОЗДАНИЕ ZIP АРХИВА =====
def create_zip_project(files: dict) -> BytesIO:
    """Создает ZIP архив с проектом бота"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filepath, content in files.items():
            zip_file.writestr(filepath, content)
    
    zip_buffer.seek(0)
    return zip_buffer

# ===== ОБРАБОТЧИКИ TELEBOT =====
def send_main_menu(message):
    """Отправляет главное меню"""
    user_id = message.from_user.id
    user = get_user(user_id)
    daily_limit = get_daily_limit(user_id)
    used_today = user["bots_today"]
    
    vip_status = "✅ VIP" if user.get("vip_until") else "❌ Бесплатный"
    if user.get("vip_until"):
        vip_status += f"\nдо {datetime.fromisoformat(user['vip_until']).strftime('%d.%m.%Y')}"
    
    text = f"""✨ <b>Izzzy CodeSpace v5</b> ✨

🤖 <b>Генератор Telegram ботов на Python</b>

📊 <b>Твоя статистика:</b>
• Сегодня создано: {used_today}/{daily_limit} ботов
• Всего создано: {user['total_bots']}
• Статус: {vip_status}

💡 <b>Как работает:</b>
Напиши описание бота, который хочешь создать, например:
«Создай бота для погоды с уведомлениями»

Я сгенерирую:
✅ Полный код бота с разделением на модули
✅ Базу данных SQLite
✅ Инструкцию по установке
✅ Файл requirements.txt

🎁 <b>Бонус:</b> Инструкция где бесплатно залить бота!

⭐ Купи VIP для увеличения лимита до {DAILY_BOTS_LIMIT_VIP} ботов в день!"""

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Создать бота", callback_data="create_bot"),
        InlineKeyboardButton("⭐ VIP статус", callback_data="vip_menu")
    )
    keyboard.add(
        InlineKeyboardButton("📊 Мой профиль", callback_data="profile"),
        InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    
    bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📢 Подписаться на канал", url=REQUIRED_CHANNEL_LINK))
        bot.send_message(
            message.chat.id,
            f"✨ <b>Izzzy CodeSpace v5</b> ✨\n\n"
            f"🤖 Я генерирую телеграм ботов на Python по твоему описанию!\n\n"
            f"❌ <b>Для использования бота необходимо подписаться на канал!</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    text = f"""✨ <b>Izzzy CodeSpace v5</b> ✨

🤖 <b>Генератор Telegram ботов на Python</b>

💡 <b>Как работает:</b>
Просто напиши описание бота, и я создам полный код с:
• Разделением на модули (handlers, keyboards, utils, database)
• База данных SQLite
• Инструкция по установке
• Файл requirements.txt
• Готово к деплою!

📝 <b>Примеры запросов:</b>
• «Создай игрового бота с угадайкой чисел»
• «Сделай бота для заметок с напоминаниями»
• «Бот для курса валют с графиками»

⭐ <b>Лимиты:</b>
• Бесплатно: {DAILY_BOTS_LIMIT} ботов в день
• VIP: {DAILY_BOTS_LIMIT_VIP} ботов в день

Нажми на кнопку ниже чтобы начать!"""

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Создать бота", callback_data="create_bot"),
        InlineKeyboardButton("⭐ VIP статус", callback_data="vip_menu")
    )
    keyboard.add(
        InlineKeyboardButton("📊 Мой профиль", callback_data="profile"),
        InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if not check_subscription(user_id):
        bot.answer_callback_query(call.id, "❌ Подпишись на канал!", show_alert=True)
        return
    
    if call.data == "create_bot":
        user = get_user(user_id)
        daily_limit = get_daily_limit(user_id)
        
        if user["bots_today"] >= daily_limit:
            bot.answer_callback_query(call.id, f"❌ Лимит {daily_limit} ботов в день! Купи VIP.", show_alert=True)
            return
        
        bot.edit_message_text(
            "📝 <b>Опиши какого бота нужно создать</b>\n\n"
            "Напиши подробное описание:\n"
            "• Какую функцию должен выполнять бот?\n"
            "• Какие команды нужны?\n"
            "• Нужна ли база данных?\n"
            "• Какие кнопки/клавиатуры?\n\n"
            "Пример: <i>Создай бота для учета расходов. Команды: /add, /stats, /report. Нужна SQLite база. Инлайн кнопки для категорий.</i>\n\n"
            "Отправь описание одним сообщением:",
            call.message.chat.id, call.message.message_id, parse_mode='HTML'
        )
        bot.register_next_step_handler(call.message, process_bot_description)
    
    elif call.data == "vip_menu":
        user = get_user(user_id)
        status = "✅ Активен" if user.get("vip_until") else "❌ Неактивен"
        if user.get("vip_until"):
            status += f"\nдо {datetime.fromisoformat(user['vip_until']).strftime('%d.%m.%Y')}"
        
        text = f"""⭐ <b>VIP статус Izzzy CodeSpace v5</b>

┌ 📊 Статус: {status}
├ 🎁 Бонусы VIP:
├   • {DAILY_BOTS_LIMIT_VIP} ботов в день
├   • Приоритетная генерация
├   • Более сложные боты
└ 🚀 Без рекламы

<b>💎 Цены (Telegram Stars):</b>
• 7 дней — {VIP_PRICES['week']} ⭐
• 30 дней — {VIP_PRICES['month']} ⭐
• 365 дней — {VIP_PRICES['year']} ⭐"""

        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton(f"7 дней — {VIP_PRICES['week']} ⭐", callback_data="vip_week"),
            InlineKeyboardButton(f"30 дней — {VIP_PRICES['month']} ⭐", callback_data="vip_month"),
            InlineKeyboardButton(f"365 дней — {VIP_PRICES['year']} ⭐", callback_data="vip_year"),
            InlineKeyboardButton("‹ Назад", callback_data="back_to_menu")
        )
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
    
    elif call.data.startswith("vip_"):
        duration = call.data.split("_")[1]
        price = VIP_PRICES[duration]
        
        bot.send_invoice(
            call.message.chat.id,
            title=f"VIP {duration} Izzzy CodeSpace",
            description=f"{DAILY_BOTS_LIMIT_VIP} ботов в день на {duration}",
            invoice_payload=f"vip_{duration}_{user_id}",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice("VIP доступ", price)],
            start_parameter="vip_subscription"
        )
    
    elif call.data == "profile":
        user = get_user(user_id)
        daily_limit = get_daily_limit(user_id)
        remaining = daily_limit - user["bots_today"]
        
        vip_status = "✅ Активен" if user.get("vip_until") else "❌ Неактивен"
        if user.get("vip_until"):
            vip_status += f"\n   до {datetime.fromisoformat(user['vip_until']).strftime('%d.%m.%Y')}"
        
        text = f"""📊 <b>Мой профиль</b>

┌ <b>📊 Статистика:</b>
├   • Сегодня: {user['bots_today']}/{daily_limit}
├   • Осталось: {remaining}
├   • Всего создано: {user['total_bots']}
│
├ <b>⭐ VIP статус:</b> {vip_status}
│
└ <b>🎁 Лимит:</b> {daily_limit} ботов/день"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("‹ Назад", callback_data="back_to_menu"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
    
    elif call.data == "help":
        text = f"""❓ <b>Помощь Izzzy CodeSpace v5</b>

<b>Как создать бота:</b>
1. Нажми «➕ Создать бота»
2. Опиши желаемого бота
3. Жди генерации (1-3 минуты)
4. Скачай ZIP архив с кодом

<b>Что входит в генерацию:</b>
• main.py — главный файл
• config.py — настройки
• handlers/ — обработчики
• keyboards/ — клавиатуры
• utils/ — утилиты
• database/ — работа с БД
• requirements.txt — зависимости
• README.md — инструкция

<b>Лимиты:</b>
• Бесплатно: {DAILY_BOTS_LIMIT} ботов/день
• VIP: {DAILY_BOTS_LIMIT_VIP} ботов/день

<b>Куда залить бота:</b>
• PythonAnywhere (бесплатно)
• Heroku (бесплатный тариф)
• Railway (бесплатно)
• Render (бесплатно)
• VPS от 300₽/мес

⭐ Приобрети VIP для увеличения лимита!"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("‹ Назад", callback_data="back_to_menu"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
    
    elif call.data == "back_to_menu":
        user = get_user(user_id)
        daily_limit = get_daily_limit(user_id)
        used_today = user["bots_today"]
        
        vip_status = "✅ VIP" if user.get("vip_until") else "❌ Бесплатный"
        if user.get("vip_until"):
            vip_status += f"\nдо {datetime.fromisoformat(user['vip_until']).strftime('%d.%m.%Y')}"
        
        text = f"""✨ <b>Izzzy CodeSpace v5</b> ✨

🤖 <b>Генератор Telegram ботов на Python</b>

📊 <b>Твоя статистика:</b>
• Сегодня создано: {used_today}/{daily_limit} ботов
• Всего создано: {user['total_bots']}
• Статус: {vip_status}

💡 Напиши описание бота, который хочешь создать!"""

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Создать бота", callback_data="create_bot"),
            InlineKeyboardButton("⭐ VIP статус", callback_data="vip_menu")
        )
        keyboard.add(
            InlineKeyboardButton("📊 Мой профиль", callback_data="profile"),
            InlineKeyboardButton("❓ Помощь", callback_data="help")
        )
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')

def process_bot_description(message):
    """Обрабатывает описание бота и запускает генерацию"""
    user_id = message.from_user.id
    description = message.text.strip()
    
    if len(description) < 10:
        bot.send_message(message.chat.id, "❌ Описание слишком короткое. Напиши подробнее (минимум 10 символов).")
        return
    
    user = get_user(user_id)
    daily_limit = get_daily_limit(user_id)
    
    if user["bots_today"] >= daily_limit:
        bot.send_message(message.chat.id, f"❌ Лимит {daily_limit} ботов в день! Купи VIP.")
        return
    
    status_msg = bot.send_message(
        message.chat.id,
        "🤖 <b>Начинаю генерацию бота...</b>\n\n"
        "📝 Анализирую описание...\n"
        "⚙️ Это займёт 1-3 минуты...\n\n"
        "Пожалуйста, подожди! 🚀",
        parse_mode='HTML'
    )
    
    # Запускаем генерацию в отдельном потоке
    def generate():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(generate_bot_code(description, user_id))
        loop.close()
        
        if result and result.get('files'):
            user["bots_today"] += 1
            user["total_bots"] += 1
            save_all()
            
            zip_buffer = create_zip_project(result['files'])
            
            bot.edit_message_text(
                f"✅ <b>Бот успешно создан!</b>\n\n"
                f"📌 <b>Название:</b> {result.get('bot_name', 'Telegram Bot')}\n"
                f"📝 <b>Описание:</b> {result.get('description', description)[:100]}\n\n"
                f"📦 <b>Структура проекта:</b>\n"
                f"• main.py — точка входа\n"
                f"• config.py — настройки\n"
                f"• handlers/ — обработчики команд\n"
                f"• keyboards/ — клавиатуры\n"
                f"• utils/ — утилиты\n"
                f"• database/ — работа с БД\n"
                f"• requirements.txt — зависимости\n"
                f"• README.md — инструкция\n\n"
                f"⬇️ Скачай архив и залей бота на хостинг!",
                status_msg.chat.id, status_msg.message_id, parse_mode='HTML'
            )
            
            bot.send_document(
                message.chat.id,
                zip_buffer,
                filename=f"{result.get('bot_name', 'telegram_bot').lower().replace(' ', '_')}.zip",
                caption="🤖 Твой готовый Telegram бот!"
            )
        else:
            bot.edit_message_text(
                "❌ <b>Ошибка генерации!</b>\n\n"
                "Не удалось создать бота. Попробуй:\n"
                "• Описать бота подробнее\n"
                "• Указать конкретные команды\n"
                "• Попробовать позже",
                status_msg.chat.id, status_msg.message_id, parse_mode='HTML'
            )
    
    threading.Thread(target=generate).start()

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = message.from_user.id
    duration = message.successful_payment.invoice_payload.split("_")[1]
    delta = {"week": timedelta(days=7), "month": timedelta(days=30), "year": timedelta(days=365)}[duration]
    
    user = get_user(user_id)
    user["vip_until"] = (datetime.now() + delta).isoformat()
    save_all()
    
    bot.send_message(
        message.chat.id,
        f"✅ <b>VIP активирован на {duration}!</b>\n\n"
        f"Теперь тебе доступно:\n"
        f"• {DAILY_BOTS_LIMIT_VIP} ботов в день\n"
        f"• Приоритетная генерация\n\n"
        f"Спасибо за поддержку! 🎉",
        parse_mode='HTML'
    )
    
    start_command(message)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Если пользователь просто написал текст вне диалога создания
    bot.send_message(
        message.chat.id,
        "❓ <b>Не понимаю команду</b>\n\n"
        "Нажми /start для начала работы или нажми кнопку «➕ Создать бота»",
        parse_mode='HTML'
    )

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("✅ Бот Izzzy CodeSpace v5 запущен!")
    bot.infinity_polling(timeout=80, long_polling_timeout=80)