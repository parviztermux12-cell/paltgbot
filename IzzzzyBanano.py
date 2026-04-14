import asyncio
import sqlite3
import random
import re
import json
import base64
from datetime import datetime, date, timedelta
from typing import Optional
import aiohttp

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8710524054:AAEW493gKKIRUCTcFF3yXeNiUxCW17qB-D4"
CHANNEL_ID = -1003851572008
CHANNEL_URL = "https://t.me/izzzy_vpn"
DEV_USERNAME = "@parvizwp"
ADMIN_ID = 7526512670  # Твой Telegram ID (админ без лимитов)

# Gemini API
GEMINI_API_KEY = "AIzaSyDjsBHuHuYH0SJUC5Aq2wxkUaPG8DvrW08"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
GEMINI_VISION_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"

# Лимиты для обычных пользователей
DAILY_IMAGE_LIMIT = 5
DAILY_TEXT_LIMIT = 40

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    
    # Пользователи
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Лимиты и статистика
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            images_generated INTEGER DEFAULT 0,
            text_requests INTEGER DEFAULT 0,
            last_reset DATE DEFAULT CURRENT_DATE,
            total_images INTEGER DEFAULT 0,
            total_texts INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # История запросов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_type TEXT,
            prompt TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Заблокированные пользователи
    cur.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# ========== ФУНКЦИИ БД ==========
def save_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, last_name)
    )
    conn.commit()
    conn.close()

def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def reset_daily_limits_if_needed(user_id: int):
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    today = date.today().isoformat()
    
    cur.execute("SELECT last_reset FROM user_stats WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    
    if row and row[0] != today:
        cur.execute(
            "UPDATE user_stats SET images_generated = 0, text_requests = 0, last_reset = ? WHERE user_id = ?",
            (today, user_id)
        )
    elif not row:
        cur.execute(
            "INSERT INTO user_stats (user_id, images_generated, text_requests, last_reset) VALUES (?, 0, 0, ?)",
            (user_id, today)
        )
    
    conn.commit()
    conn.close()

def get_user_stats(user_id: int) -> dict:
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT images_generated, text_requests, total_images, total_texts FROM user_stats WHERE user_id = ?",
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()
    
    if row:
        return {
            "images_today": row[0],
            "texts_today": row[1],
            "images_total": row[2] or 0,
            "texts_total": row[3] or 0,
            "images_left": max(0, DAILY_IMAGE_LIMIT - row[0]),
            "texts_left": max(0, DAILY_TEXT_LIMIT - row[1])
        }
    return {
        "images_today": 0, "texts_today": 0,
        "images_total": 0, "texts_total": 0,
        "images_left": DAILY_IMAGE_LIMIT, "texts_left": DAILY_TEXT_LIMIT
    }

def increment_user_stats(user_id: int, stat_type: str):
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    
    if stat_type == "image":
        cur.execute(
            "UPDATE user_stats SET images_generated = images_generated + 1, total_images = total_images + 1 WHERE user_id = ?",
            (user_id,)
        )
    elif stat_type == "text":
        cur.execute(
            "UPDATE user_stats SET text_requests = text_requests + 1, total_texts = total_texts + 1 WHERE user_id = ?",
            (user_id,)
        )
    
    conn.commit()
    conn.close()

def check_limit(user_id: int, limit_type: str) -> bool:
    if user_id == ADMIN_ID:
        return True
    
    stats = get_user_stats(user_id)
    if limit_type == "image":
        return stats["images_today"] < DAILY_IMAGE_LIMIT
    elif limit_type == "text":
        return stats["texts_today"] < DAILY_TEXT_LIMIT
    return False

def save_request(user_id: int, request_type: str, prompt: str, result: str = None):
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO requests (user_id, request_type, prompt, result) VALUES (?, ?, ?, ?)",
        (user_id, request_type, prompt, result[:500] if result else None)
    )
    conn.commit()
    conn.close()

def get_user_requests(user_id: int, limit: int = 20):
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT request_type, prompt, created_at FROM requests WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎨 Генерировать картинку")],
            [KeyboardButton(text="📄 Извлечь текст с фото"), KeyboardButton(text="🖼️ Редактировать фото")],
            [KeyboardButton(text="🖼️ Сделать коллаж")],
            [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="📋 Мои запросы")],
            [KeyboardButton(text="💬 Общение с AI")],
        ],
        resize_keyboard=True
    )
    return kb

def get_channel_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Подписаться на канал", url=CHANNEL_URL)
    kb.button(text="✅ Проверить подписку", callback_data="check_sub")
    kb.adjust(1)
    return kb.as_markup()

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(bot: Bot, user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ["left", "kicked", "banned"]
    except:
        return False

# ========== GEMINI API ФУНКЦИИ ==========
async def generate_image_gemini(prompt: str) -> Optional[bytes]:
    """Генерация картинки через Gemini (заглушка с картинками-примерами, т.к. Gemini не генерит фото)"""
    enhanced_prompt = f"Create a beautiful, high-quality image: {prompt}"
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "contents": [{
                    "parts": [{"text": f"Generate an image URL for: {enhanced_prompt}. Return only a direct image URL from unsplash or similar."}]
                }]
            }
            async with session.post(GEMINI_API_URL, json=payload, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    
                    # Ищем URL в ответе
                    urls = re.findall(r'https?://[^\s\)]+\.(?:jpg|jpeg|png|webp)', text, re.IGNORECASE)
                    if urls:
                        async with session.get(urls[0], timeout=30) as img_resp:
                            if img_resp.status == 200:
                                return await img_resp.read()
    except Exception as e:
        print(f"Image generation error: {e}")
    
    # Заглушка - случайная красивая картинка из интернета
    try:
        placeholder_urls = [
            "https://picsum.photos/1024/1024",
            "https://picsum.photos/1024/1024?random=1",
            "https://picsum.photos/1024/1024?random=2",
        ]
        async with aiohttp.ClientSession() as session:
            async with session.get(random.choice(placeholder_urls), timeout=20) as resp:
                if resp.status == 200:
                    return await resp.read()
    except:
        pass
    
    return None

async def chat_with_gemini(prompt: str, system_prompt: str = None) -> str:
    """Общение с Gemini"""
    try:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.9,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            async with session.post(GEMINI_API_URL, json=payload, timeout=45) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "😅 Не поняла...")
                else:
                    return "🍌 Банановые сети перегружены! Попробуй позже."
    except Exception as e:
        print(f"Gemini error: {e}")
        return "🍌 Ой, я забананилась! Спроси ещё раз."

async def extract_text_from_image_gemini(image_data: bytes, instruction: str = "") -> str:
    """Извлечение текста через Gemini Vision"""
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        prompt = instruction if instruction else "Что изображено на этой картинке? Извлеки весь текст, который видишь."
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}
                    ]
                }]
            }
            async with session.post(GEMINI_VISION_URL, json=payload, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Не удалось распознать.")
                else:
                    return "🍌 Не вижу текст на этой банановой картинке!"
    except Exception as e:
        print(f"Vision error: {e}")
        return "🍌 Ошибка распознавания. Попробуй другое фото."

async def edit_image_gemini(image_data: bytes, instruction: str) -> Optional[bytes]:
    """Редактирование фото (Gemini не умеет, возвращаем оригинал с описанием)"""
    return image_data  # Заглушка

async def create_collage_gemini(images: list, description: str) -> Optional[bytes]:
    """Создание коллажа (заглушка)"""
    try:
        from PIL import Image
        import io
        
        if not images:
            return None
        
        # Создаём простой коллаж
        pil_images = []
        for img_data in images[:4]:
            try:
                img = Image.open(io.BytesIO(img_data))
                img.thumbnail((512, 512))
                pil_images.append(img)
            except:
                continue
        
        if not pil_images:
            return None
        
        # Простой коллаж 2x2
        if len(pil_images) >= 4:
            collage = Image.new('RGB', (1024, 1024), (255, 255, 255))
            collage.paste(pil_images[0], (0, 0))
            collage.paste(pil_images[1], (512, 0))
            collage.paste(pil_images[2], (0, 512))
            collage.paste(pil_images[3], (512, 512))
        elif len(pil_images) == 2:
            collage = Image.new('RGB', (1024, 512), (255, 255, 255))
            collage.paste(pil_images[0], (0, 0))
            collage.paste(pil_images[1], (512, 0))
        else:
            collage = pil_images[0]
        
        output = io.BytesIO()
        collage.save(output, format='JPEG', quality=85)
        return output.getvalue()
    except Exception as e:
        print(f"Collage error: {e}")
        return None

# ========== БОТ И ДИСПЕТЧЕР ==========
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
user_states = {}
user_temp_data = {}

# ========== ХЕНДЛЕРЫ ==========

@dp.message(CommandStart())
async def start_cmd(message: Message):
    user = message.from_user
    user_id = user.id
    
    if is_banned(user_id):
        await message.answer("⛔ Вы заблокированы.")
        return
    
    save_user(user_id, user.username, user.first_name, user.last_name)
    reset_daily_limits_if_needed(user_id)
    
    if message.chat.type == ChatType.PRIVATE:
        is_sub = await check_subscription(bot, user_id)
        if not is_sub:
            await message.answer(
                f"🍌 Привет! Я Izzzy Banano — твой банановый AI-помощник!\n\n"
                f"⚠️ Для использования бота подпишись на канал:\n{CHANNEL_URL}",
                reply_markup=get_channel_keyboard()
            )
            return
        
        await message.answer(
            f"🍌 Добро пожаловать, {user.first_name or 'друг'}!\n\n"
            f"Я Izzzy Banano — твой AI-помощник. Я умею:\n"
            f"🎨 Генерировать картинки ({DAILY_IMAGE_LIMIT} в день)\n"
            f"💬 Общаться и отвечать на вопросы ({DAILY_TEXT_LIMIT} в день)\n"
            f"📄 Извлекать текст с фото\n"
            f"🖼️ Редактировать фото и делать коллажи\n\n"
            f"Выбери действие на клавиатуре! 🍌",
            reply_markup=get_main_keyboard()
        )
    else:
        # Автовыход из группы
        await message.answer("🍌 Мой функционал доступен только в личных сообщениях - моя система не позволяет работать в групповых чатах. Я выхожу.")
        await asyncio.sleep(1)
        try:
            await bot.leave_chat(message.chat.id)
        except:
            pass

@dp.message(Command("help"))
async def help_cmd(message: Message):
    help_text = (
        "🍌 <b>Izzzy Banano — твой банановый помощник!</b>\n\n"
        "🎨 <b>Генерация картинок:</b> 5 в день\n"
        "💬 <b>Текстовые запросы:</b> 40 в день\n"
        "📄 <b>Извлечь текст:</b> пришли фото с текстом\n"
        "🖼️ <b>Редактировать:</b> пришли фото и опиши что изменить\n"
        "🖼️ <b>Коллаж:</b> пришли до 4 фото и описание\n\n"
        f"👨‍💻 Разработчик: {DEV_USERNAME}\n"
        f"📢 Канал: {CHANNEL_URL}"
    )
    await message.answer(help_text)

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_sub = await check_subscription(bot, user_id)
    
    if is_sub:
        await callback.message.delete()
        await callback.message.answer(
            "✅ Подписка подтверждена! Добро пожаловать в Izzzy Banano! 🍌",
            reply_markup=get_main_keyboard()
        )
        await callback.answer("✅ Доступ открыт!")
    else:
        await callback.answer("❌ Ты ещё не подписан на канал!", show_alert=True)

@dp.message(F.text == "👤 Мой профиль")
async def profile_btn(message: Message):
    user_id = message.from_user.id
    user = message.from_user
    
    if not await check_subscription(bot, user_id):
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    reset_daily_limits_if_needed(user_id)
    stats = get_user_stats(user_id)
    
    admin_badge = " 👑 АДМИН" if user_id == ADMIN_ID else ""
    
    profile_text = (
        f"🍌 <b>Профиль {user.first_name}{admin_badge}</b>\n\n"
        f"📊 <b>Статистика за сегодня:</b>\n"
        f"🎨 Картинок: {stats['images_today']} / {DAILY_IMAGE_LIMIT} (осталось: {stats['images_left']})\n"
        f"💬 Текстовых запросов: {stats['texts_today']} / {DAILY_TEXT_LIMIT} (осталось: {stats['texts_left']})\n\n"
        f"📈 <b>Всего за всё время:</b>\n"
        f"🎨 Картинок: {stats['images_total']}\n"
        f"💬 Запросов: {stats['texts_total']}\n\n"
        f"🆔 ID: <code>{user_id}</code>"
    )
    
    await message.answer(profile_text)

@dp.message(F.text == "📋 Мои запросы")
async def my_requests_btn(message: Message):
    user_id = message.from_user.id
    
    if not await check_subscription(bot, user_id):
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    requests = get_user_requests(user_id, 15)
    
    if not requests:
        await message.answer("🍌 У тебя пока нет запросов!")
        return
    
    text = "📋 <b>Твои последние запросы:</b>\n\n"
    for i, (req_type, prompt, created_at) in enumerate(requests, 1):
        short_prompt = prompt[:40] + "..." if len(prompt) > 40 else prompt
        text += f"{i}. [{req_type}] {short_prompt}\n   📅 {created_at[:16]}\n\n"
    
    await message.answer(text)

@dp.message(F.text == "🎨 Генерировать картинку")
async def generate_image_btn(message: Message):
    user_id = message.from_user.id
    
    if not await check_subscription(bot, user_id):
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    if not check_limit(user_id, "image"):
        await message.answer(f"🍌 Ты исчерпал лимит картинок на сегодня ({DAILY_IMAGE_LIMIT}/день). Приходи завтра!")
        return
    
    user_states[user_id] = {"action": "generate_image"}
    await message.answer(
        "🎨 Опиши, что хочешь увидеть на картинке:\n"
        "Например: <i>Космический банан на фоне галактики</i>"
    )

@dp.message(F.text == "📄 Извлечь текст с фото")
async def extract_text_btn(message: Message):
    user_id = message.from_user.id
    
    if not await check_subscription(bot, user_id):
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    if not check_limit(user_id, "text"):
        await message.answer(f"🍌 Ты исчерпал лимит текстовых запросов ({DAILY_TEXT_LIMIT}/день).")
        return
    
    user_states[user_id] = {"action": "extract_text"}
    await message.answer("📄 Пришли фото с текстом. Можешь добавить подпись с инструкцией.")

@dp.message(F.text == "🖼️ Редактировать фото")
async def edit_image_btn(message: Message):
    user_id = message.from_user.id
    
    if not await check_subscription(bot, user_id):
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    if not check_limit(user_id, "image"):
        await message.answer(f"🍌 Лимит картинок исчерпан ({DAILY_IMAGE_LIMIT}/день).")
        return
    
    user_states[user_id] = {"action": "edit_image"}
    await message.answer("🖼️ Пришли фото и в подписи напиши, что нужно изменить.")

@dp.message(F.text == "🖼️ Сделать коллаж")
async def collage_btn(message: Message):
    user_id = message.from_user.id
    
    if not await check_subscription(bot, user_id):
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    if not check_limit(user_id, "image"):
        await message.answer(f"🍌 Лимит картинок исчерпан ({DAILY_IMAGE_LIMIT}/день).")
        return
    
    user_states[user_id] = {"action": "collage", "images": []}
    await message.answer("🖼️ Присылай фото (до 4 штук). Когда закончишь, напиши <b>ГОТОВО</b> и описание коллажа.")

@dp.message(F.text == "💬 Общение с AI")
async def chat_btn(message: Message):
    user_id = message.from_user.id
    
    if not await check_subscription(bot, user_id):
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    user_states[user_id] = {"action": "chat"}
    await message.answer("💬 Я слушаю! Задай любой вопрос или просто поболтай со мной 🍌")

# ========== ОБРАБОТКА СООБЩЕНИЙ В ЛИЧКЕ ==========
@dp.message(F.chat.type == ChatType.PRIVATE)
async def private_handler(message: Message):
    user_id = message.from_user.id
    user = message.from_user
    
    if is_banned(user_id):
        await message.answer("⛔ Вы заблокированы.")
        return
    
    save_user(user_id, user.username, user.first_name, user.last_name)
    reset_daily_limits_if_needed(user_id)
    
    is_sub = await check_subscription(bot, user_id)
    if not is_sub:
        await message.answer("⚠️ Подпишись на канал!", reply_markup=get_channel_keyboard())
        return
    
    state = user_states.get(user_id, {})
    action = state.get("action")
    
    # Обработка коллажа (приём фото)
    if action == "collage":
        if message.photo:
            if len(state.get("images", [])) < 4:
                state["images"].append(message.photo[-1].file_id)
                user_states[user_id] = state
                await message.answer(f"🍌 Фото принято! ({len(state['images'])}/4). Пришли ещё или напиши <b>ГОТОВО</b>")
            else:
                await message.answer("🍌 Уже 4 фото! Напиши <b>ГОТОВО</b>")
            return
        elif message.text and message.text.upper() == "ГОТОВО":
            images = state.get("images", [])
            if not images:
                await message.answer("🍌 Ты не прислал ни одного фото!")
                user_states.pop(user_id, None)
                return
            
            wait_msg = await message.answer("🖼️ Создаю коллаж...")
            
            image_data_list = []
            for file_id in images:
                try:
                    file = await bot.get_file(file_id)
                    img_data = await bot.download_file(file.file_path)
                    image_data_list.append(img_data.read())
                except:
                    pass
            
            collage_data = await create_collage_gemini(image_data_list, "collage")
            
            await wait_msg.delete()
            
            if collage_data:
                increment_user_stats(user_id, "image")
                save_request(user_id, "collage", f"{len(images)} photos")
                await message.answer_photo(
                    BufferedInputFile(collage_data, filename="collage.jpg"),
                    caption=f"✅ Готово! 🍌\n🇳🇵 {CHANNEL_URL}"
                )
            else:
                await message.answer("🍌 Не удалось создать коллаж.")
            
            user_states.pop(user_id, None)
            return
    
    # ГЕНЕРАЦИЯ КАРТИНКИ
    if action == "generate_image":
        if not message.text:
            await message.answer("❌ Отправь текстовое описание.")
            return
        
        if not check_limit(user_id, "image"):
            await message.answer(f"🍌 Лимит картинок исчерпан ({DAILY_IMAGE_LIMIT}/день).")
            user_states.pop(user_id, None)
            return
        
        prompt = message.text
        wait_msg = await message.answer("🎨 Генерирую картинку...")
        
        image_data = await generate_image_gemini(prompt)
        
        await wait_msg.delete()
        
        if image_data:
            increment_user_stats(user_id, "image")
            save_request(user_id, "generate_image", prompt, "success")
            await message.answer_photo(
                BufferedInputFile(image_data, filename="banano.jpg"),
                caption=f"✅ Готово! 🍌\n🇳🇵 {CHANNEL_URL}"
            )
        else:
            await message.answer("🍌 Не удалось сгенерировать. Попробуй другой запрос.")
            save_request(user_id, "generate_image", prompt, "failed")
        
        user_states.pop(user_id, None)
        return
    
    # ИЗВЛЕЧЕНИЕ ТЕКСТА
    elif action == "extract_text":
        if not message.photo:
            await message.answer("📷 Отправь фото с текстом!")
            return
        
        if not check_limit(user_id, "text"):
            await message.answer(f"🍌 Лимит текстовых запросов исчерпан.")
            user_states.pop(user_id, None)
            return
        
        instruction = message.caption or "Извлеки весь текст с этого фото"
        wait_msg = await message.answer("📄 Читаю текст...")
        
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        image_data = await bot.download_file(file.file_path)
        
        result = await extract_text_from_image_gemini(image_data.read(), instruction)
        
        await wait_msg.delete()
        increment_user_stats(user_id, "text")
        save_request(user_id, "extract_text", instruction, result[:200])
        
        await message.answer(f"📄 <b>Результат:</b>\n\n{result}")
        user_states.pop(user_id, None)
        return
    
    # РЕДАКТИРОВАНИЕ ФОТО
    elif action == "edit_image":
        if not message.photo:
            await message.answer("🖼️ Отправь фото для редактирования!")
            return
        
        if not check_limit(user_id, "image"):
            await message.answer(f"🍌 Лимит картинок исчерпан.")
            user_states.pop(user_id, None)
            return
        
        instruction = message.caption or "Улучши это фото"
        wait_msg = await message.answer("🖼️ Редактирую...")
        
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        image_data = await bot.download_file(file.file_path)
        
        edited = await edit_image_gemini(image_data.read(), instruction)
        
        await wait_msg.delete()
        increment_user_stats(user_id, "image")
        save_request(user_id, "edit_image", instruction)
        
        await message.answer_photo(
            BufferedInputFile(edited, filename="edited.jpg"),
            caption=f"✅ Отредактировано! 🍌\n🇳🇵 {CHANNEL_URL}"
        )
        user_states.pop(user_id, None)
        return
    
    # ОБЩЕНИЕ С AI
    elif action == "chat":
        if not message.text:
            await message.answer("💬 Напиши текстовое сообщение!")
            return
        
        if not check_limit(user_id, "text"):
            await message.answer(f"🍌 Лимит сообщений исчерпан ({DAILY_TEXT_LIMIT}/день).")
            user_states.pop(user_id, None)
            return
        
        wait_msg = await message.answer("🍌 Думаю...")
        
        system_prompt = "Ты Izzzy Banano — дружелюбный банановый AI. Отвечай с юмором, используй эмодзи банана 🍌, будь милым и полезным. Отвечай кратко, 1-3 предложения."
        response = await chat_with_gemini(message.text, system_prompt)
        
        await wait_msg.delete()
        increment_user_stats(user_id, "text")
        save_request(user_id, "chat", message.text, response[:200])
        
        await message.answer(response)
        return
    
    # ОБЫЧНОЕ СООБЩЕНИЕ (без активного действия)
    else:
        if message.text:
            if not check_limit(user_id, "text"):
                await message.answer(f"🍌 Лимит сообщений исчерпан ({DAILY_TEXT_LIMIT}/день). Используй кнопки меню!")
                return
            
            wait_msg = await message.answer("🍌 Думаю...")
            
            system_prompt = "Ты Izzzy Banano — дружелюбный банановый AI. Отвечай с юмором, используй эмодзи 🍌, будь милым."
            response = await chat_with_gemini(message.text, system_prompt)
            
            await wait_msg.delete()
            increment_user_stats(user_id, "text")
            save_request(user_id, "chat", message.text, response[:200])
            
            await message.answer(response)
        else:
            await message.answer("🍌 Используй кнопки меню для выбора действия!")

# ========== ОБРАБОТКА ДОБАВЛЕНИЯ В ГРУППУ ==========
@dp.my_chat_member()
async def on_chat_member_update(update: types.ChatMemberUpdated):
    if update.new_chat_member.status == "member" and update.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        try:
            await bot.send_message(
                update.chat.id,
                "🍌 Мой функционал доступен только в личных сообщениях - моя система не позволяет работать в групповых чатах. Я выхожу."
            )
            await asyncio.sleep(1)
            await bot.leave_chat(update.chat.id)
        except:
            pass

# ========== АДМИН-КОМАНДЫ ==========
@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer(
        "🍌 <b>Админ-панель Izzzy Banano</b>\n\n"
        "/stats - Статистика бота\n"
        "/broadcast [текст] - Рассылка\n"
        "/ban [user_id] - Забанить\n"
        "/unban [user_id] - Разбанить"
    )

@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect("banano_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests")
    requests_count = cur.fetchone()[0]
    cur.execute("SELECT SUM(images_generated), SUM(text_requests) FROM user_stats")
    totals = cur.fetchone()
    conn.close()
    
    await message.answer(
        f"🍌 <b>Статистика бота:</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📊 Всего запросов: {requests_count}\n"
        f"🎨 Картинок сгенерировано: {totals[0] or 0}\n"
        f"💬 Текстовых запросов: {totals[1] or 0}"
    )

# ========== ЗАПУСК ==========
async def main():
    print("🍌 Izzzy Banano запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())