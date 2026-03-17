import os
import sqlite3
import uuid
import logging
import requests
from datetime import datetime, date, timedelta
import urllib.parse
import json
import random
from collections import defaultdict
import time
import string
import threading
import math
import shutil
from copy import deepcopy

import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# ================== НАСТРОЙКА ЛОГИРОВАНИЯ ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_logs.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LasVenturas By parviz")

# ================== КОНСТАНТЫ И ОГРАНИЧЕНИЯ ==================
TOKEN = "8293824305:AAFJOr6qmu3TGAzuLz0yc4MXF_fa7eVnBHQ"
WELCOME_IMAGE_URL = "https://i.supaimg.com/2939d8ad-5c5a-4bea-a182-6c3e8bbc833d.jpg"
CASINO_IMAGE_URL = "https://avatars.mds.yandex.net/i?id=c651fbed170eb7128e00ff84ca1c0bf543c74de2-10332115-images-thumbs&n=13"
BLACKJACK_IMAGE_URL = "https://avatars.mds.yandex.net/i?id=dc64180881834f3c5a302bda16d65de46956d887-5355514-images-thumbs&n=13&shower=-1&blur=-1"
COIN_FLIP_GIF = "https://media.tenor.com/tewn7lzVDgcAAAAC/coin-flip-flip.gif"
ADMIN_IDS = [7526512670]
AI_TEXT_API = "https://text.pollinations.ai/prompt/"
CASINO_DATA_FILE = "cs.json"
PROMO_CODES_FILE = "promcodes.json"
CONFIG_FILE = "onfig.json"
WARNS_FILE = "wans.json"
START_BALANCE = 5000
PROMO_CHAT_ID = -1003135867755  # ID чата для отправки промокодов (None - отключено)

# ================== ВОЛШЕБНЫЙ КОНФИГ БЛЯТЬ ==================
config = {
    "max_daily_income": 999999999999999999999999999,
    "max_balance": 999999999999999999999999999999,
    "transfer_daily_limit": 999999999,
    "transfer_fee": 0.1,
    "blackjack_win_multiplier": 2.0,
    "roulette_win_multiplier": 2.0,
    "slots_win_multiplier": 3.0,
    "coinflip_win_multiplier": 2.0,
    "dice_win_multiplier": 2.0,
    "tyanka_profit_multiplier": 1.0,
    "business_profit_multiplier": 1.0,
    "car_profit_multiplier": 1.0,
    "house_profit_multiplier": 1.0,
    "pet_profit_multiplier": 1.0,
    "vip_bonus_multiplier": 1.0,
    "referral_bonus_multiplier": 1.0
}

# ================== ПРОСТЫЕ ФУНКЦИИ БЛЯТЬ ==================
def check_income_limits(user_id, amount):
    """ХУЙ ЗНАЕТ ЧТО ЭТО, ПРОПУСТИТЬ ВСЁ"""
    return amount

def add_income(user_id, amount, source="unknown"):
    """ПРОСТО ДАЁМ БАБКИ"""
    user_data = get_user_data(user_id)
    user_data["balance"] += amount
    save_casino_data()
    logger.info(f"💰 {user_id} получил {amount}$ от {source}")
    return amount

def apply_transfer_limits(sender_id, amount):
    """КОМИССИЯ 10% И ВСЁ"""
    fee = int(amount * 0.1)
    return amount - fee, fee
    
# ================== СОЗДАЁМ БОТА ==================
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")



RP_COMMANDS = {
    # Нежные действия
    "обнять": "· 🫂 | {user1} крепко обнял(а) пользователя {user2}",
    "поцеловать": "· 💋 | {user1} поцеловал(а) {user2}",
    "погладить": "· ✨ | {user1} погладил(а) {user2}",
    
    # Весёлые взаимодействия
    "пощекотать": "· 🪶 | {user1} пощекотал(а) {user2}",
    
    # Подарки
    "подарить": "· 🎁 | {user1} подарил(а) носок для пользователя {user2}",
    
    # Агрессивные действия
    "ударить": "· 👊 | {user1} ударил(а) {user2}",
    "шлёпнуть": "· 🖐️ | {user1} шлёпнул(а) {user2}",
    "избить": "· 🥊 | {user1} избил(а) пользователя {user2}",
    
    # Воровство
    "украсть": "· 🥷 | {user1} украл(а) деньги у пользователя {user2}",
    
    # 18+ действия
    "выебать": "· 🍆 | {user1} выебал(а) пользователя {user2}",
    "трахнуть": "· 🔥 | {user1} трахнул(а) пользователя {user2}",
    "отсосать": "· 👅 | {user1} отсосал(а) у {user2}",
    "отлизать": "· 💦 | {user1} отлизал(а) {user2}",
    
    # Новые действия
    "закурить": "· 🚬 | {user1} пошёл покурить с пользователем {user2}"
}

# ================== ПОЛНАЯ ОПТИМИЗИРОВАННАЯ VIP СИСТЕМА С ЗАЩИТОЙ ОТ ЧУЖИХ КНОПОК ==================

VIP_LEVELS = {
    1: {"name": "Bronze", "prefix": "🥉", "bonus": 0.05, "income": 1000},
    2: {"name": "Silver", "prefix": "🥈", "bonus": 0.10, "income": 2500},
    3: {"name": "Gold", "prefix": "🥇", "bonus": 0.15, "income": 5000},
    4: {"name": "Platinum", "prefix": "💎", "bonus": 0.20, "income": 8000},
    5: {"name": "Diamond", "prefix": "🔹", "bonus": 0.25, "income": 11000},
    6: {"name": "Master", "prefix": "👑", "bonus": 0.30, "income": 14000},
    7: {"name": "Legend", "prefix": "🔥", "bonus": 0.40, "income": 20000},
}

# Глобальная переменная для таймеров дохода
vip_income_timers = {}

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["вип", "vip"])
def vip_list(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    text = "🎊 <b>МАГАЗИН VIP</b> 🎊\n\n"
    text += "💫 <i>Повышай статус — получай бонусы и пассивный доход!</i>\n\n"
    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    for lvl, info in VIP_LEVELS.items():
        price = lvl * 250000
        bonus_percent = int(info["bonus"] * 100)
        
        text += (
            f"{info['prefix']} <b>VIP {info['name']}</b>\n"
            f"├ Уровень: <code>#{lvl}</code>\n"
            f"├ Стоимость: <code>{format_number(price)} izzzy</code>\n"
            f"├ Бонус: <b>+{bonus_percent}%</b> к доходам\n"
            f"└ Доход: <b>{format_number(info['income'])} izzzy</b>/3ч\n\n"
        )

    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"👤 <b>Твой баланс:</b> <code>{format_number(user_data['balance'])} izzzy</code>\n"
    
    current_vip = user_data["vip"]
    if current_vip["level"] > 0:
        vip_info = VIP_LEVELS[current_vip["level"]]
        text += f"⭐ <b>Твой VIP:</b> {vip_info['prefix']} {vip_info['name']}\n\n"
    else:
        text += f"⭐ <b>Твой VIP:</b> Нет\n\n"

    kb = InlineKeyboardMarkup(row_width=2)
    
    # Компактные кнопки покупки
    buttons = []
    for lvl in range(1, 8):
        buttons.append(InlineKeyboardButton(f"VIP {lvl}", callback_data=f"buy_vip_{user_id}_{lvl}"))
    
    # Добавляем кнопки по 2 в ряд
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            kb.row(buttons[i], buttons[i + 1])
        else:
            kb.row(buttons[i])
    
    # Если есть VIP, добавляем кнопку продажи
    if current_vip["level"] > 0:
        kb.row(InlineKeyboardButton("💰 Продать VIP", callback_data=f"sell_vip_{user_id}"))
    
    # Убрана кнопка "⬅️ Назад"
    # kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"menu_main_{user_id}"))

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_vip_"))
def buy_vip_callback(call):
    try:
        parts = call.data.split("_")
        owner_id = int(parts[2])
        level = int(parts[3])
        
        # ЗАЩИТА: проверяем, что нажимает владелец кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        # Проверяем, есть ли уже VIP
        if user_data["vip"]["level"] > 0:
            current_vip = VIP_LEVELS[user_data["vip"]["level"]]
            kb = InlineKeyboardMarkup()
            kb.row(InlineKeyboardButton("💰 Продать VIP", callback_data=f"sell_vip_{user_id}"))
            kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"vip_back_{user_id}"))
            
            bot.edit_message_text(
                f"{mention} у тебя уже есть VIP {current_vip['prefix']} {current_vip['name']}, если хочешь другой купить - продай свою по кнопке ниже 💎",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )
            return

        if level not in VIP_LEVELS:
            bot.answer_callback_query(call.id, "❌ Неверный уровень VIP!")
            return

        vip_info = VIP_LEVELS[level]
        price = level * 250000

        if user_data["balance"] < price:
            kb = InlineKeyboardMarkup()
            kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"vip_back_{user_id}"))
            
            bot.edit_message_text(
                f"💸 {mention} недостаточно средств для покупки <b>{vip_info['prefix']} VIP {vip_info['name']}</b> 😔\n\n"
                f"💳 Нужно: <code>{format_number(price)} izzzy</code>\n"
                f"💰 На балансе: <code>{format_number(user_data['balance'])} izzzy</code>\n\n"
                f"Чтобы пополнить игровой счёт, введи команду:\n"
                f"<code>задонатить {price}</code>\n\n"
                f"💫 Оплата через ⭐",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )
            return

        # Покупка VIP
        user_data["balance"] -= price
        user_data["vip"] = {
            "level": level,
            "expires": (datetime.now() + timedelta(days=30)).isoformat(),
            "purchase_price": price,
            "last_income": datetime.now().isoformat()
        }
        save_casino_data()

        # Устанавливаем таймер для дохода
        vip_income_timers[user_id] = time.time()

        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"vip_back_{user_id}"))

        bot.edit_message_text(
            f"🎉 {mention} ты купил <b>{vip_info['prefix']} VIP {vip_info['name']}</b>, поздравляю 🎁",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id, "✅ VIP успешно куплен!")

    except Exception as e:
        logger.error(f"Ошибка покупки VIP: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при покупке!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("sell_vip_"))
def sell_vip_callback(call):
    try:
        owner_id = int(call.data.split("_")[2])
        
        # ЗАЩИТА: проверяем, что нажимает владелец кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        current_vip = user_data["vip"]
        if current_vip["level"] == 0:
            bot.answer_callback_query(call.id, "❌ У тебя нет VIP для продажи!")
            return

        vip_info = VIP_LEVELS[current_vip["level"]]
        sell_price = int(current_vip.get("purchase_price", current_vip["level"] * 250000) * 0.15)  # 15% от стоимости

        # Продажа VIP
        user_data["balance"] += sell_price
        user_data["vip"] = {"level": 0, "expires": None}
        
        # Удаляем таймер дохода
        vip_income_timers.pop(user_id, None)
        
        save_casino_data()

        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"vip_back_{user_id}"))

        bot.edit_message_text(
            f"💎 {mention} ты продал свой VIP-статус {vip_info['prefix']} {vip_info['name']} за <code>{format_number(sell_price)} izzzy</code>\n\n"
            f"Теперь можешь купить другой 💠",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id, "✅ VIP продан!")

    except Exception as e:
        logger.error(f"Ошибка продажи VIP: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при продаже!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("vip_back_"))
def vip_back_callback(call):
    try:
        owner_id = int(call.data.split("_")[2])
        
        # ЗАЩИТА: проверяем, что нажимает владелец кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        
        text = "🎊 <b>МАГАЗИН VIP</b> 🎊\n\n"
        text += "💫 <i>Повышай статус — получай бонусы и пассивный доход!</i>\n\n"
        text += "━━━━━━━━━━━━━━━━━━━\n\n"
        
        for lvl, info in VIP_LEVELS.items():
            price = lvl * 250000
            bonus_percent = int(info["bonus"] * 100)
            
            text += (
                f"{info['prefix']} <b>VIP {info['name']}</b>\n"
                f"├ Уровень: <code>#{lvl}</code>\n"
                f"├ Стоимость: <code>{format_number(price)} izzzy</code>\n"
                f"├ Бонус: <b>+{bonus_percent}%</b> к доходам\n"
                f"└ Доход: <b>{format_number(info['income'])} izzzy</b>/3ч\n\n"
            )

        text += "━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"👤 <b>Твой баланс:</b> <code>{format_number(user_data['balance'])} izzzy</code>\n"
        
        current_vip = user_data["vip"]
        if current_vip["level"] > 0:
            vip_info = VIP_LEVELS[current_vip["level"]]
            text += f"⭐ <b>Твой VIP:</b> {vip_info['prefix']} {vip_info['name']}\n\n"
        else:
            text += f"⭐ <b>Твой VIP:</b> Нет\n\n"

        kb = InlineKeyboardMarkup(row_width=2)
        
        # Компактные кнопки покупки
        buttons = []
        for lvl in range(1, 8):
            buttons.append(InlineKeyboardButton(f"VIP {lvl}", callback_data=f"buy_vip_{user_id}_{lvl}"))
        
        # Добавляем кнопки по 2 в ряд
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                kb.row(buttons[i], buttons[i + 1])
            else:
                kb.row(buttons[i])
        
        if current_vip["level"] > 0:
            kb.row(InlineKeyboardButton("💰 Продать VIP", callback_data=f"sell_vip_{user_id}"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка возврата в VIP меню: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("menu_main_"))
def menu_main_callback(call):
    try:
        owner_id = int(call.data.split("_")[2])
        
        # ЗАЩИТА: проверяем, что нажимает владелец кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("💞 Тянки", callback_data=f"menu_tyanki_{call.from_user.id}"),
            InlineKeyboardButton("🐾 Питомцы", callback_data=f"menu_pets_{call.from_user.id}")
        )
        kb.add(
            InlineKeyboardButton("🚗 Машины", callback_data=f"menu_cars_{call.from_user.id}"),
            InlineKeyboardButton("🎰 Игры", callback_data=f"menu_games_{call.from_user.id}")
        )
        kb.add(InlineKeyboardButton("⭐ Випы", callback_data=f"menu_vip_{call.from_user.id}"))
        kb.add(
            InlineKeyboardButton("📖 Команды", callback_data=f"menu_help_{call.from_user.id}"),
            InlineKeyboardButton("📜 Правила", callback_data=f"menu_rules_{call.from_user.id}")
        )

        bot.edit_message_text(
            "📋 Главное меню\n\nВыбери раздел 👇",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка возврата в главное меню: {e}")

# ================== ОПТИМИЗИРОВАННАЯ СИСТЕМА ПАССИВНОГО ДОХОДА ==================

def process_vip_income():
    """Тихая обработка пассивного дохода VIP пользователей каждые 3 часа"""
    try:
        current_time = time.time()
        users_updated = False
        
        # Загружаем данные казино
        if casino_data == {}:  # Если данные не загружены
            load_casino_data()
        
        # Инициализируем vip_income_timers если пустой
        if not vip_income_timers:
            for user_id_str in casino_data.keys():
                try:
                    user_id = int(user_id_str)
                    vip_data = casino_data[user_id_str].get("vip", {})
                    if vip_data.get("level", 0) > 0:
                        # Устанавливаем текущее время если таймера нет
                        if user_id not in vip_income_timers:
                            vip_income_timers[user_id] = current_time
                except:
                    continue
        
        for user_id_str, user_data in casino_data.items():
            try:
                user_id = int(user_id_str)
                vip_data = user_data.get("vip", {})
                
                if vip_data.get("level", 0) > 0:
                    # Получаем или инициализируем таймер для пользователя
                    last_income = vip_income_timers.get(user_id)
                    
                    # Если таймера нет, устанавливаем текущее время
                    if last_income is None:
                        vip_income_timers[user_id] = current_time
                        last_income = current_time
                    
                    # Проверяем, прошло ли 3 часа с последнего начисления (10800 секунд)
                    if current_time - last_income >= 10800:
                        vip_info = VIP_LEVELS[vip_data["level"]]
                        income_amount = vip_info["income"]
                        
                        # Тихое начисление дохода (без уведомлений)
                        user_data["balance"] += income_amount
                        
                        # Обновляем время последнего начисления
                        vip_income_timers[user_id] = current_time
                        
                        # Обновляем в базе данных
                        if "last_income" not in vip_data:
                            vip_data["last_income"] = datetime.now().isoformat()
                            user_data["vip"] = vip_data
                        
                        users_updated = True
                        logger.info(f"💰 VIP доход начислен: {user_id} +{income_amount}$")
                        
            except Exception as e:
                logger.error(f"Ошибка обработки VIP дохода для {user_id_str}: {e}")
                continue
        
        # Сохраняем только если были изменения
        if users_updated:
            save_casino_data()
            logger.info("💾 VIP доход: данные сохранены")
        
    except Exception as e:
        logger.error(f"Критическая ошибка в процессе VIP дохода: {e}")

# ================== ЗАПУСК АВТОМАТИЧЕСКОГО ДОХОДА ==================

def start_vip_income_loop():
    """Запускает бесконечный цикл для начисления VIP дохода"""
    def income_loop():
        while True:
            try:
                # Ждем 3 часа (10800 секунд) перед первой проверкой
                time.sleep(10800)
                
                # Выполняем начисление дохода
                process_vip_income()
                
                # Ждем еще 3 часа до следующей проверки
                # Фактически будет проверять каждые 3 часа
                time.sleep(10800)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле VIP дохода: {e}")
                time.sleep(300)  # Ждем 5 минут при ошибке
    
    # Запускаем в отдельном потоке
    income_thread = threading.Thread(target=income_loop, daemon=True)
    income_thread.start()
    logger.info("✅ Система пассивного VIP дохода запущена (интервал: 3 часа)")

# Запускаем систему дохода при старте бота
start_vip_income_loop()

# ================== ОБНОВЛЁННЫЙ START ДЛЯ VIP ==================

@bot.message_handler(commands=['sжажаrt'])
def cmd_start(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    get_user_referral_data(user_id)

    if len(message.text.split()) > 1:
        start_param = message.text.split()[1]
        
        if start_param.startswith('ref_'):
            process_referral_join(user_id, start_param[4:])
        
        elif start_param.startswith('buy_vip_'):
            try:
                level = int(start_param.split('_')[2])
                user_data = get_user_data(user_id)
                mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

                # Проверяем, есть ли уже VIP
                if user_data["vip"]["level"] > 0:
                    current_vip = VIP_LEVELS[user_data["vip"]["level"]]
                    kb = InlineKeyboardMarkup()
                    kb.row(InlineKeyboardButton("💰 Продать VIP", callback_data=f"sell_vip_{user_id}"))
                    kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"vip_back_{user_id}"))
                    
                    bot.send_message(
                        message.chat.id,
                        f"{mention} у тебя уже есть VIP {current_vip['prefix']} {current_vip['name']}, если хочешь другой купить - продай свою по кнопке ниже 💎",
                        parse_mode="HTML",
                        reply_markup=kb
                    )
                    return

                if level not in VIP_LEVELS:
                    bot.send_message(message.chat.id, "❌ Неверный уровень VIP!")
                    return

                vip_info = VIP_LEVELS[level]
                price = level * 250000

                if user_data["balance"] < price:
                    kb = InlineKeyboardMarkup()
                    kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"vip_back_{user_id}"))
                    
                    bot.send_message(
                        message.chat.id,
                        f"💸 {mention} недостаточно средств для покупки <b>{vip_info['prefix']} VIP {vip_info['name']}</b> 😔\n\n"
                        f"💳 Нужно: <code>{format_number(price)}$</code>\n"
                        f"💰 На балансе: <code>{format_number(user_data['balance'])}$</code>\n\n"
                        f"Чтобы пополнить игровой счёт, введи команду:\n"
                        f"<code>задонатить {price}</code>\n\n"
                        f"💫 Оплата через ⭐",
                        parse_mode="HTML",
                        reply_markup=kb
                    )
                    return

                # Покупка VIP
                user_data["balance"] -= price
                user_data["vip"] = {
                    "level": level,
                    "expires": (datetime.now() + timedelta(days=30)).isoformat(),
                    "purchase_price": price,
                    "last_income": datetime.now().isoformat()
                }
                save_casino_data()

                # Устанавливаем таймер для дохода
                vip_income_timers[user_id] = time.time()

                kb = InlineKeyboardMarkup()
                kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"vip_back_{user_id}"))

                bot.send_message(
                    message.chat.id,
                    f"🎉 {mention} ты купил <b>{vip_info['prefix']} VIP {vip_info['name']}</b>, поздравляю 🎁",
                    parse_mode="HTML",
                    reply_markup=kb
                )
                return
            except:
                pass


# ================== АДМИН КОМАНДЫ ДЛЯ VIP ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("выдать вип"))
def admin_give_vip(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = message.text.split()
        if len(parts) != 5:
            bot.send_message(message.chat.id, "❌ Использование: выдать вип [id] [уровень] [дни]")
            return

        _, _, uid, lvl, days = parts
        uid, lvl, days = int(uid), int(lvl), int(days)

        if lvl not in VIP_LEVELS:
            bot.send_message(message.chat.id, "❌ Неверный уровень VIP!")
            return

        user_data = get_user_data(uid)
        user_data["vip"] = {
            "level": lvl,
            "expires": (datetime.now() + timedelta(days=days)).isoformat(),
            "purchase_price": lvl * 250000,
            "last_income": datetime.now().isoformat()
        }
        
        # Устанавливаем таймер для дохода
        vip_income_timers[uid] = time.time()
        
        save_casino_data()
        bot.send_message(
            message.chat.id,
            f"✅ VIP {VIP_LEVELS[lvl]['name']} выдан {uid} на {days} дней."
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("снять вип"))
def admin_remove_vip(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ Использование: снять вип [id]")
            return

        _, _, uid = parts
        uid = int(uid)
        user_data = get_user_data(uid)
        user_data["vip"] = {"level": 0, "expires": None}
        
        # Удаляем таймер дохода
        vip_income_timers.pop(uid, None)
        
        save_casino_data()
        bot.send_message(message.chat.id, f"✅ VIP снят с {uid}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
# ================== RP ==================

@bot.message_handler(func=lambda m: m.text and any(m.text.lower().startswith(cmd) for cmd in RP_COMMANDS))
def rp_action(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Нужно ответить на сообщение пользователя!")
        return

    user1_id = message.from_user.id
    user2_id = message.reply_to_message.from_user.id

    user1_name = message.from_user.first_name
    user2_name = message.reply_to_message.from_user.first_name

    mention1 = f'<a href="tg://user?id={user1_id}">{user1_name}</a>'
    mention2 = f'<a href="tg://user?id={user2_id}">{user2_name}</a>'

    cmd = message.text.split()[0].lower()
    if cmd in RP_COMMANDS:
        text = RP_COMMANDS[cmd].format(user1=mention1, user2=mention2)
        bot.send_message(message.chat.id, text, parse_mode="HTML")

# ================== УЛУЧШЕННЫЙ СПИСОК RP КОМАНД ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "рп")
def rp_list(message):
    # Красивое оформление заголовка
    text = "----------------------------------\n"
    text += "🕹️ <b>РП КОМАНДЫ</b> 🕹️\n"
    text += "---------------------------------\n\n"
    
    # Словарь эмодзи для каждой команды
    cmd_emojis = {
        "обнять": "🤗",
        "поцеловать": "😘", 
        "погладить": "✨",
        "пощекотать": "🪶",
        "подарить": "🎁",
        "ударить": "👊",
        "шлёпнуть": "🖐️",
        "избить": "🥊",
        "украсть": "🥷",
        "выебать": "🍆",
        "трахнуть": "🔥",
        "отсосать": "👅",
        "отлизать": "💦",
        "закурить": "🚬"
    }
    
    # Все команды в алфавитном порядке (вертикальный список)
    all_commands = sorted(RP_COMMANDS.keys())
    
    # Выводим каждую команду с новой строки
    for cmd in all_commands:
        emoji = cmd_emojis.get(cmd, "🎭")
        text += f"[{emoji}] <b>{cmd.capitalize()}</b>\n"
    
    text += "\n----------------------------------\n"
    text += "💬 <b>Работают только ответом на сообщение</b>\n"
    text += "----------------------------------"
    
    bot.send_message(
        message.chat.id, 
        text, 
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    
 
        
        # =========================================================
# 💰 Система чеков (meow coins 💰)
# =========================================================

# База SQLite используется та же, что и для казино
# Импортов новых не нужно — telebot и sqlite3 уже подключены

def init_cheques_table():
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cheques (
            code TEXT PRIMARY KEY,
            amount INTEGER,
            max_activations INTEGER,
            used_by TEXT
        )
    """)
    conn.commit()
    conn.close()

init_cheques_table()

def generate_code():
    import random, string
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def get_cheque(code):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT code, amount, max_activations, used_by FROM cheques WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "code": row[0],
            "amount": row[1],
            "max": row[2],
            "used_by": row[3].split(",") if row[3] else []
        }
    return None

def save_cheque(code, amount, max_activations):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cheques (code, amount, max_activations, used_by) VALUES (?, ?, ?, ?)",
              (code, amount, max_activations, ""))
    conn.commit()
    conn.close()

def update_cheque_used(code, used_by):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE cheques SET used_by=? WHERE code=?", (",".join(used_by), code))
    conn.commit()
    conn.close()


# =========================================================
# 🎁 Команда: чек <сумма> <активаций> (только для админов)
# =========================================================

@bot.message_handler(commands=["чек"])
def create_cheque(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Только администратор может создавать чеки.")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Использование: чек <сумма> <активаций>")
        return

    try:
        amount = int(args[1])
        max_acts = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Сумма и активации должны быть числами.")
        return

    code = generate_code()
    while get_cheque(code):
        code = generate_code()

    save_cheque(code, amount, max_acts)

    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start=check_{code}"

    text = (
        f"🧾 <b>Чек на {amount} izzzy </b>\n"
        f"🪪 Активаций: <b>{max_acts}</b>\n"
        f"💎 Награда: <b>{amount} izzzy</b>\n\n"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("АКТИВИРОВАТЬ", url=link))

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    bot.send_message(message.chat.id, f"✅ Чек создан!\nКод: <code>{code}</code>", parse_mode="HTML")


# =========================================================
# 📨 Активация чека в ЛС (через /start check_CODE)
# =========================================================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start check_"))
def activate_cheque(message):
    code = message.text.replace("/start check_", "").strip().upper()
    user_id = str(message.from_user.id)
    cheque = get_cheque(code)

    if not cheque:
        bot.send_message(message.chat.id, "❌ Этот чек не найден или уже истёк.")
        return

    if user_id in cheque["used_by"]:
        bot.send_message(message.chat.id, "⚠️ Ты уже активировал этот чек.")
        return

    if len(cheque["used_by"]) >= cheque["max"]:
        bot.send_message(message.chat.id, "⚠️ Все активации уже использованы.")
        return

    cheque["used_by"].append(user_id)
    update_cheque_used(code, cheque["used_by"])

    user_data = get_user_data(int(user_id))
    user_data["balance"] += cheque["amount"]
    save_casino_data()

    bot.send_message(
        message.chat.id,
        f"Ты активировал чек и получил <b>{cheque['amount']} izzzy на свой баланс!</b>",
        parse_mode="HTML"
    )


# =========================================================
# 💬 Инлайн режим: @bot чек <сумма> <активаций>
# =========================================================

@bot.inline_handler(lambda query: query.query.lower().startswith("чек"))
def inline_create_cheque(query):
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        result = telebot.types.InlineQueryResultArticle(
            id="no_access",
            title="🚫 Нет доступа",
            description="Только администратор может создавать чеки.",
            input_message_content=telebot.types.InputTextMessageContent(
                "⛔ Недостаточно прав для создания чека."
            )
        )
        bot.answer_inline_query(query.id, [result], cache_time=1)
        return

    parts = query.query.split()
    if len(parts) < 3:
        result = telebot.types.InlineQueryResultArticle(
            id="usage",
            title="📜 Формат: чек <сумма> <активаций>",
            description="Например: чек 1000 5",
            input_message_content=telebot.types.InputTextMessageContent(
                "💡 Пример использования: @YourBot чек 1000 5"
            )
        )
        bot.answer_inline_query(query.id, [result], cache_time=1)
        return

    try:
        amount = int(parts[1])
        max_acts = int(parts[2])
    except:
        result = telebot.types.InlineQueryResultArticle(
            id="error",
            title="⚠️ Ошибка",
            description="Сумма и активации должны быть числами.",
            input_message_content=telebot.types.InputTextMessageContent(
                "⚠️ Введите: чек <сумма> <активаций>"
            )
        )
        bot.answer_inline_query(query.id, [result], cache_time=1)
        return

    code = generate_code()
    while get_cheque(code):
        code = generate_code()
    save_cheque(code, amount, max_acts)

    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start=check_{code}"

    text = (
        f"🧾 <b>Чек на {amount} izzzy</b>\n"
        f"🪪 Активаций: <b>{max_acts}</b>\n"
        f"💎 Награда: <b>{amount} izzzy</b>\n\n"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("АКТИВИРОВАТЬ", url=link))

    result = telebot.types.InlineQueryResultArticle(
        id=code,
        title=f"🎁 Чек на {amount} 💰",
        description=f"Активаций: {max_acts}",
        input_message_content=telebot.types.InputTextMessageContent(
            text, parse_mode="HTML"
        ),
        reply_markup=markup
    )

    bot.answer_inline_query(query.id, [result], cache_time=1)


# =========================================================
# 🔍 Команда /чеки (показать все активные)
# =========================================================

@bot.message_handler(commands=["чеки"])
def list_cheques(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT code, amount, max_activations, used_by FROM cheques")
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "📭 Нет активных чеков.")
        return

    text = "📜 <b>Активные чеки:</b>\n\n"
    for row in rows:
        code, amount, max_acts, used_by = row
        used = len(used_by.split(",")) if used_by else 0
        left = max_acts - used
        text += f"• <code>{code}</code> — {amount} 💰 (осталось {left}/{max_acts})\n"

    bot.send_message(message.chat.id, text, parse_mode="HTML")
    


# ================== 🃏 НОВАЯ ИГРА "ДЖОКЕР" (JOKER) ==================
# Команда: джокер [ставка]
# Правила:
# - Начальное поле: 3 клетки (1 ряд)
# - Если игрок открывает безопасную клетку, поле расширяется на 3 новые клетки (новый ряд)
# - Максимум: 5 рядов (15 клеток)
# - Множитель за каждую безопасную клетку: +0.20
# - Если игрок натыкается на череп 💀 - проигрыш

import uuid

# Словарь для хранения активных игр
active_joker_games = {}

# Настройки игры
JOKER_ROWS = 5  # Максимальное количество рядов
JOKER_COLS = 3  # Количество колонок (всегда 3)
JOKER_MULTIPLIER_PER_CELL = 0.20  # +0.20 за каждую безопасную клетку

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("джокер"))
def joker_game_start(message):
    """
    Запуск игры "Джокер".
    Использование: джокер [ставка]
    """
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        chat_id = message.chat.id
        user_data = get_user_data(user_id)

        # --- Парсинг ставки ---
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                         f"{mention}, укажи ставку!\n\n"
                         f"🃏 <b>Игра Джокер</b>\n"
                         f"• Начальное поле: 3 клетки\n"
                         f"• За каждый ход +{JOKER_MULTIPLIER_PER_CELL:.2f} к множителю\n"
                         f"• Максимум: {JOKER_ROWS} рядов ({JOKER_ROWS * JOKER_COLS} клеток)\n"
                         f"• Попадаешь на череп 💀 - проигрыш\n\n"
                         f"<b>Пример:</b> <code>джокер 1000</code>",
                         parse_mode="HTML")
            return

        try:
            bet = int(parts[1])
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше 0!")
                return
        except ValueError:
            bot.reply_to(message, "❌ Ставка должна быть числом!")
            return

        # --- Проверка баланса ---
        if user_data["balance"] < bet:
            bot.reply_to(message,
                         f"❌ {mention}, недостаточно средств!\n\n"
                         f"💰 Нужно: <code>{format_number(bet)} izzzy</code>\n"
                         f"💳 У тебя: <code>{format_number(user_data['balance'])} izzzy</code>",
                         parse_mode="HTML")
            return

        # Списываем ставку
        user_data["balance"] -= bet
        save_casino_data()

        # Генерация уникального ID игры
        game_id = str(uuid.uuid4())[:8]

        # Создаём поле с черепами
        # В первом ряду всегда один череп
        skull_positions = []
        
        # Для каждого ряда рандомно выбираем клетку с черепом (0, 1 или 2)
        for row in range(JOKER_ROWS):
            skull_positions.append(random.randint(0, 2))

        # Сохраняем игру
        active_joker_games[game_id] = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": None,
            "bet": bet,
            "skull_positions": skull_positions,  # Список позиций черепов по рядам
            "opened_cells": [],  # Список открытых клеток (row, col)
            "current_row": 0,  # Текущий ряд (0 - первый)
            "current_multiplier": 1.0,
            "active": True,
            "max_visible_row": 0  # Максимальный видимый ряд (изначально только первый)
        }

        # Создаем клавиатуру для первого ряда
        kb = joker_keyboard(game_id, user_id, [], 0, 0, skull_positions)

        # Отправляем сообщение
        game_text = (f"🃏 <b>Джокер</b> | {mention}\n\n"
                     f"💰 Ставка: <code>{format_number(bet)} izzzy</code>\n"
                     f"📈 Текущий множитель: <b>x{1.0:.2f}</b>\n"
                     f"🎯 Ряд: <b>1/{JOKER_ROWS}</b>\n\n"
                     f"Выбери клетку 👇")
        msg = bot.send_message(chat_id, game_text, parse_mode="HTML", reply_markup=kb)

        # Сохраняем ID сообщения
        active_joker_games[game_id]["message_id"] = msg.message_id

        # Удаляем команду пользователя (для чистоты чата)
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка в игре Джокер (старт): {e}")
        bot.reply_to(message, "❌ Произошла ошибка при создании игры!")


def joker_keyboard(game_id, user_id, opened_cells, current_row, max_visible_row, skull_positions, show_cashout=False):
    """Создает клавиатуру для игры"""
    kb = InlineKeyboardMarkup()
    
    # Показываем все ряды до max_visible_row
    for row in range(max_visible_row + 1):
        row_buttons = []
        for col in range(JOKER_COLS):
            cell = (row, col)
            
            if cell in opened_cells:
                # Клетка уже открыта
                if col == skull_positions[row]:
                    # Это череп (но он не должен быть открыт, если игрок не проиграл)
                    row_buttons.append(InlineKeyboardButton("⬛", callback_data="joker_done"))
                else:
                    # Безопасная клетка
                    row_buttons.append(InlineKeyboardButton(" 🟢 ", callback_data="joker_done"))
            else:
                if row == current_row and row <= max_visible_row:
                    # Текущий ряд, который можно открывать
                    row_buttons.append(InlineKeyboardButton(f" ❓ ", callback_data=f"joker_open_{game_id}_{row}_{col}_{user_id}"))
                else:
                    # Недоступные ряды
                    row_buttons.append(InlineKeyboardButton("       ", callback_data="joker_done"))
        
        kb.row(*row_buttons)
    
    # Кнопка "Забрать выигрыш" (появляется после первого хода)
    if show_cashout and game_id in active_joker_games:
        game = active_joker_games[game_id]
        current_win = int(game["bet"] * game["current_multiplier"])
        kb.add(InlineKeyboardButton(f"💸 Забрать выигрыш", 
                                   callback_data=f"joker_cashout_{game_id}_{user_id}"))
    
    return kb


@bot.callback_query_handler(func=lambda c: c.data.startswith("joker_open_"))
def joker_open_cell(call):
    """Обработчик открытия клетки"""
    try:
        # Разбираем callback_data: joker_open_GAMEID_ROW_COL_USERID
        parts = call.data.split("_")
        game_id = parts[2]
        row = int(parts[3])
        col = int(parts[4])
        owner_id = int(parts[5])

        # ЗАЩИТА: проверяем, что нажимает владелец игры
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
            return

        # Проверяем существование игры
        game = active_joker_games.get(game_id)
        if not game:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return

        # Проверяем, активна ли игра
        if not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра уже завершена!", show_alert=True)
            return

        # Проверяем, что это текущий ряд
        if row != game["current_row"]:
            bot.answer_callback_query(call.id, "❌ Сейчас не твой ход!", show_alert=True)
            return

        # Проверяем, не открыта ли уже клетка
        if (row, col) in game["opened_cells"]:
            bot.answer_callback_query(call.id, "❌ Эта клетка уже открыта!", show_alert=True)
            return

        user_id = game["user_id"]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        skull_positions = game["skull_positions"]
        bet = game["bet"]

        # Проверяем, есть ли череп в этой клетке
        if col == skull_positions[row]:
            # 💀 ПРОИГРЫШ - наткнулся на череп
            game["active"] = False
            
            # Показываем поле с черепом
            result_kb = InlineKeyboardMarkup()
            for r in range(game["max_visible_row"] + 1):
                row_buttons = []
                for c in range(JOKER_COLS):
                    if r == row and c == col:
                        row_buttons.append(InlineKeyboardButton("💀", callback_data="joker_done"))
                    elif c == skull_positions[r]:
                        row_buttons.append(InlineKeyboardButton("💀", callback_data="joker_done"))
                    elif (r, c) in game["opened_cells"]:
                        row_buttons.append(InlineKeyboardButton(" 🟢 ", callback_data="joker_done"))
                    else:
                        row_buttons.append(InlineKeyboardButton("      ", callback_data="joker_done"))
                result_kb.row(*row_buttons)

            text = (f"💀 {mention}, <b>Ты наткнулся на череп и проиграл</b>\n\n"
                    f"💰 Ты потерял ставку: <code>{format_number(bet)} izzzy</code>")
            
            bot.edit_message_text(
                text,
                game["chat_id"],
                game["message_id"],
                parse_mode="HTML",
                reply_markup=result_kb
            )
            
            del active_joker_games[game_id]
            bot.answer_callback_query(call.id, "💀 Ты проиграл!")
            return

        # ✅ БЕЗОПАСНАЯ КЛЕТКА
        # Открываем клетку
        game["opened_cells"].append((row, col))
        
        # Увеличиваем множитель
        game["current_multiplier"] = round(game["current_multiplier"] + JOKER_MULTIPLIER_PER_CELL, 2)
        
        # Подсчитываем, сколько безопасных клеток открыто в текущем ряду
        safe_cells_in_row = 0
        for opened_cell in game["opened_cells"]:
            if opened_cell[0] == row:
                safe_cells_in_row += 1
        
        # В каждом ряду 2 безопасные клетки (3 всего, 1 череп)
        if safe_cells_in_row == 2:  # Открыты обе безопасные клетки
            # Переходим на следующий ряд, если он существует
            if game["current_row"] + 1 < JOKER_ROWS:
                game["current_row"] += 1
                game["max_visible_row"] = max(game["max_visible_row"], game["current_row"])
        
        # Проверяем, не достигнут ли максимум рядов
        if game["current_row"] >= JOKER_ROWS and safe_cells_in_row == 2:
            # 🎉 ПОБЕДА - пройдены все ряды
            game["active"] = False
            win_amount = int(bet * game["current_multiplier"])
            
            user_data = get_user_data(user_id)
            user_data["balance"] += win_amount
            save_casino_data()
            
            # Показываем поле с результатом
            result_kb = InlineKeyboardMarkup()
            for r in range(JOKER_ROWS):
                row_buttons = []
                for c in range(JOKER_COLS):
                    if c == skull_positions[r]:
                        row_buttons.append(InlineKeyboardButton(" 💀 ", callback_data="joker_done"))
                    else:
                        row_buttons.append(InlineKeyboardButton("      ", callback_data="joker_done"))
                result_kb.row(*row_buttons)
            
            text = (f"🎉 {mention}, <b>Ты прошёл все ряды и выиграл</b>\n\n"
                    f"💰 Выигрыш: <code>{format_number(win_amount)} izzzy</code>\n"
                    f"📈 Итоговый множитель: <b>x{game['current_multiplier']:.2f}</b>")
            
            bot.edit_message_text(
                text,
                game["chat_id"],
                game["message_id"],
                parse_mode="HTML",
                reply_markup=result_kb
            )
            
            del active_joker_games[game_id]
            bot.answer_callback_query(call.id, f"🎉 +{format_number(win_amount)} izzzy")
            return

        # Обновляем сообщение
        show_cashout = len(game["opened_cells"]) > 0  # Кнопка появляется после первого хода
        current_win = int(bet * game["current_multiplier"])
        
        text = (f"🃏 <b>Джокер</b> | {mention}\n\n"
                f"💰 Ставка: <code>{format_number(bet)} izzzy</code>\n"
                f"📈 Текущий множитель: <b>x{game['current_multiplier']:.2f}</b>\n"
                f"💎 Возможный выигрыш: <code>{format_number(current_win)} izzzy</code>\n"
                f"🎯 Ряд: <b>{game['current_row'] + 1}/{JOKER_ROWS}</b>\n\n"
                f"Выбери клетку 👇")
        
        kb = joker_keyboard(game_id, user_id, game["opened_cells"], game["current_row"], 
                           game["max_visible_row"], game["skull_positions"], show_cashout)
        
        bot.edit_message_text(
            text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id, f"✅ Безопасно! +{JOKER_MULTIPLIER_PER_CELL:.2f} к множителю")

    except Exception as e:
        logger.error(f"Ошибка в игре Джокер (ход): {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith("joker_cashout_"))
def joker_cashout(call):
    """Обработчик кнопки 'Забрать выигрыш'"""
    try:
        parts = call.data.split("_")
        game_id = parts[2]
        owner_id = int(parts[3])

        # ЗАЩИТА: проверяем, что нажимает владелец игры
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
            return

        # Проверяем существование игры
        game = active_joker_games.get(game_id)
        if not game:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return

        # Проверяем, активна ли игра
        if not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра уже завершена!", show_alert=True)
            return

        # Проверяем, есть ли что забирать (хотя бы одна клетка открыта)
        if len(game["opened_cells"]) == 0:
            bot.answer_callback_query(call.id, "❌ Сначала открой хотя бы одну клетку!", show_alert=True)
            return

        # Завершаем игру
        game["active"] = False
        user_id = game["user_id"]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        bet = game["bet"]
        win_amount = int(bet * game["current_multiplier"])
        
        # Начисляем выигрыш
        user_data = get_user_data(user_id)
        user_data["balance"] += win_amount
        save_casino_data()

        # Показываем поле с результатом
        result_kb = InlineKeyboardMarkup()
        skull_positions = game["skull_positions"]
        max_visible = game["max_visible_row"]
        
        for r in range(max_visible + 1):
            row_buttons = []
            for c in range(JOKER_COLS):
                if (r, c) in game["opened_cells"]:
                    row_buttons.append(InlineKeyboardButton("       ", callback_data="joker_done"))
                elif c == skull_positions[r]:
                    row_buttons.append(InlineKeyboardButton(" 💀 ", callback_data="joker_done"))
                else:
                    row_buttons.append(InlineKeyboardButton(" 🟢 ", callback_data="joker_done"))
            result_kb.row(*row_buttons)

        text = (f"✅ {mention}, <b>ты забрал выигрыш!</b>\n\n"
                f"💰 Ты получил: <code>{format_number(win_amount)} izzzy</code>\n"
                f"📈 Множитель: <b>x{game['current_multiplier']:.2f}</b>\n"
                f"🎯 Открыто рядов: <b>{max_visible + 1}</b>")

        bot.edit_message_text(
            text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML",
            reply_markup=result_kb
        )

        del active_joker_games[game_id]
        bot.answer_callback_query(call.id, f"✅ +{format_number(win_amount)} izzzy")

    except Exception as e:
        logger.error(f"Ошибка в игре Джокер (выигрыш): {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# Заглушка для неактивных кнопок
@bot.callback_query_handler(func=lambda c: c.data == "joker_done")
def joker_done_callback(call):
    bot.answer_callback_query(call.id, "🎮 Игра завершена")

print("✅ Игра 'Джокер' с расширяющимся полем успешно загружена! 🃏")
        
# ================== РЕФЕРАЛЬНАЯ СИСТЕМА (SQLite) ==================
REFERRAL_BONUS = 15000
DB_FILE = "referrals.db"

# Инициализация базы данных
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Таблица пользователей с их реферальными кодами
c.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    user_id INTEGER PRIMARY KEY,
    referral_code TEXT UNIQUE,
    referrer_id INTEGER,
    joined_at TEXT
)
""")

# Таблица связей "реферер → реферал"
c.execute("""
CREATE TABLE IF NOT EXISTS referral_links (
    referrer_id INTEGER,
    referral_id INTEGER,
    UNIQUE(referrer_id, referral_id)
)
""")

conn.commit()
conn.close()

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def generate_referral_code():
    characters = string.ascii_uppercase + string.digits
    conn = get_db()
    c = conn.cursor()
    while True:
        code = ''.join(random.choice(characters) for _ in range(8))
        c.execute("SELECT 1 FROM referrals WHERE referral_code = ?", (code,))
        if not c.fetchone():
            conn.close()
            return code
    conn.close()

def get_user_referral_data(user_id):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT referral_code, referrer_id, joined_at FROM referrals WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        referral_code = generate_referral_code()
        referrer_id = None
        joined_at = datetime.now().isoformat()

        c.execute("""
            INSERT INTO referrals (user_id, referral_code, referrer_id, joined_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, referral_code, referrer_id, joined_at))
        conn.commit()

        referrals = []
    else:
        referral_code, referrer_id, joined_at = user
        c.execute("SELECT referral_id FROM referral_links WHERE referrer_id = ?", (user_id,))
        referrals = [r[0] for r in c.fetchall()]

    conn.close()

    return {
        "user_id": user_id,
        "referral_code": referral_code,
        "referrals": referrals,
        "referrer": referrer_id,
        "joined_at": joined_at
    }

def get_referral_link(bot_username, referral_code):
    return f"https://t.me/{bot_username}?start=ref_{referral_code}"

def process_referral_join(new_user_id, referral_code):
    """Обрабатывает присоединение по реферальной ссылке"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Находим реферера по коду
        c.execute("SELECT user_id FROM referrals WHERE referral_code = ?", (referral_code,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return False
            
        referrer_id = result[0]
        
        # Проверяем, не является ли пользователь самим собой
        if new_user_id == referrer_id:
            conn.close()
            return False
            
        # Проверяем, есть ли уже реферер у пользователя
        c.execute("SELECT referrer_id FROM referrals WHERE user_id = ?", (new_user_id,))
        existing_referrer = c.fetchone()
        
        if existing_referrer and existing_referrer[0]:
            conn.close()
            return False  # Уже есть реферер
        
        # Добавляем связь и обновляем запись
        c.execute("INSERT OR IGNORE INTO referral_links (referrer_id, referral_id) VALUES (?, ?)",
                  (referrer_id, new_user_id))
        c.execute("UPDATE referrals SET referrer_id = ? WHERE user_id = ?", (referrer_id, new_user_id))
        conn.commit()
        conn.close()

        # Начисляем бонус рефереру
        referrer_user_data = get_user_data(referrer_id)
        referrer_user_data["balance"] += REFERRAL_BONUS
        save_casino_data()

        logger.info(f"✅ Бонус начислен: {referrer_id} получил {REFERRAL_BONUS}$ за {new_user_id}")
        send_referral_notifications(referrer_id, new_user_id)
        return True

    except Exception as e:
        logger.error(f"Ошибка обработки реферала: {e}")
        return False

def send_referral_notifications(referrer_id, new_user_id):
    try:
        referrer_name = bot.get_chat(referrer_id).first_name
        new_user_name = bot.get_chat(new_user_id).first_name
        referrer_mention = f'<a href="tg://user?id={referrer_id}">{referrer_name}</a>'
        new_user_mention = f'<a href="tg://user?id={new_user_id}">{new_user_name}</a>'

        bot.send_message(
            referrer_id,
            f"🎉 {referrer_mention}\n\n"
            f"💌 <b>По твоей ссылке перешёл {new_user_mention}</b>\n\n"
            f"💰 На твой счёт начислено <b>{format_number(REFERRAL_BONUS)} izzzy</b>\n"
            f"💵 Баланс: {format_number(get_user_data(referrer_id)['balance'])} izzzy\n\n"
            f"👥 Всего рефералов: {len(get_user_referral_data(referrer_id)['referrals'])}",
            parse_mode="HTML"
        )

        bot.send_message(
            new_user_id,
            f"👋 Добро пожаловать!\n\n"
            f"Ты перешёл по ссылке от {referrer_mention}!\n"
            f"🎁 Ему начислено <b>{format_number(REFERRAL_BONUS)} izzzy</b> 🎉",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")

# ================== START МЕНЮ ==================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    get_user_referral_data(user_id)

    # Обработка реферальной ссылки
    if len(message.text.split()) > 1:
        start_param = message.text.split()[1]
        if start_param.startswith('ref_'):
            process_referral_join(user_id, start_param[4:])

    # Получаем username бота для создания ссылки добавления в группу
    bot_username = bot.get_me().username
    add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"
    
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    welcome_text = (
        f"Привет {mention}, я игровой чат бот, для того чтобы узнать обо мне по больше, "
        f"напиши команду /help или <code>помощь</code>. "
        f"Если хочешь добавить меня в свой чат, <a href='{add_to_group_url}'>нажми сюда</a> "
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

# ================== КОМАНДЫ РЕФЕРАЛЬНОЙ СИСТЕМЫ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["реф", "реферал", "мой кабинет", "рефералка"])
def referral_cabinet(message):
    user_id = message.from_user.id
    ref_data = get_user_referral_data(user_id)
    referrals_count = len(ref_data["referrals"])
    total_earned = referrals_count * REFERRAL_BONUS

    referrer_info = ""
    if ref_data["referrer"]:
        try:
            referrer = bot.get_chat(ref_data["referrer"])
            referrer_info = f"\n👤 Тебя пригласил: <a href='tg://user?id={ref_data['referrer']}'>{referrer.first_name}</a>"
        except:
            referrer_info = f"\n👤 Тебя пригласил: пользователь {ref_data['referrer']}"

    text = (
        f"👤 <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n\n"
        f"💼 <b>Твой реферальный кабинет</b>\n\n"
        f"💌 За друга: <b>{format_number(REFERRAL_BONUS)} izzzy</b>\n"
        f"👥 Приглашено: <b>{referrals_count}</b>\n"
        f"💰 Заработано: <b>{format_number(total_earned)} izzzy</b>"
        f"{referrer_info}\n\n"
        f"📨 Твоя ссылка ниже 👇"
    )

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔗 Моя ссылка", callback_data=f"ref_link_{user_id}"))
    if referrals_count > 0:
        kb.add(InlineKeyboardButton("👥 Мои рефералы", callback_data=f"my_refs_{user_id}"))

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ref_link_"))
def show_referral_link(call):
    user_id = int(call.data.split("_")[2])
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return

    ref_data = get_user_referral_data(user_id)
    bot_username = bot.get_me().username
    link = get_referral_link(bot_username, ref_data["referral_code"])

    text = (
        f"🔗 <b>Твоя реферальная ссылка:</b>\n\n"
        f"<code>{link}</code>\n\n"
        f"💰 За друга: <b>{format_number(REFERRAL_BONUS)} izzzy</b>\n"
        f"👥 Твоих друзей: {len(ref_data['referrals'])}"
    )

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📤 Поделиться", url=f"https://t.me/share/url?url={urllib.parse.quote(link)}"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"back_to_ref_{user_id}"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("my_refs_"))
def show_my_referrals(call):
    user_id = int(call.data.split("_")[2])
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return

    ref_data = get_user_referral_data(user_id)
    referrals = ref_data["referrals"]
    if not referrals:
        text = "👥 У тебя пока нет рефералов.\nПригласи друзей по ссылке!"
    else:
        text = f"👥 <b>Твои рефералы ({len(referrals)}):</b>\n\n"
        for i, ref_id in enumerate(referrals, 1):
            try:
                ref_user = bot.get_chat(ref_id)
                text += f"{i}. <a href='tg://user?id={ref_id}'>{ref_user.first_name}</a>\n"
            except:
                text += f"{i}. Пользователь {ref_id}\n"
        text += f"\n💰 Всего заработано: <b>{format_number(len(referrals)*REFERRAL_BONUS)} izzzy</b>"

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"back_to_ref_{user_id}"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("back_to_ref_"))
def back_to_referral(call):
    user_id = int(call.data.split("_")[3])
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return
    
    # Создаем фейковый объект message с правильным пользователем
    class FakeMessage:
        def __init__(self, chat, from_user):
            self.chat = chat
            self.chat_id = chat.id
            self.from_user = from_user
    
    fake_message = FakeMessage(call.message.chat, call.from_user)
    referral_cabinet(fake_message)

# ================== АДМИН КОМАНДА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "рефералки")
def admin_referrals_top(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У тебя нет прав администратора.")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT referrer_id, COUNT(referral_id) as total
        FROM referral_links
        GROUP BY referrer_id
        ORDER BY total DESC
        LIMIT 50
    """)
    top = c.fetchall()
    conn.close()

    text = "🏆 <b>Топ рефералов</b>\n\n"
    if not top:
        text += "📊 Пока нет данных"
    else:
        for i, (uid, count) in enumerate(top, 1):
            try:
                user = bot.get_chat(uid)
                name = user.first_name
            except:
                name = f"User {uid}"
            text += f"{i}. <a href='tg://user?id={uid}'>{name}</a> — <b>{count}</b> реф. ({format_number(count*REFERRAL_BONUS)}$)\n"

    bot.send_message(message.chat.id, text, parse_mode="HTML")
    
    # ================== 🌱 НОВЫЙ ИВЕНТ: САДОВНИК (GARDENER) ==================
GARDENER_DB = "gardener.db"

# Инициализация базы данных
def init_gardener_db():
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    
    # Таблица с данными растений пользователя
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plant_name TEXT NOT NULL,
            plant_type TEXT NOT NULL,
            planted_at TEXT NOT NULL,
            water_level INTEGER DEFAULT 100,
            last_watered TEXT,
            grow_time_minutes INTEGER NOT NULL,
            status TEXT DEFAULT 'growing',  -- growing, ready, sold
            sell_price INTEGER NOT NULL
        )
    """)
    
    # Таблица для статистики пользователя
    c.execute("""
        CREATE TABLE IF NOT EXISTS gardener_stats (
            user_id INTEGER PRIMARY KEY,
            total_plants_ever INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            last_water_all TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_gardener_db()

# Данные растений (10 видов) - время до 60 минут
PLANTS_DATA = {
    1: {
        "name": "Подсолнух",
        "emoji": "🌻",
        "price": 5000,
        "grow_time": 30,  # минут (0.5 часа)
        "sell_multiplier": 1.5,
        "description": "Яркий и солнечный цветок"
    },
    2: {
        "name": "Клубника",
        "emoji": "🍓",
        "price": 8000,
        "grow_time": 45,  # минут (0.75 часа)
        "sell_multiplier": 1.8,
        "description": "Сладкая и ароматная ягода"
    },
    3: {
        "name": "Роза",
        "emoji": "🌹",
        "price": 12000,
        "grow_time": 60,  # минут (1 час)
        "sell_multiplier": 2.0,
        "description": "Королева цветов с божественным ароматом"
    },
    4: {
        "name": "Кактус",
        "emoji": "🌵",
        "price": 15000,
        "grow_time": 50,  # минут (50 минут)
        "sell_multiplier": 2.2,
        "description": "Неприхотливый, но колючий друг"
    },
    5: {
        "name": "Гриб",
        "emoji": "🍄",
        "price": 20000,
        "grow_time": 40,  # минут (40 минут)
        "sell_multiplier": 2.5,
        "description": "Загадочный лесной гриб"
    },
    6: {
        "name": "Мята",
        "emoji": "🌿",
        "price": 7000,
        "grow_time": 20,  # минут (20 минут)
        "sell_multiplier": 1.6,
        "description": "Ароматная и полезная трава"
    },
    7: {
        "name": "Помидор",
        "emoji": "🍅",
        "price": 10000,
        "grow_time": 35,  # минут (35 минут)
        "sell_multiplier": 1.7,
        "description": "Сочный и вкусный овощ"
    },
    8: {
        "name": "Перец",
        "emoji": "🌶️",
        "price": 18000,
        "grow_time": 55,  # минут (55 минут)
        "sell_multiplier": 2.1,
        "description": "Острый и дерзкий перец чили"
    },
    9: {
        "name": "Тыква",
        "emoji": "🎃",
        "price": 25000,
        "grow_time": 60,  # минут (1 час)
        "sell_multiplier": 2.3,
        "description": "Большая и полезная тыква"
    },
    10: {
        "name": "Сакура",
        "emoji": "🌸",
        "price": 30000,
        "grow_time": 60,  # минут (1 час)
        "sell_multiplier": 2.5,
        "description": "Нежное японское дерево"
    }
}

WATER_COOLDOWN = 30  # минут

def check_gardener_button_owner(call, user_id):
    """Проверка владельца кнопки для садовника"""
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return False
    return True

def get_user_gardener_stats(user_id):
    """Получает статистику пользователя-садовника"""
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    
    c.execute("SELECT total_plants_ever, total_earned, last_water_all FROM gardener_stats WHERE user_id = ?", (user_id,))
    stats = c.fetchone()
    
    if not stats:
        # Создаем новую запись
        c.execute("INSERT INTO gardener_stats (user_id) VALUES (?)", (user_id,))
        conn.commit()
        stats = (0, 0, None)
    
    conn.close()
    return {
        "total_plants_ever": stats[0],
        "total_earned": stats[1],
        "last_water_all": stats[2]
    }

def update_gardener_stats(user_id, plants_ever_delta=0, earned_delta=0, last_water=None):
    """Обновляет статистику садовника"""
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    
    current = get_user_gardener_stats(user_id)
    new_plants = current["total_plants_ever"] + plants_ever_delta
    new_earned = current["total_earned"] + earned_delta
    new_last_water = last_water if last_water else current["last_water_all"]
    
    c.execute("""
        INSERT OR REPLACE INTO gardener_stats 
        (user_id, total_plants_ever, total_earned, last_water_all) 
        VALUES (?, ?, ?, ?)
    """, (user_id, new_plants, new_earned, new_last_water))
    
    conn.commit()
    conn.close()

def add_plant(user_id, plant_type):
    """Добавляет новое растение пользователю"""
    plant_info = PLANTS_DATA[plant_type]
    now = datetime.now().isoformat()
    
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    
    sell_price = int(plant_info["price"] * plant_info["sell_multiplier"])
    
    c.execute("""
        INSERT INTO user_plants 
        (user_id, plant_name, plant_type, planted_at, last_watered, grow_time_minutes, sell_price) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, plant_info["emoji"] + " " + plant_info["name"], plant_type, now, now, 
          plant_info["grow_time"], sell_price))
    
    conn.commit()
    conn.close()
    
    update_gardener_stats(user_id, plants_ever_delta=1)
    return True

def get_user_plants(user_id, status_filter=None):
    """Получает растения пользователя"""
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    
    query = "SELECT id, plant_name, plant_type, planted_at, water_level, last_watered, grow_time_minutes, status, sell_price FROM user_plants WHERE user_id = ?"
    params = [user_id]
    
    if status_filter:
        if isinstance(status_filter, list):
            query += " AND status IN ({})".format(','.join(['?']*len(status_filter)))
            params.extend(status_filter)
        else:
            query += " AND status = ?"
            params.append(status_filter)
    
    c.execute(query, params)
    plants = c.fetchall()
    conn.close()
    
    return plants

def update_plant_status(plant_id, status=None, water_level=None):
    """Обновляет статус растения"""
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    
    updates = []
    params = []
    
    if status:
        updates.append("status = ?")
        params.append(status)
    
    if water_level is not None:
        updates.append("water_level = ?")
        params.append(water_level)
    
    if updates:
        query = "UPDATE user_plants SET " + ", ".join(updates) + " WHERE id = ?"
        params.append(plant_id)
        c.execute(query, params)
        conn.commit()
    
    conn.close()

def delete_plant(plant_id):
    """Удаляет растение"""
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    c.execute("DELETE FROM user_plants WHERE id = ?", (plant_id,))
    conn.commit()
    conn.close()

def water_all_plants(user_id):
    """Поливает все растения пользователя"""
    plants = get_user_plants(user_id, ["growing", "ready"])
    
    conn = sqlite3.connect(GARDENER_DB)
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    for plant in plants:
        plant_id = plant[0]
        c.execute("UPDATE user_plants SET water_level = 100, last_watered = ? WHERE id = ?", (now, plant_id))
    
    conn.commit()
    conn.close()
    
    update_gardener_stats(user_id, last_water=now)

def check_plant_readiness(user_id):
    """Проверяет, какие растения уже выросли и обновляет их статус"""
    plants = get_user_plants(user_id, "growing")
    now = datetime.now()
    
    ready_count = 0
    for plant in plants:
        plant_id = plant[0]
        planted_at = datetime.fromisoformat(plant[3])
        grow_time = timedelta(minutes=plant[6])
        
        if now >= planted_at + grow_time:
            update_plant_status(plant_id, status="ready")
            ready_count += 1
    
    return ready_count

def get_gardening_stats(user_id):
    """Получает актуальную статистику для садовника"""
    check_plant_readiness(user_id)
    
    all_plants = get_user_plants(user_id)
    growing_plants = get_user_plants(user_id, "growing")
    ready_plants = get_user_plants(user_id, "ready")
    
    return {
        "total_plants_ever": get_user_gardener_stats(user_id)["total_plants_ever"],
        "growing_count": len(growing_plants),
        "ready_count": len(ready_plants),
        "all_count": len(all_plants),
        "ready_plants": ready_plants
    }

def format_time_remaining(planted_at, grow_time_minutes):
    """Форматирует оставшееся время до созревания"""
    planted = datetime.fromisoformat(planted_at)
    ready_time = planted + timedelta(minutes=grow_time_minutes)
    now = datetime.now()
    
    if now >= ready_time:
        return "✅ Готово!"
    
    remaining = ready_time - now
    minutes = remaining.seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours > 0:
        return f"⏳ {hours}ч {minutes}м"
    else:
        return f"⏳ {minutes}м"

def can_water(user_id):
    """Проверяет, можно ли полить растения (кулдаун 30 минут)"""
    stats = get_user_gardener_stats(user_id)
    if not stats["last_water_all"]:
        return True, 0
    
    last_water = datetime.fromisoformat(stats["last_water_all"])
    now = datetime.now()
    cooldown = timedelta(minutes=WATER_COOLDOWN)
    
    if now >= last_water + cooldown:
        return True, 0
    else:
        remaining = (last_water + cooldown) - now
        minutes = remaining.seconds // 60
        seconds = remaining.seconds % 60
        return False, f"{minutes} мин {seconds} сек"
        
        # ================== КОМАНДА: ПОСАДИТЬ РАСТЕНИЕ ==================
# ================== КОМАНДА: ПОСАДИТЬ РАСТЕНИЕ (С ДОБАВЛЕНИЕМ В ПРОФИЛЬ) ==================
# Словарь для хранения кулдаунов посадки
plant_cooldowns = {}

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["посадить растение", "посадить растения", "растения"])
def plant_seedling(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Проверка кулдауна (1 минута)
    current_time = time.time()
    last_plant_time = plant_cooldowns.get(user_id, 0)
    
    if current_time - last_plant_time < 60:  # 60 секунд = 1 минута
        remaining = int(60 - (current_time - last_plant_time))
        bot.reply_to(message, 
                    f"⏳ {mention}, сажать можно раз в минуту! Подожди ещё <code>{remaining} сек</code>",
                    parse_mode="HTML")
        return
    
    # Случайный выбор саженца из списка растений
    # Можно сделать выбор случайного растения или определенного
    # Сейчас случайный, но можно изменить на выбор пользователя
    plant_num = random.choice(list(PLANTS_DATA.keys()))
    plant_info = PLANTS_DATA[plant_num]
    
    # Проверяем, хватает ли денег (опционально)
    user_data = get_user_data(user_id)
    if user_data["balance"] < plant_info["price"]:
        bot.reply_to(message,
                    f"❌ {mention}, у тебя недостаточно средств для посадки!\n\n"
                    f"💰 Нужно: <code>{format_number(plant_info['price'])} izzzy</code>\n"
                    f"💳 У тебя: <code>{format_number(user_data['balance'])} izzzy</code>\n\n"
                    f"Купить саженец можно в магазине: <code>мои растения</code> → Купить саженцы",
                    parse_mode="HTML")
        return
    
    # Списываем деньги
    user_data["balance"] -= plant_info["price"]
    save_casino_data()
    
    # Добавляем растение в профиль игрока
    add_plant(user_id, plant_num)
    
    # Обновляем время последней посадки
    plant_cooldowns[user_id] = current_time
    
    text = f"🍀 {mention} Ты посадил сажанец <code>{plant_info['emoji']} {plant_info['name']}</code>\n\n🌱 Следить за ростом: <code>мои растения</code>"
    bot.reply_to(message, text, parse_mode="HTML")
    
    logger.info(f"Пользователь {user_id} посадил растение {plant_info['name']} за {plant_info['price']}$")

# ================== КОМАНДА: МОИ РАСТЕНИЯ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мои растения", "мое растение", "мое растения"])
def my_plants(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    stats = get_gardening_stats(user_id)
    
    # Рассчитываем время до продажи (максимальное время среди растущих)
    growing_plants = get_user_plants(user_id, "growing")
    max_time_remaining = "—"
    
    if growing_plants:
        max_minutes = 0
        for plant in growing_plants:
            planted = plant[3]
            grow_time = plant[6]
            planted_dt = datetime.fromisoformat(planted)
            ready_dt = planted_dt + timedelta(minutes=grow_time)
            now = datetime.now()
            
            if now < ready_dt:
                remaining = (ready_dt - now).seconds // 60
                if remaining > max_minutes:
                    max_minutes = remaining
        
        if max_minutes > 0:
            hours = max_minutes // 60
            minutes = max_minutes % 60
            if hours > 0:
                max_time_remaining = f"{hours}ч {minutes}м"
            else:
                max_time_remaining = f"{minutes}м"
        else:
            max_time_remaining = "Скоро созреют"
    
    text = (
        f"🌿 Привет {mention}, это твое меню где ты можешь следить за своими растениями, продавать, расти.\n\n"
        f"🍀 Всего растений: <code>{stats['total_plants_ever']}</code>\n"
        f"🌰 Сейчас растёт: <code>{stats['growing_count']}</code> растений\n"
        f"🌷 Осталось ждать до продажи: <code>{max_time_remaining}</code>"
    )
    
    # Создаем клавиатуру
    kb = InlineKeyboardMarkup(row_width=2)
    
    # Кнопка Полить (всегда доступна, проверка будет в обработчике)
    kb.add(InlineKeyboardButton("💧Полить", callback_data=f"gardener_water_{user_id}"))
    
    # Кнопка Продать все (только если есть готовые растения)
    if stats['ready_count'] > 0:
        kb.add(InlineKeyboardButton("🍈 Продать все", callback_data=f"gardener_sell_all_{user_id}"))
    
    # Кнопка Купить саженцы
    kb.add(InlineKeyboardButton("🌿 Купить саженцы", callback_data=f"gardener_shop_{user_id}"))
    
    bot.reply_to(message, text, parse_mode="HTML", reply_markup=kb)

# ================== КНОПКА: ПОЛИТЬ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gardener_water_"))
def gardener_water_callback(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        if not check_gardener_button_owner(call, user_id):
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        # Проверяем кулдаун
        can_water_result, time_left = can_water(user_id)
        
        if not can_water_result:
            bot.answer_callback_query(call.id, f"⏳ Подожди {time_left} до следующего полива!", show_alert=True)
            return
        
        # Проверяем, есть ли растения
        plants = get_user_plants(user_id)
        if not plants:
            bot.answer_callback_query(call.id, "❌ У тебя нет растений для полива!", show_alert=True)
            return
        
        # Поливаем все растения
        water_all_plants(user_id)
        
        text = f"🍄 {mention}, ты успешно полил свои саженцы, они вырастут в скором времени"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Назад", callback_data=f"gardener_back_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id, "✅ Растения политы!")
        
    except Exception as e:
        logger.error(f"Ошибка полива растений: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КНОПКА: ПРОДАТЬ ВСЕ (ПОДТВЕРЖДЕНИЕ) ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gardener_sell_all_") and "confirm" not in c.data and "cancel" not in c.data)
def gardener_sell_all_prompt(call):
    try:
        # Разбираем данные: gardener_sell_all_USERID
        parts = call.data.split("_")
        user_id = int(parts[3])  # Индекс 3, потому что: gardener(0) sell(1) all(2) USERID(3)
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        stats = get_gardening_stats(user_id)
        
        if stats['ready_count'] == 0:
            bot.answer_callback_query(call.id, "❌ Нет готовых растений для продажи!", show_alert=True)
            return
        
        # Рассчитываем общую цену
        total_price = 0
        ready_plants = stats['ready_plants']
        
        for plant in ready_plants:
            total_price += plant[8]  # sell_price
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"{mention}, садовник - ты уверен что хочешь продать все свои выращенные саженцы за <code>{format_number(total_price)} izzzy</code>"
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Да", callback_data=f"gardener_confirm_sell_{user_id}"),
            InlineKeyboardButton("Нет", callback_data=f"gardener_cancel_sell_{user_id}")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка подтверждения продажи: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КНОПКА: ПРОДАТЬ ВСЕ (ПОДТВЕРЖДЕНИЕ - ДА) ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gardener_confirm_sell_"))
def gardener_confirm_sell(call):
    try:
        # Разбираем данные: gardener_confirm_sell_USERID
        parts = call.data.split("_")
        user_id = int(parts[3])  # Индекс 3, потому что: gardener(0) confirm(1) sell(2) USERID(3)
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        stats = get_gardening_stats(user_id)
        ready_plants = stats['ready_plants']
        
        if not ready_plants:
            bot.answer_callback_query(call.id, "❌ Нет готовых растений для продажи!", show_alert=True)
            return
        
        # Рассчитываем общую цену и удаляем растения
        total_price = 0
        plant_names = []
        
        for plant in ready_plants:
            plant_id = plant[0]
            plant_name = plant[1]
            plant_price = plant[8]
            
            total_price += plant_price
            plant_names.append(plant_name)
            
            # Удаляем растение
            delete_plant(plant_id)
        
        # Начисляем деньги
        user_data = get_user_data(user_id)
        user_data["balance"] += total_price
        save_casino_data()
        
        # Обновляем статистику
        update_gardener_stats(user_id, earned_delta=total_price)
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"{mention}, ты продал все свои растения за <code>{format_number(total_price)} izzzy</code>"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Назад", callback_data=f"gardener_back_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id, f"✅ +{format_number(total_price)} izzzy")
        
    except Exception as e:
        logger.error(f"Ошибка продажи растений: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КНОПКА: ПРОДАТЬ ВСЕ (ПОДТВЕРЖДЕНИЕ - НЕТ) ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gardener_cancel_sell_"))
def gardener_cancel_sell(call):
    try:
        # Разбираем данные: gardener_cancel_sell_USERID
        parts = call.data.split("_")
        user_id = int(parts[3])  # Индекс 3, потому что: gardener(0) cancel(1) sell(2) USERID(3)
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Возвращаемся в меню растений
        class FakeCall:
            def __init__(self, message, from_user, data):
                self.message = message
                self.from_user = from_user
                self.data = data
        
        fake_call = FakeCall(call.message, call.from_user, f"gardener_back_{user_id}")
        gardener_back(fake_call)
        
        bot.answer_callback_query(call.id, "❌ Продажа отменена")
        
    except Exception as e:
        logger.error(f"Ошибка отмены продажи: {e}")
        bot.answer_callback_query(call.id, "Продажа саженцев отменена", show_alert=True)
        
        # ================== КНОПКА: КУПИТЬ САЖЕНЦЫ (МАГАЗИН) ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gardener_shop_"))
def gardener_shop(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        if not check_gardener_button_owner(call, user_id):
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"🛒 {mention}, магазин саженцев:\n\n"
        
        for num, plant_data in PLANTS_DATA.items():
            text += (
                f"<b>{num}. {plant_data['emoji']} {plant_data['name']}</b>\n"
                f"   💰 Цена: <code>{format_number(plant_data['price'])} izzzy</code>\n"
                f"   ⏱ Время роста: <code>{plant_data['grow_time']} мин</code>\n"
                f"   📝 {plant_data['description']}\n\n"
            )
        
        text += (
            "\n<b>Как купить:</b>\n"
            "<code>купить сажанец [номер]</code>\n"
            "Пример: <code>купить сажанец 1</code>"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Назад", callback_data=f"gardener_back_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка магазина саженцев: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КОМАНДА: КУПИТЬ САЖАНЕЦ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить сажанец"))
def buy_seedling(message):
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, 
                       f"❌ {mention}, используй: <code>купить сажанец [номер]</code>\n\n"
                       f"Список саженцев: <code>мои растения</code> → Купить саженцы",
                       parse_mode="HTML")
            return
        
        try:
            plant_num = int(parts[2])
        except ValueError:
            bot.reply_to(message, "❌ Номер саженца должен быть числом!", parse_mode="HTML")
            return
        
        if plant_num not in PLANTS_DATA:
            bot.reply_to(message, f"❌ Саженца с номером {plant_num} не существует!", parse_mode="HTML")
            return
        
        plant_info = PLANTS_DATA[plant_num]
        user_data = get_user_data(user_id)
        
        if user_data["balance"] < plant_info["price"]:
            bot.reply_to(message,
                       f"❌ {mention}, недостаточно средств!\n\n"
                       f"💰 Нужно: <code>{format_number(plant_info['price'])} izzzy</code>\n"
                       f"💳 У тебя: <code>{format_number(user_data['balance'])} izzzy</code>",
                       parse_mode="HTML")
            return
        
        # Списываем деньги
        user_data["balance"] -= plant_info["price"]
        save_casino_data()
        
        # Сажаем растение
        add_plant(user_id, plant_num)
        
        bot.reply_to(message,
                   f"✅ {mention}, ты успешно купил и посадил <code>{plant_info['emoji']} {plant_info['name']}</code>!\n\n"
                   f"🌱 Следить за ростом: <code>мои растения</code>",
                   parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка покупки саженца: {e}")
        bot.reply_to(message, "❌ Ошибка при покупке саженца!", parse_mode="HTML")

# ================== КНОПКА: НАЗАД ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gardener_back_"))
def gardener_back(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Получаем данные для отображения
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        stats = get_gardening_stats(user_id)
        
        # Рассчитываем время до продажи
        growing_plants = get_user_plants(user_id, "growing")
        max_time_remaining = "—"
        
        if growing_plants:
            max_minutes = 0
            for plant in growing_plants:
                planted = plant[3]
                grow_time = plant[6]
                planted_dt = datetime.fromisoformat(planted)
                ready_dt = planted_dt + timedelta(minutes=grow_time)
                now = datetime.now()
                
                if now < ready_dt:
                    remaining = (ready_dt - now).seconds // 60
                    if remaining > max_minutes:
                        max_minutes = remaining
            
            if max_minutes > 0:
                hours = max_minutes // 60
                minutes = max_minutes % 60
                if hours > 0:
                    max_time_remaining = f"{hours}ч {minutes}м"
                else:
                    max_time_remaining = f"{minutes}м"
            else:
                max_time_remaining = "Скоро созреют"
        
        text = (
            f"🌿 Привет {mention}, это твое меню где ты можешь следить за своими растениями, продавать, расти.\n\n"
            f"🍀 Всего растений: <code>{stats['total_plants_ever']}</code>\n"
            f"🌰 Сейчас растёт: <code>{stats['growing_count']}</code> растений\n"
            f"🌷 Осталось ждать до продажи: <code>{max_time_remaining}</code>"
        )
        
        # Создаем клавиатуру со стикерами
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("💧 Полить", callback_data=f"gardener_water_{user_id}"))
        
        if stats['ready_count'] > 0:
            kb.add(InlineKeyboardButton("💰 Продать все", callback_data=f"gardener_sell_all_{user_id}"))
        
        kb.add(InlineKeyboardButton("🛒 Купить саженцы", callback_data=f"gardener_shop_{user_id}"))
        
        # Редактируем существующее сообщение
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка возврата: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
    
    # ================== 🍬 НОВАЯ ИГРА: КОНФЕТКА (CANDY HUNT) ==================
# Команда: конфетка [ставка] или конфета [ставка]
# Поле 2x3 (6 клеток), 3 конфеты, 3 пустых клетки

import random
import uuid

# Словарь для хранения активных игр
active_candy_games = {}

# Настройки игры
CANDY_MULTIPLIER_PER_CANDY = 0.50  # +0.35 к множителю за каждую конфету
CANDY_TOTAL_CELLS = 6               # Всего клеток 2x3
CANDY_COUNT = 3                      # Количество конфет

def create_candy_board():
    """Создает доску и прячет конфеты (3 случайных индекса от 0 до 5)"""
    candy_positions = random.sample(range(CANDY_TOTAL_CELLS), CANDY_COUNT)
    return candy_positions

def format_candy_board(opened_cells, candy_positions):
    """
    Форматирует доску для отображения.
    opened_cells: список индексов открытых клеток.
    candy_positions: список индексов, где лежат конфеты.
    """
    board = []
    for i in range(CANDY_TOTAL_CELLS):
        if i in opened_cells:
            # Если клетка открыта, показываем, что там
            if i in candy_positions:
                board.append("🍬")  # Конфета
            else:
                board.append("⬛")  # Пусто
        else:
            board.append("⚫")  # Неоткрытая клетка

    # Собираем в сетку 2x3
    return (f"{board[0]} | {board[1]} | {board[2]}\n"
            f"{board[3]} | {board[4]} | {board[5]}")

def check_candy_owner(call, user_id):
    """Проверка владельца кнопки"""
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
        return False
    return True

def candy_keyboard(game_id, user_id, opened_cells, show_cashout=False):
    """Создает клавиатуру для игры"""
    kb = InlineKeyboardMarkup(row_width=3)
    
    # Создаем кнопки для каждой клетки
    row1_buttons = []
    row2_buttons = []
    
    for i in range(CANDY_TOTAL_CELLS):
        button = InlineKeyboardButton(
            "⚫", 
            callback_data=f"candy_open_{game_id}_{i}_{user_id}"
        )
        if i < 3:
            row1_buttons.append(button)
        else:
            row2_buttons.append(button)
    
    kb.row(*row1_buttons)
    kb.row(*row2_buttons)
    
    # Кнопка "Забрать выигрыш" (появляется после нахождения хотя бы одной конфеты)
    if show_cashout:
        kb.add(InlineKeyboardButton("💸 Забрать выигрыш", callback_data=f"candy_cashout_{game_id}_{user_id}"))
    
    return kb

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(("конфетка", "конфета")))
def candy_game_start(message):
    """
    Запуск игры "Конфетка".
    Использование: конфетка [ставка]
    """
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        chat_id = message.chat.id
        user_data = get_user_data(user_id)

        # --- Парсинг ставки ---
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                         f"{mention}, укажи ставку!\n\n"
                         f"🍬 <b>Найди 3 конфеты в полях, в остальных трёх - минус ставка</b>\n\n"
                         f"<b>Пример:</b> <code>конфетка 1000</code>",
                         parse_mode="HTML")
            return

        try:
            bet = int(parts[1])
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше 0!")
                return
        except ValueError:
            bot.reply_to(message, "❌ Ставка должна быть числом!")
            return

        # --- Проверка баланса ---
        if user_data["balance"] < bet:
            bot.reply_to(message,
                         f"❌ {mention}, недостаточно средств!\n\n"
                         f"💰 Нужно: <code>{format_number(bet)} izzzy</code>\n"
                         f"💳 У тебя: <code>{format_number(user_data['balance'])} izzzy</code>",
                         parse_mode="HTML")
            return

        # Списываем ставку
        user_data["balance"] -= bet
        save_casino_data()

        # Генерация уникального ID игры
        game_id = str(uuid.uuid4())[:8]

        # Создаем доску с конфетами
        candy_positions = create_candy_board()

        # Сохраняем игру
        active_candy_games[game_id] = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": None,
            "bet": bet,
            "candy_positions": candy_positions,
            "opened_cells": [],
            "candies_found": 0,
            "current_multiplier": 1.0,
            "active": True
        }

        # Текст игры
        text = (f"{mention}, найди конфеты! 🍬\n\n"
                f"<b>Ставка:</b> <code>{format_number(bet)} izzzy</code>\n"
                f"<b>Множитель:</b> <code>x1.00</code>\n\n"
                f"{format_candy_board([], candy_positions)}")

        # Отправляем сообщение
        msg = bot.send_message(
            chat_id,
            text,
            parse_mode="HTML",
            reply_markup=candy_keyboard(game_id, user_id, [], show_cashout=False)
        )

        # Сохраняем ID сообщения
        active_candy_games[game_id]["message_id"] = msg.message_id

        # Удаляем команду пользователя (для чистоты)
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка в игре Конфетка (старт): {e}")
        bot.reply_to(message, "❌ Произошла ошибка при создании игры!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("candy_open_"))
def candy_open_cell(call):
    """Обработчик открытия клетки"""
    try:
        # Разбираем callback_data: candy_open_GAMEID_CELL_OWNERID
        parts = call.data.split("_")
        game_id = parts[2]
        cell = int(parts[3])
        owner_id = int(parts[4])

        # Проверка владельца
        if not check_candy_owner(call, owner_id):
            return

        # Проверка существования игры
        if game_id not in active_candy_games:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return

        game = active_candy_games[game_id]
        user_id = game["user_id"]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        # Проверка, активна ли игра
        if not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра уже завершена!")
            return

        # Проверка, не открыта ли уже клетка
        if cell in game["opened_cells"]:
            bot.answer_callback_query(call.id, "❌ Эта клетка уже открыта!")
            return

        # Открываем клетку
        game["opened_cells"].append(cell)

        # Проверяем, есть ли в клетке конфета
        if cell in game["candy_positions"]:
            # Нашли конфету!
            game["candies_found"] += 1
            game["current_multiplier"] = round(1.0 + (game["candies_found"] * CANDY_MULTIPLIER_PER_CANDY), 2)

            # Проверяем, все ли конфеты найдены
            if game["candies_found"] >= CANDY_COUNT:
                # Найдены все конфеты - автоматический выигрыш
                win_amount = int(game["bet"] * game["current_multiplier"])
                user_data = get_user_data(user_id)
                user_data["balance"] += win_amount
                save_casino_data()

                text = (f"{mention}, 🎉 <b>ТЫ НАШЁЛ ВСЕ КОНФЕТЫ!</b>\n\n"
                        f"💰 Выигрыш: <code>{format_number(win_amount)} izzzy</code>\n"
                        f"📈 Множитель: <b>x{game['current_multiplier']:.2f}</b>\n"
                        f"🍬 Найдено конфет: <code>{game['candies_found']}</code>\n\n"
                        f"{format_candy_board(game['opened_cells'], game['candy_positions'])}")

                game["active"] = False
                bot.edit_message_text(
                    text,
                    game["chat_id"],
                    game["message_id"],
                    parse_mode="HTML"
                )
                del active_candy_games[game_id]
                bot.answer_callback_query(call.id, "🎉 Ты выиграл!")
                return

            # Не все конфеты найдены - показываем сообщение о находке
            show_cashout = True  # После первой конфеты появляется кнопка
            text = (f"{mention}, 🍬 <b>Ты нашёл конфету!</b>\n\n"
                    f"<b>Ставка:</b> <code>{format_number(game['bet'])} izzzy</code>\n"
                    f"<b>Текущий множитель:</b> <b>x{game['current_multiplier']:.2f}</b>\n"
                    f"<b>Найдено конфет:</b> <code>{game['candies_found']}/{CANDY_COUNT}</code>\n\n"
                    f"Продолжай искать или забирай выигрыш!\n\n"
                    f"{format_candy_board(game['opened_cells'], game['candy_positions'])}")

        else:
            # Пустая клетка - проигрыш
            text = (f"{mention}, 😢 <b>Тут, к сожалению, не было конфет...</b>\n\n"
                    f"💸 Ты потерял ставку: <code>{format_number(game['bet'])} izzzy</code>\n\n"
                    f"{format_candy_board(game['opened_cells'], game['candy_positions'])}")

            game["active"] = False
            bot.edit_message_text(
                text,
                game["chat_id"],
                game["message_id"],
                parse_mode="HTML"
            )
            del active_candy_games[game_id]
            bot.answer_callback_query(call.id, "❌ Ты проиграл!")
            return

        # Обновляем сообщение
        show_cashout = game["candies_found"] > 0
        bot.edit_message_text(
            text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML",
            reply_markup=candy_keyboard(game_id, user_id, game["opened_cells"], show_cashout)
        )

        bot.answer_callback_query(call.id, f"✅ Клетка открыта!")

    except Exception as e:
        logger.error(f"Ошибка в игре Конфетка (открытие): {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("candy_cashout_"))
def candy_cashout(call):
    """Обработчик кнопки 'Забрать выигрыш'"""
    try:
        parts = call.data.split("_")
        game_id = parts[2]
        owner_id = int(parts[3])

        # Проверка владельца
        if not check_candy_owner(call, owner_id):
            return

        # Проверка существования игры
        if game_id not in active_candy_games:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return

        game = active_candy_games[game_id]
        user_id = game["user_id"]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        # Проверка, активна ли игра
        if not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра уже завершена!")
            return

        # Проверка, есть ли что забирать (должна быть найдена хотя бы одна конфета)
        if game["candies_found"] == 0:
            bot.answer_callback_query(call.id, "❌ Сначала найди хотя бы одну конфету!")
            return

        # Рассчитываем выигрыш
        win_amount = int(game["bet"] * game["current_multiplier"])
        user_data = get_user_data(user_id)
        user_data["balance"] += win_amount
        save_casino_data()

        # Формируем правильное окончание для слова "конфет"
        candy_word = "конфету" if game["candies_found"] == 1 else "конфет"

        text = (f"{mention}, ✅ <b>Ты успешно забрал выигрыш!</b>\n\n"
                f"💰 Выигрыш: <code>{format_number(win_amount)} izzzy</code>\n"
                f"📈 Множитель: <b>x{game['current_multiplier']:.2f}</b>\n"
                f"🍬 Нашёл <code>{game['candies_found']}</code> {candy_word}\n\n"
                f"{format_candy_board(game['opened_cells'], game['candy_positions'])}")

        game["active"] = False
        bot.edit_message_text(
            text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML"
        )

        del active_candy_games[game_id]
        bot.answer_callback_query(call.id, f"✅ +{format_number(win_amount)} izzzy")

    except Exception as e:
        logger.error(f"Ошибка в игре Конфетка (выигрыш): {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

print("✅ Игра 'Конфетка' (6 клеток, 3 конфеты) успешно загружена! 🍬")
    
    # ================== 💣 ИГРА "ОБЕЗВРЕДЬ БОМБУ" ==================

BOMB_COOLDOWN = 120  # 2 минуты
bomb_sessions = {}  # user_id -> данные игры
bomb_last_play = {}  # user_id -> timestamp


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("бомба"))
def bomb_game(message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "Использование: бомба <ставка>")
        return

    try:
        bet = int(args[1])
    except:
        bot.send_message(message.chat.id, "❌ Ставка должна быть числом.")
        return

    if bet <= 0:
        bot.send_message(message.chat.id, "❌ Ставка должна быть больше 0.")
        return

    user_data = get_user_data(user_id)

    if user_data["balance"] < bet:
        bot.send_message(message.chat.id, "❌ Недостаточно средств.")
        return

    # Кулдаун
    now = time.time()
    last_play = bomb_last_play.get(user_id, 0)
    if now - last_play < BOMB_COOLDOWN:
        remaining = int(BOMB_COOLDOWN - (now - last_play))
        bot.send_message(message.chat.id, f"⏳ Подожди {remaining} сек перед новой бомбой.")
        return

    # Списание ставки
    user_data["balance"] -= bet
    save_casino_data()

    # Определяем случайный правильный провод
    wires = ["red", "blue", "green"]
    good_wire = random.choice(wires)

    bomb_sessions[user_id] = {
        "bet": bet,
        "good_wire": good_wire,
        "chat_id": message.chat.id,
        "message_id": None
    }

    bomb_last_play[user_id] = now

    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🔴 Красный", callback_data=f"bomb_red_{user_id}"),
        InlineKeyboardButton("🔵 Синий", callback_data=f"bomb_blue_{user_id}"),
        InlineKeyboardButton("🟢 Зелёный", callback_data=f"bomb_green_{user_id}")
    )

    sent = bot.send_message(
        message.chat.id,
        f"💣 БОМБА АКТИВИРОВАНА!\n\n"
        f"💰 Ставка: {bet} izzzy\n"
        f"Выбери провод для обезвреживания 👇",
        reply_markup=kb
    )

    bomb_sessions[user_id]["message_id"] = sent.message_id


@bot.callback_query_handler(func=lambda c: c.data.startswith("bomb_"))
def bomb_callback(call):
    parts = call.data.split("_")
    chosen_wire = parts[1]
    owner_id = int(parts[2])

    if call.from_user.id != owner_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя бомба!", show_alert=True)
        return

    if owner_id not in bomb_sessions:
        bot.answer_callback_query(call.id, "❌ Игра не найдена.")
        return

    session = bomb_sessions.pop(owner_id)
    bet = session["bet"]
    good_wire = session["good_wire"]
    chat_id = session["chat_id"]
    message_id = session["message_id"]

    user_data = get_user_data(owner_id)

    # Победа
    if chosen_wire == good_wire:
        win_amount = int(bet * 1.8)
        user_data["balance"] += win_amount
        result_text = f"🎉 УСПЕХ!\n\nТы правильно обезвредил бомбу!\n\n💰 Выигрыш: {win_amount} izzzy"

    else:
        if chosen_wire == "red":
            lose_amount = int(bet * 0.5)
            user_data["balance"] += lose_amount
            result_text = f"💥 ЧАСТИЧНЫЙ ВЗРЫВ!\n\nТы потерял половину.\n\n💸 Вернулось: {lose_amount} izzzy"
        else:
            result_text = f"💀 БОМБА ВЗОРВАЛАСЬ!\n\nТы потерял всю ставку.\n\n💸 Потеря: {bet} izzzy"

    save_casino_data()

    bot.edit_message_text(
        result_text,
        chat_id,
        message_id
    )

    bot.answer_callback_query(call.id)
    
    
    
# ================== 🎁 НОВАЯ СИСТЕМА ПОКУПКИ ПОДАРКОВ (ТОЛЬКО СЕБЕ) ==================
# ID подарков (Telegram Premium Gifts) и их настройки
GIFTS_DATA = {
    "heart": {
        "id": "5801108895304779062",
        "name": "Сердечко",
        "emoji": "❤️",
        "base_price": 50  # Базовая цена в звездах
    },
    "tree": {
        "id": "5922558454332916696",
        "name": "Ёлочка",
        "emoji": "🎄",
        "base_price": 50
    }
}

# Текстовые оформления и их стоимость (добавляется к цене подарка)
GIFT_TEXTS = {
    "simple": {
        "text": "🎁 Подарок от Meow Game",
        "price": 0  # Бесплатный
    },
    "love": {
        "text": "💖 С любовью, от Meow Game! 💖",
        "price": 5  # +5⭐
    },
    "congrats": {
        "text": "🎉 Поздравляю! Этот подарок от Meow Game 🎉",
        "price": 5
    },
    "super": {
        "text": "✨ Ты самый лучший! Этот подарок для тебя от Meow Game! ✨",
        "price": 10
    },
    "friend": {
        "text": "🤝 Спасибо, что ты есть! От Meow Game с благодарностью 🤝",
        "price": 10
    },
    "birthday": {
        "text": "🎂 С Днём Рождения! Пусть сбываются мечты! От Meow Game 🎂",
        "price": 15
    },
    "valentine": {
        "text": "💘 С Днём Святого Валентина! Ты особенный! От Meow Game 💘",
        "price": 15
    },
    "newyear": {
        "text": "🎄 С Новым Годом! Счастья, здоровья и удачи! От Meow Game 🎄",
        "price": 15
    },
    "best": {
        "text": "👑 Ты лучший! Этот подарок только для тебя! От Meow Game 👑",
        "price": 20
    },
    "legend": {
        "text": "🌟 Легендарный подарок для легендарного человека! От Meow Game 🌟",
        "price": 25
    },
    "god": {
        "text": "⚡ Божественный подарок от богов Meow Game! Ты этого достоин! ⚡",
        "price": 30
    }
}

# Хранилище временных данных для покупок (ID пользователя -> данные)
_temp_gift_data = {}

def is_admin(user_id):
    """Проверка на администратора"""
    return user_id in ADMIN_IDS

def get_user_mention(user):
    """Создает кликабельное упоминание пользователя"""
    if user.username:
        return f"@{user.username}"
    else:
        return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

# ================== 🛒 КОМАНДА: КУПИТЬ ПОДАРОК ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить подарок"))
def gift_shop_command(message):
    """Показывает список доступных подарков для покупки"""
    user_id = message.from_user.id
    mention = get_user_mention(message.from_user)

    # Очищаем старые временные данные для этого пользователя, если они есть
    if user_id in _temp_gift_data:
        del _temp_gift_data[user_id]

    text = f"🎁 <b>Магазин подарков</b> | {mention}\n\n"
    text += "Цена указана <b>без учёта текста</b>\n"
    text += "Текст увеличивает стоимость подарка\n"
    text += "Подарок будет отправлен <b>тебе</b>!\n\n"
    text += "Выбери, что хочешь получить:\n\n"

    kb = InlineKeyboardMarkup(row_width=1)
    for gift_key, gift_data in GIFTS_DATA.items():
        text += f"{gift_data['emoji']} <b>{gift_data['name']}</b> — <code>{gift_data['base_price']}⭐</code>\n"
        # Кнопка для выбора подарка
        kb.add(InlineKeyboardButton(
            f"{gift_data['emoji']} {gift_data['name']} ({gift_data['base_price']}⭐)",
            callback_data=f"gift_select_{gift_key}_{user_id}"
        ))

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)


# ================== 🎨 ВЫБОР ТЕКСТА ДЛЯ ПОДАРКА ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gift_select_"))
def gift_select_text_callback(call):
    try:
        parts = call.data.split("_")
        gift_key = parts[2]
        owner_id = int(parts[3])

        # Проверка владельца кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        # Проверяем, существует ли такой подарок
        if gift_key not in GIFTS_DATA:
            bot.answer_callback_query(call.id, "❌ Подарок не найден!", show_alert=True)
            return

        gift_data = GIFTS_DATA[gift_key]
        mention = get_user_mention(call.from_user)

        # Сохраняем выбранный подарок во временные данные
        _temp_gift_data[owner_id] = {
            "gift_key": gift_key,
            "gift_name": gift_data["name"],
            "gift_id": gift_data["id"],
            "base_price": gift_data["base_price"],
            "step": "waiting_for_text"
        }

        # Формируем список текстов с ценами
        texts_list = ""
        for text_key, text_data in GIFT_TEXTS.items():
            price_info = f"+{text_data['price']}⭐" if text_data['price'] > 0 else "бесплатно"
            texts_list += f"• «{text_data['text']}» — {price_info}\n"

        text = (
            f"{mention}, ты выбрал: {gift_data['emoji']} <b>{gift_data['name']}</b>\n"
            f"💰 <b>Базовая цена:</b> {gift_data['base_price']}⭐\n\n"
            f"📝 <b>Выбери текст для подарка (цена добавится к базовой):</b>\n\n"
            f"{texts_list}"
        )

        kb = InlineKeyboardMarkup(row_width=1)
        for text_key, text_data in GIFT_TEXTS.items():
            price_info = f"+{text_data['price']}⭐" if text_data['price'] > 0 else "0⭐"
            kb.add(InlineKeyboardButton(
                f"{text_data['text']} ({price_info})",
                callback_data=f"gift_text_{text_key}_{owner_id}"
            ))

        # Кнопка отмены
        kb.add(InlineKeyboardButton("Отменить", callback_data=f"gift_cancel_{owner_id}"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка gift_select_text_callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ================== 📝 ВЫБОР ТЕКСТА ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gift_text_"))
def gift_text_callback(call):
    try:
        parts = call.data.split("_")
        text_key = parts[2]
        owner_id = int(parts[3])

        # Проверка владельца кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        # Проверяем временные данные
        if owner_id not in _temp_gift_data or _temp_gift_data[owner_id].get("step") != "waiting_for_text":
            bot.answer_callback_query(call.id, "❌ Сессия покупки истекла! Начни заново.", show_alert=True)
            return

        # Проверяем, существует ли такой текст
        if text_key not in GIFT_TEXTS:
            bot.answer_callback_query(call.id, "❌ Текст не найден!", show_alert=True)
            return

        text_data = GIFT_TEXTS[text_key]
        gift_data = _temp_gift_data[owner_id]

        # Рассчитываем итоговую цену
        total_price = gift_data["base_price"] + text_data["price"]

        # Сохраняем выбранный текст и итоговую цену
        _temp_gift_data[owner_id]["text"] = text_data["text"]
        _temp_gift_data[owner_id]["text_price"] = text_data["price"]
        _temp_gift_data[owner_id]["total_price"] = total_price
        _temp_gift_data[owner_id]["step"] = "ready_for_payment"

        mention = get_user_mention(call.from_user)
        gift_emoji = GIFTS_DATA[gift_data["gift_key"]]["emoji"]

        text = (
            f"{mention}, ты выбрал:\n"
            f"🎁 Подарок: {gift_emoji} <b>{gift_data['gift_name']}</b> — {gift_data['base_price']}⭐\n"
            f"📝 Текст: «{text_data['text']}» — +{text_data['price']}⭐\n"
            f"💰 Итого к оплате: <b>{total_price}⭐</b>\n\n"
            f"Подарок будет отправлен <b>тебе</b>!\n\n"
            f"👇 Нажми кнопку ниже для оплаты"
        )

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f" Оплатить {total_price}⭐", callback_data=f"gift_pay_{owner_id}"))
        kb.add(InlineKeyboardButton(" Отменить", callback_data=f"gift_cancel_{owner_id}"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка gift_text_callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ================== 💳 ОПЛАТА ПОДАРКА ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gift_pay_"))
def gift_pay_callback(call):
    try:
        owner_id = int(call.data.split("_")[2])

        # Проверка владельца кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        # Проверяем временные данные
        if owner_id not in _temp_gift_data or _temp_gift_data[owner_id].get("step") != "ready_for_payment":
            bot.answer_callback_query(call.id, "❌ Сессия покупки истекла! Начни заново.", show_alert=True)
            return

        gift_data = _temp_gift_data[owner_id]

        # Проверяем, админ ли отправитель
        if is_admin(owner_id):
            # Админ может получать бесплатно
            process_free_gift_for_admin(call, owner_id)
        else:
            # Обычный пользователь - выставляем счет
            create_gift_invoice(call, owner_id)

    except Exception as e:
        logger.error(f"Ошибка gift_pay_callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ================== 💳 СОЗДАНИЕ ИНВОЙСА ДЛЯ ОПЛАТЫ ==================
def create_gift_invoice(call, owner_id):
    """Создает инвойс для оплаты подарка звездами"""
    try:
        gift_data = _temp_gift_data[owner_id]

        # Создаем платеж в базе
        payment_id = create_star_payment(owner_id, gift_data["total_price"], 0)

        title = f"Покупка подарка: {GIFTS_DATA[gift_data['gift_key']]['emoji']} {gift_data['gift_name']}"
        description = f"{gift_data['text']}"
        currency = "XTR"  # Telegram Stars

        price = types.LabeledPrice(label=gift_data['gift_name'], amount=gift_data["total_price"])

        # Удаляем сообщение с кнопками
        bot.delete_message(call.message.chat.id, call.message.message_id)

        # Отправляем инвойс
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=title,
            description=description,
            invoice_payload=f"gift_payment_{payment_id}_{owner_id}",
            provider_token="",
            currency=currency,
            prices=[price],
            start_parameter="buy-gift"
        )

        logger.info(f"Создан инвойс для покупки подарка пользователем {owner_id} на {gift_data['total_price']}⭐")
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка create_gift_invoice: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при создании платежа!", show_alert=True)


# ================== 👑 БЕСПЛАТНАЯ ОТПРАВКА ДЛЯ АДМИНА ==================
def process_free_gift_for_admin(call, owner_id):
    """Отправляет подарок бесплатно для администратора"""
    try:
        gift_data = _temp_gift_data[owner_id]
        admin_mention = get_user_mention(call.from_user)

        # Отправляем подарок
        success, result_text = send_telegram_gift(
            chat_id=call.message.chat.id,
            user_id=owner_id,  # Отправляем самому себе
            gift_id=gift_data["gift_id"],
            text=gift_data["text"]
        )

        if success:
            bot.edit_message_text(
                f"✅ {admin_mention}, подарок <b>{gift_data['gift_name']}</b> успешно отправлен тебе! (бесплатно, как админу)\n"
                f"📝 Текст: «{gift_data['text']}»\n"
                f"💰 Экономия: {gift_data['total_price']}⭐",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            logger.info(f"Админ {owner_id} получил бесплатный подарок {gift_data['gift_name']}")
        else:
            bot.edit_message_text(
                f"❌ {admin_mention}, ошибка при отправке подарка: {result_text}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            logger.error(f"Ошибка отправки подарка админу {owner_id}: {result_text}")

        # Очищаем временные данные
        if owner_id in _temp_gift_data:
            del _temp_gift_data[owner_id]

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка process_free_gift_for_admin: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при отправке подарка!", show_alert=True)


# ================== ✅ ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ ==================
@bot.pre_checkout_query_handler(func=lambda q: q.invoice_payload.startswith("gift_payment_"))
def gift_pre_checkout(pre_q):
    """Подтверждение предоплаты"""
    bot.answer_pre_checkout_query(pre_q.id, ok=True)


@bot.message_handler(content_types=['successful_payment'], func=lambda m: m.successful_payment.invoice_payload.startswith("gift_payment_"))
def gift_payment_success(message):
    """Обработка успешной оплаты подарка"""
    try:
        payload = message.successful_payment.invoice_payload
        parts = payload.split("_")
        payment_id = parts[2]
        owner_id = int(parts[3])

        # Проверяем, что платёж принадлежит этому пользователю
        if message.from_user.id != owner_id:
            bot.send_message(message.chat.id, "❌ Ошибка: платёж принадлежит другому пользователю!")
            return

        # Получаем информацию о платеже из базы
        payment_info = get_star_payment(payment_id)
        if not payment_info:
            bot.send_message(message.chat.id, "⚠️ Платёж не найден в базе, но звёзды списаны. Обратитесь к администратору!")
            return

        # Помечаем платёж как завершённый
        complete_star_payment(payment_id)

        # Проверяем временные данные
        if owner_id not in _temp_gift_data:
            bot.send_message(message.chat.id, "⚠️ Данные покупки не найдены, но звёзды списаны. Обратитесь к администратору!")
            return

        gift_data = _temp_gift_data[owner_id]
        mention = get_user_mention(message.from_user)

        # Отправляем подарок
        success, result_text = send_telegram_gift(
            chat_id=message.chat.id,
            user_id=owner_id,  # Отправляем самому себе
            gift_id=gift_data["gift_id"],
            text=gift_data["text"]
        )

        if success:
            bot.send_message(
                message.chat.id,
                f"✅ {mention}, спасибо за покупку!\n"
                f"Подарок <b>{gift_data['gift_name']}</b> успешно отправлен тебе!\n"
                f"📝 Текст: «{gift_data['text']}»\n"
                f"💰 Списано: {gift_data['total_price']}⭐",
                parse_mode="HTML"
            )
            logger.info(f"Пользователь {owner_id} купил подарок {gift_data['gift_name']} за {gift_data['total_price']}⭐")
        else:
            bot.send_message(
                message.chat.id,
                f"❌ {mention}, произошла ошибка при отправке подарка: {result_text}\n"
                f"Звёзды списаны, но подарок не доставлен. Обратитесь к администратору!",
                parse_mode="HTML"
            )
            logger.error(f"Ошибка отправки подарка пользователю {owner_id} после оплаты: {result_text}")

        # Очищаем временные данные
        if owner_id in _temp_gift_data:
            del _temp_gift_data[owner_id]

    except Exception as e:
        logger.error(f"Ошибка gift_payment_success: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке платежа! Обратитесь к администратору.")


# ================== ❌ ОТМЕНА ПОКУПКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("gift_cancel_"))
def gift_cancel_callback(call):
    try:
        owner_id = int(call.data.split("_")[2])

        # Проверка владельца кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        # Очищаем временные данные
        if owner_id in _temp_gift_data:
            del _temp_gift_data[owner_id]

        mention = get_user_mention(call.from_user)

        bot.edit_message_text(
            f"❌ {mention}, покупка подарка отменена.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id, "✅ Отменено")

    except Exception as e:
        logger.error(f"Ошибка gift_cancel_callback: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ================== 📦 ФУНКЦИЯ ОТПРАВКИ ПОДАРКА ==================
def send_telegram_gift(chat_id, user_id, gift_id, text):
    """
    Отправляет подарок через Telegram API
    Возвращает (True, "OK") при успехе или (False, "описание ошибки") при неудаче
    """
    try:
        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "gift_id": gift_id,
            "text": text
        }

        response = requests.post(
            f"https://api.telegram.org/bot{bot.token}/sendGift",
            json=params,
            timeout=15
        )

        response_data = response.json()

        if response.status_code == 200 and response_data.get('ok'):
            return True, "OK"

        # Обработка ошибок
        error_code = response_data.get('error_code')
        error_message = response_data.get('description', 'Неизвестная ошибка')

        if error_code == 400:
            if "gift not available" in error_message.lower():
                return False, "Этот подарок недоступен в данном регионе"
            elif "user not found" in error_message.lower():
                return False, "Пользователь не найден"
            else:
                return False, f"Ошибка запроса: {error_message}"

        elif error_code == 403:
            return False, "У бота недостаточно прав для отправки подарков"

        elif error_code == 429:
            return False, "Слишком много запросов. Попробуйте позже"

        else:
            return False, f"Ошибка при отправке подарка: {error_message}"

    except requests.exceptions.Timeout:
        return False, "Время ожидания истекло. Попробуйте позже."

    except requests.exceptions.RequestException as req_err:
        return False, f"Сетевая ошибка: {req_err}"

    except Exception as e:
        return False, f"Внутренняя ошибка: {str(e)}"

print("✅ Система покупки подарков загружена (тексты платные, только себе)")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "статистика бота")
def bot_stats(message):
    # Проверяем, является ли пользователь админом
    if message.from_user.id not in ADMIN_IDS:
        # Игнорируем обычных пользователей (бот молчит)
        logger.info(f"Пользователь {message.from_user.id} попытался вызвать статистику бота")
        return
    
    try:
        # Быстрый подсчет пользователей (просто количество записей в casino_data)
        total_users = len(casino_data)
        
        # Подсчет пользователей с положительным балансом
        users_with_balance = 0
        total_balance = 0
        max_balance = 0
        max_balance_user = None
        
        # Один проход по данным для сбора всей статистики
        for uid_str, data in casino_data.items():
            bal = data.get("balance", 0)
            if bal > 0:
                users_with_balance += 1
                total_balance += bal
                
                if bal > max_balance:
                    max_balance = bal
                    max_balance_user = int(uid_str)
        
        # Формируем текст статистики
        text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 <b>Пользователей в базе:</b> <code>{total_users}</code>\n"
            f"💰 <b>Активных игроков:</b> <code>{users_with_balance}</code>\n"
            f"💵 <b>Общий баланс:</b> <code>{format_number(total_balance)}$</code>\n"
            f"🏆 <b>Максимальный баланс:</b> <code>{format_number(max_balance)}$</code>"
        )
        
        # Добавляем информацию о рекордсмене, если есть
        if max_balance_user:
            try:
                user = bot.get_chat(max_balance_user)
                user_name = user.first_name
                text += f"\n👑 <b>Рекордсмен:</b> <a href=\"tg://user?id={max_balance_user}\">{user_name}</a>"
            except:
                text += f"\n👑 <b>Рекордсмен ID:</b> <code>{max_balance_user}</code>"
        
        # Отправляем статистику
        bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)
        
        logger.info(f"Админ {message.from_user.id} запросил статистику бота")
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики бота: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при получении статистики")
# ================== 🎲 НОВАЯ ИГРА: ЛЕСТНИЦА (LADDER) ==================
# Команда: лестница [ставка]
# Суть: Игроку показывается число от 1 до 100.
# Нужно угадать, следующее число будет больше или меньше текущего.
# Можно остановиться в любой момент и забрать текущий выигрыш.

import random
import uuid
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Словарь для хранения активных игр
active_ladder_games = {}

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("лестница"))
def ladder_game_start(message):
    """
    Запуск игры "Лестница".
    Использование: лестница [ставка]
    """
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        chat_id = message.chat.id
        user_data = get_user_data(user_id)

        # --- Парсинг ставки ---
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                         "❌ Укажи ставку!\n"
                         "Пример: <code>лестница 1000</code>",
                         parse_mode="HTML")
            return

        try:
            bet = int(parts[1])
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше 0!")
                return
        except ValueError:
            bot.reply_to(message, "❌ Ставка должна быть числом!")
            return

        # --- Проверка баланса ---
        if user_data["balance"] < bet:
            bot.reply_to(message,
                         f"❌ Недостаточно средств!\n"
                         f"💰 Нужно: {format_number(bet)} izzzy\n"
                         f"💳 У тебя: {format_number(user_data['balance'])} izzzy",
                         parse_mode="HTML")
            return

        # Списываем ставку
        user_data["balance"] -= bet
        save_casino_data()

        # Генерация первого числа
        first_number = random.randint(1, 100)

        # Генерация уникального ID игры
        game_id = str(uuid.uuid4())[:8]

        # Сохраняем игру
        active_ladder_games[game_id] = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": None,
            "bet": bet,
            "current_multiplier": 1.0,
            "current_number": first_number,
            "last_number": first_number,
            "active": True,
            "step": 0
        }

        # Создаем клавиатуру (ЗАЩИТА: в колбеке передаём ID игры и владельца)
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("⬆️", callback_data=f"ladder_higher_{game_id}_{user_id}"),
            InlineKeyboardButton("⬇️", callback_data=f"ladder_lower_{game_id}_{user_id}")
        )
        kb.add(InlineKeyboardButton("Забрать выигрыш", callback_data=f"ladder_cashout_{game_id}_{user_id}"))

        text = (
            f"{mention}, твоя ставка: <code>{format_number(bet)} izzzy</code>\n"
            f"Текущий множитель: <b>x{active_ladder_games[game_id]['current_multiplier']:.2f}</b>\n\n"
            f"<b>Число: {first_number}</b>\n\n"
            f"Следующее число будет больше ⬆️ или меньше ⬇️?"
        )

        msg = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
        active_ladder_games[game_id]["message_id"] = msg.message_id

        # Удаляем команду пользователя (для чистоты)
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка в игре Лестница (старт): {e}")
        bot.reply_to(message, "❌ Произошла ошибка при создании игры!")


@bot.callback_query_handler(func=lambda c: c.data.startswith("ladder_"))
def ladder_game_callback(call):
    """
    Обработчик ходов в игре "Лестница".
    """
    try:
        data_parts = call.data.split("_")
        action = data_parts[1]  # higher, lower, cashout
        game_id = data_parts[2]
        owner_id = int(data_parts[3])

        # --- ЗАЩИТА: проверяем владельца ---
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
            return

        # --- Проверка существования игры ---
        if game_id not in active_ladder_games:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return

        game = active_ladder_games[game_id]

        # Дополнительная проверка на случай коллизий
        if call.from_user.id != game["user_id"]:
            bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
            return

        # --- Проверка, активна ли игра ---
        if not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра уже завершена!")
            return

        user_id = game["user_id"]
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        # --- ОБРАБОТКА: ЗАБРАТЬ ВЫИГРЫШ ---
        if action == "cashout":
            game["active"] = False
            win_amount = int(game["bet"] * game["current_multiplier"])

            # Начисляем выигрыш
            user_data["balance"] += win_amount
            save_casino_data()

            result_text = (
                f"🎉 {mention}, ты вовремя остановился!\n\n"
                f"💰 Выигрыш: <code>{format_number(win_amount)} izzzy</code>\n"
                f"📈 Множитель: <b>x{game['current_multiplier']:.2f}</b>"
            )

            bot.edit_message_text(
                result_text,
                game["chat_id"],
                game["message_id"],
                parse_mode="HTML"
            )

            del active_ladder_games[game_id]
            bot.answer_callback_query(call.id)
            return

        # --- ОБРАБОТКА: ХОД ---
        if action in ["higher", "lower"]:
            # Генерируем новое число
            new_number = random.randint(1, 100)

            # Проверка
            is_higher = new_number > game["current_number"]
            is_lower = new_number < game["current_number"]
            is_equal = new_number == game["current_number"]

            player_won = False
            if action == "higher" and is_higher:
                player_won = True
            elif action == "lower" and is_lower:
                player_won = True

            # --- Ничья (проигрыш) ---
            if is_equal:
                game["active"] = False
                result_text = (
                    f"😵 {mention}, выпало то же число <b>{new_number}</b>.\n"
                    f"💸 Ты потерял <code>{format_number(game['bet'])} izzzy</code>."
                )
                bot.edit_message_text(
                    result_text,
                    game["chat_id"],
                    game["message_id"],
                    parse_mode="HTML"
                )
                del active_ladder_games[game_id]
                bot.answer_callback_query(call.id, "❌ Ничья! Ты проиграл.")
                return

            # --- Победа ---
            if player_won:
                game["current_multiplier"] = round(game["current_multiplier"] + 0.2, 2)
                game["step"] += 1
                game["last_number"] = game["current_number"]
                game["current_number"] = new_number

                potential_win = int(game["bet"] * game["current_multiplier"])

                # Обновляем клавиатуру (с защитой)
                kb = InlineKeyboardMarkup(row_width=2)
                kb.add(
                    InlineKeyboardButton("⬆️", callback_data=f"ladder_higher_{game_id}_{user_id}"),
                    InlineKeyboardButton("⬇️", callback_data=f"ladder_lower_{game_id}_{user_id}")
                )
                kb.add(InlineKeyboardButton("Забрать выигрыш", callback_data=f"ladder_cashout_{game_id}_{user_id}"))

                text = (
                    f"{mention}, ставка: <code>{format_number(game['bet'])}$</code>\n"
                    f"Множитель: <b>x{game['current_multiplier']:.2f}</b>\n"
                    f"Возможный выигрыш: <code>{format_number(potential_win)} izzzy</code>\n\n"
                    f"Было: <b>{game['last_number']}</b>\n"
                    f"<b>Стало: {game['current_number']}</b>\n\n"
                    f"Дальше?"
                )

                bot.edit_message_text(
                    text,
                    game["chat_id"],
                    game["message_id"],
                    parse_mode="HTML",
                    reply_markup=kb
                )
                bot.answer_callback_query(call.id, f"✅ Угадал! Множитель +0.2")

            # --- Проигрыш ---
            else:
                game["active"] = False
                result_text = (
                    f"💥 {mention}, ты ошибся!\n\n"
                    f"Ты выбрал <b>{'ВЫШЕ' if action == 'higher' else 'НИЖЕ'}</b>, а выпало <b>{new_number}</b>.\n"
                    f"💸 Ты потерял ставку: <code>{format_number(game['bet'])} izzzy</code>"
                )
                bot.edit_message_text(
                    result_text,
                    game["chat_id"],
                    game["message_id"],
                    parse_mode="HTML"
                )
                del active_ladder_games[game_id]
                bot.answer_callback_query(call.id, "❌ Ты проиграл!")

    except Exception as e:
        logger.error(f"Ошибка в игре Лестница (ход): {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

print("✅ Новая игра 'Лестница' успешно добавлена!")

# ================== НАЛОГОВАЯ СИСТЕМА ==================
TAX_DB = "taxes.db"

# Инициализация базы данных налогов
def init_tax_db():
    conn = sqlite3.connect(TAX_DB)
    c = conn.cursor()
    
    # Таблица для хранения истории налоговых списаний
    c.execute("""
        CREATE TABLE IF NOT EXISTS tax_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            balance_before INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            tax_date TEXT NOT NULL
        )
    """)
    
    # Таблица для хранения статистики пользователя
    c.execute("""
        CREATE TABLE IF NOT EXISTS tax_stats (
            user_id INTEGER PRIMARY KEY,
            total_tax_paid INTEGER DEFAULT 0,
            last_tax_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ База данных налогов инициализирована")

init_tax_db()

def record_tax_payment(user_id, amount, balance_before, balance_after):
    """Записывает налоговое списание в историю"""
    conn = sqlite3.connect(TAX_DB)
    c = conn.cursor()
    
    tax_date = datetime.now().isoformat()
    
    # Записываем в историю
    c.execute("""
        INSERT INTO tax_history (user_id, amount, balance_before, balance_after, tax_date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, balance_before, balance_after, tax_date))
    
    # Обновляем статистику пользователя
    c.execute("""
        INSERT OR REPLACE INTO tax_stats (user_id, total_tax_paid, last_tax_date)
        VALUES (?, COALESCE((SELECT total_tax_paid FROM tax_stats WHERE user_id = ?), 0) + ?, ?)
    """, (user_id, user_id, amount, tax_date))
    
    conn.commit()
    conn.close()

def get_user_tax_history(user_id, limit=10):
    """Получает историю налоговых списаний пользователя"""
    conn = sqlite3.connect(TAX_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT amount, tax_date 
        FROM tax_history 
        WHERE user_id = ? 
        ORDER BY tax_date DESC 
        LIMIT ?
    """, (user_id, limit))
    
    history = c.fetchall()
    conn.close()
    return history

def get_user_tax_stats(user_id):
    """Получает статистику налоговых списаний пользователя"""
    conn = sqlite3.connect(TAX_DB)
    c = conn.cursor()
    
    c.execute("SELECT total_tax_paid, last_tax_date FROM tax_stats WHERE user_id = ?", (user_id,))
    stats = c.fetchone()
    conn.close()
    
    if stats:
        return {
            "total_paid": stats[0],
            "last_date": stats[1]
        }
    return {
        "total_paid": 0,
        "last_date": None
    }

# ================== АДМИН КОМАНДА: СНЯТЬ НАЛОГ (ИСПРАВЛЕННАЯ) ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "снять налог")
def admin_collect_tax(message):
    user_id = message.from_user.id
    
    # Проверяем, админ ли
    if user_id not in ADMIN_IDS:
        # Админ команда - бот игнорирует
        return
    
    # Отправляем начальное сообщение
    status_msg = bot.reply_to(message, 
        "🧾 <b>Сбор налогов начат...</b>\n\n"
        "⏳ Обработка...",
        parse_mode="HTML"
    )
    
    # Счетчики
    total_collected = 0
    taxed_balance_users = 0
    taxed_bank_users = 0
    skipped_users = 0
    processed = 0
    
    # Проходим по всем пользователям
    for user_id_str, user_data in casino_data.items():
        processed += 1
        uid = int(user_id_str)
        balance = user_data.get("balance", 0)
        
        # Получаем банковский счет пользователя
        bank_account = get_bank_account(uid)
        bank_balance = bank_account.get("balance", 0) if bank_account else 0
        
        # Обновляем статус каждые 50 пользователей
        if processed % 50 == 0:
            try:
                bot.edit_message_text(
                    f"🧾 <b>Сбор налогов...</b>\n\n"
                    f"📊 Обработано: <code>{processed}</code> пользователей\n"
                    f"💰 Собрано: <code>{format_number(total_collected)}$</code>\n"
                    f"✅ Обложено налогом (баланс): <code>{taxed_balance_users}</code>\n"
                    f"✅ Обложено налогом (банк): <code>{taxed_bank_users}</code>\n"
                    f"⏭ Пропущено: <code>{skipped_users}</code>",
                    status_msg.chat.id,
                    status_msg.message_id,
                    parse_mode="HTML"
                )
            except:
                pass
        
        user_taxed = False
        user_tax_amount = 0
        
        # Налог с основного баланса (> 100 млн)
        if balance > 100000000:
            tax_amount = int(balance * 0.1)
            new_balance = balance - tax_amount
            
            # Сохраняем старый баланс для записи
            old_balance = user_data["balance"]
            
            # Списываем налог
            user_data["balance"] = new_balance
            
            user_tax_amount += tax_amount
            user_taxed = True
            taxed_balance_users += 1
        
        # Налог с банковского счета (> 1 млрд)
        if bank_balance > 1000000000:  # 1 миллиард
            bank_tax_amount = int(bank_balance * 0.1)
            new_bank_balance = bank_balance - bank_tax_amount
            
            # Обновляем банковский счет
            conn = sqlite3.connect(BANK_DB)
            c = conn.cursor()
            c.execute("UPDATE bank_accounts SET balance = ? WHERE user_id = ?", 
                     (new_bank_balance, uid))
            conn.commit()
            conn.close()
            
            user_tax_amount += bank_tax_amount
            user_taxed = True
            taxed_bank_users += 1
        
        # Если был налог, записываем в историю
        if user_taxed:
            total_collected += user_tax_amount
            record_tax_payment(uid, user_tax_amount, balance + bank_balance, 
                              (balance - (balance if balance > 100000000 else 0)) + 
                              (bank_balance - (bank_tax_amount if bank_balance > 1000000000 else 0)))
        else:
            skipped_users += 1
    
    # Сохраняем все изменения
    save_casino_data()
    
    # Формируем итоговый отчет
    final_text = (
        f"✅ <b>СБОР НАЛОГОВ ЗАВЕРШЕН</b> ✅\n\n"
        f"📊 <b>СТАТИСТИКА:</b>\n"
        f"• Всего обработано пользователей: <code>{processed}</code>\n"
        f"• Обложено налогом (баланс >100M$): <code>{taxed_balance_users}</code>\n"
        f"• Обложено налогом (банк >1B$): <code>{taxed_bank_users}</code>\n"
        f"• Всего обложено налогом: <code>{taxed_balance_users + taxed_bank_users}</code>\n"
        f"• Пропущено (без налогов): <code>{skipped_users}</code>\n"
        f"• Всего собрано налогов: <code>{format_number(total_collected)}$</code>\n\n"
        f"📅 Дата сбора: <b>{datetime.now().strftime('%d.%m.%Y %H:%M')}</b>"
    )
    
    bot.edit_message_text(
        final_text,
        status_msg.chat.id,
        status_msg.message_id,
        parse_mode="HTML"
    )
    
    logger.info(f"Админ {message.from_user.id} провел сбор налогов. Собрано: {total_collected}$")

# ================== КОМАНДА ДЛЯ ПОЛЬЗОВАТЕЛЕЙ: МОЙ НАЛОГ ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "мой налог")
def my_tax_info(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Получаем статистику пользователя
    stats = get_user_tax_stats(user_id)
    history = get_user_tax_history(user_id, 10)  # Последние 10 списаний
    
    # Формируем текст ответа
    if stats["total_paid"] > 0:
        text = (
            f"📄 <b>Статистика списаний ваших налогов под 10%:</b>\n\n"
        )
        
        # Добавляем историю списаний
        for amount, tax_date in history:
            # Форматируем дату для красивого отображения
            try:
                date_obj = datetime.fromisoformat(tax_date)
                formatted_date = date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                formatted_date = tax_date
                
            text += f"<code>{format_number(amount)} izzzy</code> - <b>{formatted_date}</b>\n"
        
        # Добавляем итоговую статистику
        text += f"\n💰 <b>Всего уплачено налогов:</b> <code>{format_number(stats['total_paid'])} izzzy</code>"
        
        if stats["last_date"]:
            try:
                last_date_obj = datetime.fromisoformat(stats["last_date"])
                last_formatted = last_date_obj.strftime("%d.%m.%Y %H:%M")
                text += f"\n📅 <b>Последний налог:</b> {last_formatted}"
            except:
                pass
    else:
        text = (
            f"📄 <b>Статистика списаний ваших налогов под 10%:</b>\n\n"
            f"<i>У вас пока не было налоговых списаний.</i>"
        )
    
    # Отправляем ответом на сообщение пользователя
    bot.reply_to(message, text, parse_mode="HTML")

print("✅ Налоговая система загружена и готова к работе! 🧾")
    
# ================== АДМИН-КОМАНДЫ ДЛЯ ГРУПП ==================

def mention(user):
    name = user.first_name or "Пользователь"
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def is_chat_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

def is_bot_admin(chat_id):
    try:
        me = bot.get_me()
        member = bot.get_chat_member(chat_id, me.id)
        return member.status in ("administrator", "creator")
    except:
        return False

def get_target_user(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None

# ================== КОМАНДА: /admins ==================
@bot.message_handler(commands=['admins'])
def admins_help(message):
    help_text = (
        "<b>🌰 Admin Tools | Команды администраторов для ваших чатов:</b>\n\n"
        "1. <b>мут (время) (причина)</b> — Ограничить отправку сообщений.\n"
        "   Пример: <code>мут 30 спам</code> (ответом на сообщение)\n\n"
        "2. <b>снять мут</b> — Снять ограничение на отправку сообщений.\n"
        "   Пример: ответьте на сообщение и напишите <code>снять мут</code>\n\n"
        "3. <b>кик</b> — Исключить пользователя из чата.\n"
        "   Пример: ответьте на сообщение и напишите <code>кик</code>\n\n"
        "4. <b>бан</b> — Заблокировать пользователя в чате навсегда.\n"
        "   Пример: ответьте на сообщение и напишите <code>бан</code>\n\n"
        "5. <b>-смс</b> — Удалить сообщение.\n"
        "   Пример: ответьте на сообщение и напишите <code>-смс</code>\n\n"
        "⛔ <b>Важно:</b> Все команды работают ТОЛЬКО ответом на сообщение пользователя.\n"
        "⚠️ <b>Права бота:</b> Убедитесь, что у бота есть права администратора с включенными возможностями "
        "«Блокировка пользователей» и «Удаление сообщений»."
    )
    bot.reply_to(message, help_text, parse_mode="HTML")

# ================== МУТ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("мут"))
def mute_user(message):
    if message.chat.type not in ("group", "supergroup"):
        return

    chat_id = message.chat.id
    admin = message.from_user

    if admin.id not in ADMIN_IDS and not is_chat_admin(chat_id, admin.id):
        return

    if not is_bot_admin(chat_id):
        bot.reply_to(message, "❌ Бот не администратор", parse_mode="HTML")
        return

    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя", parse_mode="HTML")
        return

    if is_chat_admin(chat_id, target.id):
        bot.reply_to(message, "❌ Нельзя мутить администратора", parse_mode="HTML")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(
            message,
            "❌ Использование: мут 60 Спам (ответом на сообщение)",
            parse_mode="HTML"
        )
        return

    try:
        minutes = int(args[1])
    except:
        bot.reply_to(message, "❌ Время должно быть числом", parse_mode="HTML")
        return

    reason = " ".join(args[2:])
    until = int(time.time() + minutes * 60)

    bot.restrict_chat_member(
        chat_id,
        target.id,
        until_date=until,
        can_send_messages=False
    )

    bot.reply_to(
        message,
        f"🔇 Администратор чата {mention(admin)}, выдал мут на {minutes} минут пользователю {mention(target)}, причина: <code>{reason}</code>",
        parse_mode="HTML"
    )

# ================== СНЯТЬ МУТ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("снять мут"))
def unmute_user(message):
    if message.chat.type not in ("group", "supergroup"):
        return

    chat_id = message.chat.id
    admin = message.from_user

    if admin.id not in ADMIN_IDS and not is_chat_admin(chat_id, admin.id):
        return

    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя", parse_mode="HTML")
        return

    bot.restrict_chat_member(
        chat_id,
        target.id,
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    bot.reply_to(
        message,
        f"🔊 Администратор чата {mention(admin)}, снял мут с пользователя {mention(target)}",
        parse_mode="HTML"
    )

# ================== КИК ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "кик")
def kick_user(message):
    if message.chat.type not in ("group", "supergroup"):
        return

    chat_id = message.chat.id
    admin = message.from_user

    if admin.id not in ADMIN_IDS and not is_chat_admin(chat_id, admin.id):
        return

    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя", parse_mode="HTML")
        return

    if is_chat_admin(chat_id, target.id):
        bot.reply_to(message, "❌ Нельзя кикнуть администратора", parse_mode="HTML")
        return

    bot.ban_chat_member(chat_id, target.id)
    bot.unban_chat_member(chat_id, target.id)

    bot.reply_to(
        message,
        f"👢 Администратор чата {mention(admin)}, кикнул пользователя {mention(target)}",
        parse_mode="HTML"
    )

# ================== БАН ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "бан")
def ban_user(message):
    if message.chat.type not in ("group", "supergroup"):
        return

    chat_id = message.chat.id
    admin = message.from_user

    if admin.id not in ADMIN_IDS and not is_chat_admin(chat_id, admin.id):
        return

    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя", parse_mode="HTML")
        return

    if is_chat_admin(chat_id, target.id):
        bot.reply_to(message, "❌ Нельзя банить администратора", parse_mode="HTML")
        return

    bot.ban_chat_member(chat_id, target.id)

    bot.reply_to(
        message,
        f"🚫 Администратор чата {mention(admin)}, забанил пользователя {mention(target)}",
        parse_mode="HTML"
    )

# ================== УДАЛЕНИЕ СООБЩЕНИЯ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "-смс")
def delete_message_cmd(message):
    if message.chat.type not in ("group", "supergroup"):
        return

    chat_id = message.chat.id
    admin = message.from_user

    if admin.id not in ADMIN_IDS and not is_chat_admin(chat_id, admin.id):
        warning = bot.send_message(chat_id, "❌ Команда доступна только администраторам!", parse_mode="HTML")
        time.sleep(5)
        try:
            bot.delete_message(chat_id, warning.message_id)
            bot.delete_message(chat_id, message.message_id)
        except Exception as e:  # Добавлено имя исключения
            pass  # Добавлен отступ
        return

    if not message.reply_to_message:
        hint = bot.send_message(chat_id, "❌ Ответьте на сообщение, которое нужно удалить!", parse_mode="HTML")
        time.sleep(5)
        try:
            bot.delete_message(chat_id, hint.message_id)
            bot.delete_message(chat_id, message.message_id)
        except Exception as e:  # Добавлено имя исключения
            pass  # Добавлен отступ
        return

    try:
        bot.delete_message(chat_id, message.reply_to_message.message_id)
        bot.delete_message(chat_id, message.message_id)
    except Exception as e:
        error_msg = bot.send_message(chat_id, "❌ Не удалось удалить сообщение!", parse_mode="HTML")
        time.sleep(5)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
            bot.delete_message(chat_id, message.message_id)
        except Exception as e:  # Добавлено имя исключения
            pass  # Добавлен отступ
    
    # ================== 🐝 НОВАЯ ИГРА "УЛЕЙ" (HIVE) ==================
# Поле 4x4, ищешь мед 🍯, избегая пчел 🐝
# Кнопки: неоткрытая ячейка - 🟫 (соты), открытая с медом - 🍯, открытая с пчелой - 🐝

import random
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

active_hive_games = {}

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("улей"))
def hive_game_start(message):
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        chat_id = message.chat.id
        user_data = get_user_data(user_id)

        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Ставка?\nПример: <code>улей 1000</code>", parse_mode="HTML")
            return

        try:
            bet = int(parts[1])
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка > 0!")
                return
        except ValueError:
            bot.reply_to(message, "❌ Число!", parse_mode="HTML")
            return

        if user_data["balance"] < bet:
            bot.reply_to(message, f"❌ Нужно: {format_number(bet)} izzzy", parse_mode="HTML")
            return

        user_data["balance"] -= bet
        save_casino_data()

        game_id = str(uuid.uuid4())[:8]

        # 4x4 = 16 клеток, 4 пчелы (мины)
        bee_positions = random.sample(range(16), 4)

        active_hive_games[game_id] = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": None,
            "bet": bet,
            "bee_positions": bee_positions,
            "opened_cells": [],
            "honey_found": 0,
            "current_multiplier": 1.0,
            "active": True
        }

        text = f"🐝 <b>УЛЕЙ</b> | {mention}\n💰 {format_number(bet)} izzzy"
        
        msg = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=hive_keyboard(game_id, user_id, [], show_cashout=False))
        active_hive_games[game_id]["message_id"] = msg.message_id

        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка Улей: {e}")

def hive_keyboard(game_id, user_id, opened_cells, show_cashout=False):
    kb = InlineKeyboardMarkup(row_width=4)
    game = active_hive_games.get(game_id)
    
    buttons = []
    for i in range(16):
        if i in opened_cells:
            if game and i in game["bee_positions"]:
                buttons.append(InlineKeyboardButton("🐝", callback_data="hive_noop"))
            else:
                buttons.append(InlineKeyboardButton("🍯", callback_data="hive_noop"))
        else:
            buttons.append(InlineKeyboardButton("🟫", callback_data=f"hive_open_{game_id}_{i}_{user_id}"))
    
    for i in range(0, 16, 4):
        kb.row(*buttons[i:i+4])
    
    if show_cashout:
        kb.add(InlineKeyboardButton("💸 Забрать мёд", callback_data=f"hive_cashout_{game_id}_{user_id}"))
    
    return kb

@bot.callback_query_handler(func=lambda c: c.data.startswith("hive_open_"))
def hive_open_cell(call):
    try:
        parts = call.data.split("_")
        game_id = parts[2]
        cell = int(parts[3])
        owner_id = int(parts[4])

        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Не твоя игра!", show_alert=True)
            return

        game = active_hive_games.get(game_id)
        if not game or not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра окончена")
            return

        if cell in game["opened_cells"]:
            bot.answer_callback_query(call.id)
            return

        game["opened_cells"].append(cell)

        if cell in game["bee_positions"]:
            game["active"] = False
            bot.edit_message_text(
                f"🐝 <b>УЖАЛИЛА!</b>\n💸 -{format_number(game['bet'])} izzzy",
                game["chat_id"],
                game["message_id"],
                parse_mode="HTML"
            )
            del active_hive_games[game_id]
            bot.answer_callback_query(call.id, "🐝 Тебя ужалили!")
            return
        else:
            game["honey_found"] += 1
            game["current_multiplier"] = round(1.0 + (game["honey_found"] * 0.3), 2)

            if game["honey_found"] >= 12:
                win = int(game["bet"] * game["current_multiplier"])
                user_data = get_user_data(owner_id)
                user_data["balance"] += win
                save_casino_data()

                bot.edit_message_text(
                    f"🐝 <b>ВЕСЬ МЁД!</b>\n💰 +{format_number(win)} izzzy | x{game['current_multiplier']:.2f}",
                    game["chat_id"],
                    game["message_id"],
                    parse_mode="HTML"
                )
                del active_hive_games[game_id]
                bot.answer_callback_query(call.id, f"✅ +{format_number(win)} izzzy")
                return

            bot.edit_message_text(
                f"🐝 <b>+1 мёд!</b>\n💰 {format_number(game['bet'])} izzzy | x{game['current_multiplier']:.2f}",
                game["chat_id"],
                game["message_id"],
                parse_mode="HTML",
                reply_markup=hive_keyboard(game_id, owner_id, game["opened_cells"], show_cashout=True)
            )
            bot.answer_callback_query(call.id, f"🍯 +1 мёд!")

    except Exception as e:
        logger.error(f"Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("hive_cashout_"))
def hive_cashout(call):
    try:
        parts = call.data.split("_")
        game_id = parts[2]
        owner_id = int(parts[3])

        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Не твоя кнопка!", show_alert=True)
            return

        game = active_hive_games.get(game_id)
        if not game or not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра окончена")
            return

        if game["honey_found"] == 0:
            bot.answer_callback_query(call.id, "❌ Сначала найди мёд!")
            return

        win = int(game["bet"] * game["current_multiplier"])
        user_data = get_user_data(owner_id)
        user_data["balance"] += win
        save_casino_data()

        bot.edit_message_text(
            f"✅ <b>Мёд собран!</b>\n💰 +{format_number(win)} izzzy | x{game['current_multiplier']:.2f}",
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML"
        )

        del active_hive_games[game_id]
        bot.answer_callback_query(call.id, f"✅ +{format_number(win)}$")

    except Exception as e:
        logger.error(f"Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "hive_noop")
def hive_noop(call):
    bot.answer_callback_query(call.id)

print("✅ Игра 'Улей' (Hive) загружена!")




# ================== 💰 СИСТЕМА ДЕНЕЖНЫХ КЕЙСОВ (CASES) ==================
CASES_DB = "cases.db"

# Данные о кейсах: Номер, Название, Редкость, Цена в ⭐, Мин. выигрыш, Макс. выигрыш
CASES_DATA = {
    1: {"name": "Обычный", "full_name": "Обычный — Простой кейс", "price": 2, "min_win": 25000, "max_win": 100000},
    2: {"name": "Обычный", "full_name": "Обычный — Стартовый кейс", "price": 5, "min_win": 75000, "max_win": 250000},
    3: {"name": "Необычный", "full_name": "Необычный — Удачный кейс", "price": 8, "min_win": 150000, "max_win": 500000},
    4: {"name": "Необычный", "full_name": "Необычный — Шанс кейс", "price": 12, "min_win": 300000, "max_win": 900000},
    5: {"name": "Редкий", "full_name": "Редкий — Редкая удача", "price": 18, "min_win": 600000, "max_win": 1800000},
    6: {"name": "Редкий", "full_name": "Редкий — Серебряный кейс", "price": 25, "min_win": 1200000, "max_win": 3500000},
    7: {"name": "Эпический", "full_name": "Эпический — Золотой кейс", "price": 32, "min_win": 2000000, "max_win": 6000000},
    8: {"name": "Эпический", "full_name": "Эпический — Героический кейс", "price": 38, "min_win": 3000000, "max_win": 9000000},
    9: {"name": "Легендарный", "full_name": "Легендарный — Легенда кейс", "price": 45, "min_win": 5000000, "max_win": 15000000},
    10: {"name": "Мифический", "full_name": "Мифический — Мифический клад", "price": 60, "min_win": 8000000, "max_win": 25000000},
    11: {"name": "Божественный", "full_name": "Божественный — Кейс богов", "price": 100, "min_win": 15000000, "max_win": 50000000},
}

# Инициализация базы данных
def init_cases_db():
    conn = sqlite3.connect(CASES_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_cases (
            user_id INTEGER PRIMARY KEY,
            case_number INTEGER,
            purchased_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("✅ База данных кейсов инициализирована")

init_cases_db()

def get_user_case(user_id):
    """Получает номер кейса пользователя или None"""
    conn = sqlite3.connect(CASES_DB)
    c = conn.cursor()
    c.execute("SELECT case_number FROM user_cases WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_user_case(user_id, case_number):
    """Устанавливает кейс пользователю"""
    conn = sqlite3.connect(CASES_DB)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO user_cases (user_id, case_number, purchased_at) 
        VALUES (?, ?, ?)
    """, (user_id, case_number, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def clear_user_case(user_id):
    """Удаляет кейс пользователя (после открытия)"""
    conn = sqlite3.connect(CASES_DB)
    c = conn.cursor()
    c.execute("DELETE FROM user_cases WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ================== КОМАНДА: КУПИТЬ КЕЙС ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить кейс"))
def buy_case_command(message):
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        parts = message.text.split()

        if len(parts) < 3:
            text = (
                "❌ Использование: <code>купить кейс [номер]</code>\n\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "📋 <b>АССОРТИМЕНТ КЕЙСОВ</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                
                "<b>🥉 ОБЫЧНЫЕ</b>\n"
                "1️⃣ Простой кейс — 2⭐ (25к-100к💸)\n"
                "2️⃣ Стартовый кейс — 5⭐ (75к-250к💸)\n\n"
                
                "<b>🥈 НЕОБЫЧНЫЕ</b>\n"
                "3️⃣ Удачный кейс — 8⭐ (150к-500к💸)\n"
                "4️⃣ Шанс кейс — 12⭐ (300к-900к💸)\n\n"
                
                "<b>🥇 РЕДКИЕ</b>\n"
                "5️⃣ Редкая удача — 18⭐ (600к-1.8M💸)\n"
                "6️⃣ Серебряный кейс — 25⭐ (1.2M-3.5M💸)\n\n"
                
                "<b>💎 ЭПИЧЕСКИЕ</b>\n"
                "7️⃣ Золотой кейс — 32⭐ (2M-6M💸)\n"
                "8️⃣ Героический кейс — 38⭐ (3M-9M💸)\n\n"
                
                "<b>👑 ЛЕГЕНДАРНЫЕ</b>\n"
                "9️⃣ Легенда кейс — 45⭐ (5M-15M💸)\n"
                "🔟 Мифический клад — 60⭐ (8M-25M💸)\n\n"
                
                "<b>✨ БОЖЕСТВЕННЫЕ</b>\n"
                "1️⃣1️⃣ Кейс богов — 100⭐ (15M-50M💸)\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            bot.reply_to(message, text, parse_mode="HTML")
            return

        try:
            case_num = int(parts[2])
        except ValueError:
            bot.reply_to(message, "❌ Номер кейса должен быть числом!")
            return

        if case_num not in CASES_DATA:
            bot.reply_to(message, f"❌ Кейса с номером {case_num} не существует!")
            return

        # Проверяем, есть ли уже неоткрытый кейс
        existing_case = get_user_case(user_id)
        if existing_case is not None:
            case_info = CASES_DATA[existing_case]
            bot.reply_to(
                message,
                f"❌ {mention}, у тебя уже есть неоткрытый кейс!\n\n"
                f"📦 Твой кейс: <b>{case_info['full_name']}</b>\n"
                f"🔓 Открыть: <code>открыть кейс</code>",
                parse_mode="HTML"
            )
            return

        # Создаем платеж
        case_info = CASES_DATA[case_num]
        stars_amount = case_info["price"]
        payment_id = create_star_payment(user_id, stars_amount, 0)

        title = f"💰 Покупка кейса #{case_num}"
        description = f"{case_info['full_name']} — выигрыш от {format_number(case_info['min_win'])} izzzy до {format_number(case_info['max_win'])} izzzy"
        currency = "XTR"

        price = types.LabeledPrice(label=case_info['full_name'], amount=stars_amount)

        bot.send_invoice(
            chat_id=message.chat.id,
            title=title,
            description=description,
            invoice_payload=f"case_payment_{payment_id}_{user_id}_{case_num}",
            provider_token="",
            currency=currency,
            prices=[price],
            start_parameter="buy-case"
        )

    except Exception as e:
        logger.error(f"Ошибка покупки кейса: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при покупке кейса!")

# ================== ОБРАБОТКА ОПЛАТЫ КЕЙСА ==================
@bot.pre_checkout_query_handler(func=lambda q: q.invoice_payload.startswith("case_payment_"))
def case_pre_checkout(pre_q):
    bot.answer_pre_checkout_query(pre_q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'], func=lambda m: m.successful_payment.invoice_payload.startswith("case_payment_"))
def case_payment_success(message):
    try:
        payload = message.successful_payment.invoice_payload
        parts = payload.split("_")
        payment_id = parts[2]
        user_id = int(parts[3])
        case_num = int(parts[4])

        # Проверяем, что платёж принадлежит этому пользователю
        if message.from_user.id != user_id:
            bot.send_message(message.chat.id, "❌ Ошибка: платёж принадлежит другому пользователю!")
            return

        # Получаем информацию о платеже из базы
        payment_info = get_star_payment(payment_id)
        if not payment_info:
            bot.send_message(message.chat.id, "⚠️ Платёж не найден в базе.")
            return

        # Помечаем платёж как завершённый
        complete_star_payment(payment_id)

        # Проверяем, не появился ли кейс за это время
        if get_user_case(user_id) is not None:
            bot.send_message(
                message.chat.id,
                "❌ У тебя уже есть неоткрытый кейс! Открой его командой <code>открыть кейс</code>.",
                parse_mode="HTML"
            )
            return

        # Начисляем кейс пользователю
        set_user_case(user_id, case_num)
        case_info = CASES_DATA[case_num]

        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        bot.send_message(
            message.chat.id,
            f"{mention}, поздравляю с покупкой кейса <b>{case_info['full_name']}</b> за <code>{case_info['price']}⭐</code>!\n\n"
            f"🔓 Открыть можно командой: <code>открыть кейс</code>",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка обработки успешной оплаты кейса: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при обработке покупки!")

# ================== КОМАНДА: МОИ КЕЙСЫ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мои кейсы", "мой кейс", "кейсы"])
def my_cases_command(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    case_num = get_user_case(user_id)

    if case_num is None:
        text = (
            f"📦 {mention}, у тебя нет неоткрытых кейсов.\n\n"
            f"Купить кейс: <code>купить кейс [номер]</code>\n\n"
            f"<b>Список кейсов:</b>\n"
            f"1️⃣ (2⭐) 25к-100к💸\n"
            f"2️⃣ (5⭐) 75к-250к💸\n"
            f"3️⃣ (8⭐) 150к-500к💸\n"
            f"4️⃣ (12⭐) 300к-900к💸\n"
            f"5️⃣ (18⭐) 600к-1.8M💸\n"
            f"6️⃣ (25⭐) 1.2M-3.5M💸\n"
            f"7️⃣ (32⭐) 2M-6M💸\n"
            f"8️⃣ (38⭐) 3M-9M💸\n"
            f"9️⃣ (45⭐) 5M-15M💸\n"
            f"🔟 (60⭐) 8M-25M💸\n"
            f"1️⃣1️⃣ (100⭐) 15M-50M💸"
        )
    else:
        case_info = CASES_DATA[case_num]
        text = (
            f"📦 {mention}, у тебя есть неоткрытый кейс:\n\n"
            f"🎁 <b>{case_info['full_name']}</b>\n"
            f"💎 Редкость: {case_info['name']}\n"
            f"💰 Возможный выигрыш: {format_number(case_info['min_win'])} izzzy - {format_number(case_info['max_win'])} izzzy\n\n"
            f"🔓 Открыть командой: <code>открыть кейс</code>"
        )

    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ================== КОМАНДА: ОТКРЫТЬ КЕЙС ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "открыть кейс")
def open_case_command(message):
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        case_num = get_user_case(user_id)

        if case_num is None:
            bot.reply_to(
                message,
                f"📦 {mention}, у тебя нет неоткрытых кейсов!\n"
                f"Купить кейс: <code>купить кейс [номер]</code>",
                parse_mode="HTML"
            )
            return

        case_info = CASES_DATA[case_num]

        # Генерируем случайный выигрыш
        win_amount = random.randint(case_info["min_win"], case_info["max_win"])

        # Получаем данные пользователя и начисляем деньги
        user_data = get_user_data(user_id)
        user_data["balance"] += win_amount
        save_casino_data()

        # Удаляем кейс
        clear_user_case(user_id)

        # Специальные эмодзи для разных редкостей
        rarity_emojis = {
            "Обычный": "📦",
            "Необычный": "📦✨",
            "Редкий": "🌟",
            "Эпический": "💫",
            "Легендарный": "👑",
            "Мифический": "🔮",
            "Божественный": "⚡"
        }
        emoji = rarity_emojis.get(case_info["name"], "🎁")

        # Отправляем сообщение
        result_text = (
            f"{emoji} {mention}, ты открыл <b>{case_info['full_name']}</b>!\n\n"
            f"💰 Ты получил: <code>{format_number(win_amount)} izzzy</code>\n"
            f"💳 Твой баланс: <code>{format_number(user_data['balance'])} izzzy</code>"
        )

        bot.send_message(message.chat.id, result_text, parse_mode="HTML")

        # Логирование
        logger.info(f"Пользователь {user_id} открыл кейс #{case_num} и получил {win_amount}$")

    except Exception as e:
        logger.error(f"Ошибка открытия кейса: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при открытии кейса!")

# ================== КОМАНДА: СПИСОК КЕЙСОВ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["кейсы", "список кейсов", "магазин кейсов"])
def cases_list_command(message):
    text = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "МАГАЗИН КЕЙСОВ\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        
        "ОБЫЧНЫЕ\n"
        "1. Простой кейс — 2⭐\n"
        "   Выигрыш: 25,000 - 100,000$\n"
        "2. Стартовый кейс — 5⭐\n"
        "   Выигрыш: 75,000 - 250,000$\n\n"
        
        "НЕОБЫЧНЫЕ\n"
        "3. Удачный кейс — 8⭐\n"
        "   Выигрыш: 150,000 - 500,000$\n"
        "4. Шанс кейс — 12⭐\n"
        "   Выигрыш: 300,000 - 900,000$\n\n"
        
        "РЕДКИЕ\n"
        "5. Редкая удача — 18⭐\n"
        "   Выигрыш: 600,000 - 1,800,000$\n"
        "6. Серебряный кейс — 25⭐\n"
        "   Выигрыш: 1,200,000 - 3,500,000$\n\n"
        
        "ЭПИЧЕСКИЕ\n"
        "7. Золотой кейс — 32⭐\n"
        "   Выигрыш: 2,000,000 - 6,000,000$\n"
        "8. Героический кейс — 38⭐\n"
        "   Выигрыш: 3,000,000 - 9,000,000$\n\n"
        
        "ЛЕГЕНДАРНЫЕ\n"
        "9. Легенда кейс — 45⭐\n"
        "   Выигрыш: 5,000,000 - 15,000,000$\n"
        "10. Мифический клад — 60⭐\n"
        "   Выигрыш: 8,000,000 - 25,000,000$\n\n"
        
        "БОЖЕСТВЕННЫЕ\n"
        "11. Кейс богов — 100⭐\n"
        "   Выигрыш: 15,000,000 - 50,000,000$\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Купить: купить кейс [номер]\n"
        "Мои кейсы: мои кейсы"
    )
    
    bot.send_message(message.chat.id, text, parse_mode="HTML")

print("✅ Система кейсов загружена (11 видов)")

# ================== РАЗБАН ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "разбан")
def unban_user(message):
    if message.chat.type not in ("group", "supergroup"):
        return

    chat_id = message.chat.id
    admin = message.from_user

    if admin.id not in ADMIN_IDS and not is_chat_admin(chat_id, admin.id):
        return

    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ <b>Укажи ID пользователя</b>", parse_mode="HTML")
        return

    bot.unban_chat_member(chat_id, target.id)

    bot.reply_to(
        message,
        f"✅ <b>РАЗБАН</b>\n\n"
        f"👮 {mention(admin)}\n"
        f"👤 {mention(target)}",
        parse_mode="HTML"
    )
    
  
# ================== 🎣 СИСТЕМА РЫБАЛКИ ==================
FISHING_DB = "fishing.db"
FISHING_IMAGE_URL = "https://img.freepik.com/free-photo/portrait-young-3d-adorable-baby-boy_23-2151734960.jpg"

# Инициализация базы данных рыбалки
def init_fishing_db():
    conn = sqlite3.connect(FISHING_DB)
    c = conn.cursor()
    
    # Таблица пользователей рыбалки
    c.execute("""
        CREATE TABLE IF NOT EXISTS fishing_users (
            user_id INTEGER PRIMARY KEY,
            rod_id INTEGER DEFAULT 1,
            energy INTEGER DEFAULT 100,
            max_energy INTEGER DEFAULT 100,
            rod_durability INTEGER DEFAULT 100,
            max_durability INTEGER DEFAULT 100,
            total_fish_caught INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            last_energy_regen TEXT,
            last_fishing_time TEXT
        )
    """)
    
    # Таблица инвентаря рыб
    c.execute("""
        CREATE TABLE IF NOT EXISTS fishing_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fish_name TEXT NOT NULL,
            fish_price INTEGER NOT NULL,
            quantity INTEGER DEFAULT 0,
            UNIQUE(user_id, fish_name)
        )
    """)
    
    conn.commit()
    conn.close()

init_fishing_db()

FISHING_RODS = {
    1: {"id": 1, "name": "Деревянная удочка", "price": 0, "rarity_bonus": 1.0, "durability": 100, "sellable": False},
    2: {"id": 2, "name": "Стальная удочка", "price": 50000, "rarity_bonus": 1.5, "durability": 150, "sellable": True},
    3: {"id": 3, "name": "Титановая удочка", "price": 200000, "rarity_bonus": 2.0, "durability": 200, "sellable": True},
    4: {"id": 4, "name": "Карбоновая удочка", "price": 500000, "rarity_bonus": 2.5, "durability": 250, "sellable": True},
    5: {"id": 5, "name": "Алмазная удочка", "price": 1500000, "rarity_bonus": 3.0, "durability": 300, "sellable": True},
    6: {"id": 6, "name": "Мифическая удочка", "price": 4000000, "rarity_bonus": 4.0, "durability": 400, "sellable": True},
    7: {"id": 7, "name": "Легендарная удочка", "price": 9000000, "rarity_bonus": 5.0, "durability": 500, "sellable": True}
}

# ================== 🐟 100+ ВИДОВ РЫБ ==================
FISH_DATA = {
    # Обычные рыбы (шанс высокий, цена низкая)
    "Плотва": {"price": 50, "rarity": 100, "min_weight": 0.1, "max_weight": 0.5, "unit": "кг"},
    "Окунь": {"price": 80, "rarity": 95, "min_weight": 0.2, "max_weight": 1.2, "unit": "кг"},
    "Ёрш": {"price": 40, "rarity": 90, "min_weight": 0.05, "max_weight": 0.2, "unit": "кг"},
    "Карась": {"price": 60, "rarity": 88, "min_weight": 0.3, "max_weight": 1.5, "unit": "кг"},
    "Пескарь": {"price": 30, "rarity": 85, "min_weight": 0.02, "max_weight": 0.1, "unit": "кг"},
    "Уклейка": {"price": 25, "rarity": 82, "min_weight": 0.01, "max_weight": 0.08, "unit": "кг"},
    "Густера": {"price": 70, "rarity": 80, "min_weight": 0.2, "max_weight": 0.8, "unit": "кг"},
    "Краснопёрка": {"price": 90, "rarity": 78, "min_weight": 0.2, "max_weight": 1.0, "unit": "кг"},
    "Линь": {"price": 120, "rarity": 75, "min_weight": 0.5, "max_weight": 2.5, "unit": "кг"},
    "Язь": {"price": 150, "rarity": 73, "min_weight": 0.5, "max_weight": 3.0, "unit": "кг"},
    "Голавль": {"price": 180, "rarity": 70, "min_weight": 0.5, "max_weight": 4.0, "unit": "кг"},
    "Жерех": {"price": 250, "rarity": 68, "min_weight": 1.0, "max_weight": 8.0, "unit": "кг"},
    "Судак": {"price": 350, "rarity": 65, "min_weight": 1.0, "max_weight": 10.0, "unit": "кг"},
    "Щука": {"price": 400, "rarity": 63, "min_weight": 1.0, "max_weight": 15.0, "unit": "кг"},
    "Налим": {"price": 300, "rarity": 60, "min_weight": 0.5, "max_weight": 5.0, "unit": "кг"},
    "Сом": {"price": 600, "rarity": 58, "min_weight": 2.0, "max_weight": 50.0, "unit": "кг"},
    "Сазан": {"price": 500, "rarity": 55, "min_weight": 1.0, "max_weight": 20.0, "unit": "кг"},
    "Карп": {"price": 450, "rarity": 53, "min_weight": 1.0, "max_weight": 25.0, "unit": "кг"},
    "Белый амур": {"price": 550, "rarity": 50, "min_weight": 2.0, "max_weight": 30.0, "unit": "кг"},
    "Толстолобик": {"price": 480, "rarity": 48, "min_weight": 2.0, "max_weight": 40.0, "unit": "кг"},
    "Форель": {"price": 800, "rarity": 45, "min_weight": 0.5, "max_weight": 5.0, "unit": "кг"},
    "Хариус": {"price": 700, "rarity": 43, "min_weight": 0.3, "max_weight": 2.0, "unit": "кг"},
    "Лосось": {"price": 1200, "rarity": 40, "min_weight": 2.0, "max_weight": 15.0, "unit": "кг"},
    "Сёмга": {"price": 1500, "rarity": 38, "min_weight": 3.0, "max_weight": 20.0, "unit": "кг"},
    "Кета": {"price": 1100, "rarity": 36, "min_weight": 2.0, "max_weight": 12.0, "unit": "кг"},
    "Горбуша": {"price": 900, "rarity": 35, "min_weight": 1.0, "max_weight": 5.0, "unit": "кг"},
    "Кижуч": {"price": 1300, "rarity": 33, "min_weight": 2.0, "max_weight": 10.0, "unit": "кг"},
    "Нерка": {"price": 1400, "rarity": 31, "min_weight": 1.5, "max_weight": 8.0, "unit": "кг"},
    "Чавыча": {"price": 1800, "rarity": 29, "min_weight": 5.0, "max_weight": 25.0, "unit": "кг"},
    "Сиг": {"price": 850, "rarity": 28, "min_weight": 0.5, "max_weight": 4.0, "unit": "кг"},
    "Омуль": {"price": 950, "rarity": 27, "min_weight": 0.5, "max_weight": 3.0, "unit": "кг"},
    "Муксун": {"price": 1100, "rarity": 26, "min_weight": 1.0, "max_weight": 5.0, "unit": "кг"},
    "Нельма": {"price": 2000, "rarity": 25, "min_weight": 5.0, "max_weight": 30.0, "unit": "кг"},
    "Таймень": {"price": 3000, "rarity": 24, "min_weight": 10.0, "max_weight": 60.0, "unit": "кг"},
    "Угорь": {"price": 1600, "rarity": 23, "min_weight": 0.5, "max_weight": 4.0, "unit": "кг"},
    "Минога": {"price": 700, "rarity": 22, "min_weight": 0.1, "max_weight": 0.5, "unit": "кг"},
    "Кумжа": {"price": 1700, "rarity": 21, "min_weight": 1.0, "max_weight": 8.0, "unit": "кг"},
    "Палтус": {"price": 2500, "rarity": 20, "min_weight": 5.0, "max_weight": 200.0, "unit": "кг"},
    "Треска": {"price": 1000, "rarity": 19, "min_weight": 2.0, "max_weight": 40.0, "unit": "кг"},
    "Пикша": {"price": 900, "rarity": 18, "min_weight": 1.0, "max_weight": 15.0, "unit": "кг"},
    "Минтай": {"price": 400, "rarity": 17, "min_weight": 0.5, "max_weight": 3.0, "unit": "кг"},
    "Камбала": {"price": 700, "rarity": 16, "min_weight": 0.5, "max_weight": 10.0, "unit": "кг"},
    "Скумбрия": {"price": 800, "rarity": 15, "min_weight": 0.3, "max_weight": 2.0, "unit": "кг"},
    "Ставрида": {"price": 600, "rarity": 14, "min_weight": 0.2, "max_weight": 1.5, "unit": "кг"},
    "Сардина": {"price": 500, "rarity": 13, "min_weight": 0.1, "max_weight": 0.3, "unit": "кг"},
    "Килька": {"price": 200, "rarity": 12, "min_weight": 0.01, "max_weight": 0.05, "unit": "кг"},
    "Хамса": {"price": 300, "rarity": 11, "min_weight": 0.01, "max_weight": 0.04, "unit": "кг"},
    "Тюлька": {"price": 150, "rarity": 10, "min_weight": 0.005, "max_weight": 0.02, "unit": "кг"},
    "Бычок": {"price": 250, "rarity": 9, "min_weight": 0.05, "max_weight": 0.3, "unit": "кг"},
    "Рыба-игла": {"price": 400, "rarity": 8, "min_weight": 0.05, "max_weight": 0.2, "unit": "кг"},
    "Морской конёк": {"price": 800, "rarity": 7, "min_weight": 0.01, "max_weight": 0.03, "unit": "кг"},
    "Барабуля": {"price": 900, "rarity": 6, "min_weight": 0.1, "max_weight": 0.5, "unit": "кг"},
    "Зубатка": {"price": 1200, "rarity": 5, "min_weight": 3.0, "max_weight": 20.0, "unit": "кг"},
    "Морской окунь": {"price": 1500, "rarity": 4, "min_weight": 1.0, "max_weight": 10.0, "unit": "кг"},
    "Дорадо": {"price": 2000, "rarity": 3, "min_weight": 1.0, "max_weight": 8.0, "unit": "кг"},
    "Сибас": {"price": 1800, "rarity": 3, "min_weight": 0.5, "max_weight": 5.0, "unit": "кг"},
    
    # Редкие рыбы (шанс низкий, цена высокая)
    "Осётр": {"price": 5000, "rarity": 2.0, "min_weight": 10.0, "max_weight": 100.0, "unit": "кг"},
    "Севрюга": {"price": 6000, "rarity": 1.8, "min_weight": 5.0, "max_weight": 50.0, "unit": "кг"},
    "Белуга": {"price": 10000, "rarity": 1.5, "min_weight": 50.0, "max_weight": 1000.0, "unit": "кг"},
    "Стерлядь": {"price": 4000, "rarity": 1.7, "min_weight": 1.0, "max_weight": 15.0, "unit": "кг"},
    "Форель радужная": {"price": 3000, "rarity": 1.9, "min_weight": 0.5, "max_weight": 4.0, "unit": "кг"},
    "Золотая рыбка": {"price": 15000, "rarity": 0.5, "min_weight": 0.1, "max_weight": 0.5, "unit": "кг"},
    
    # Очень редкие (шанс очень маленький, цена высокая до 2-6 млн)
    "Рыба-клоун": {"price": 25000, "rarity": 0.3, "min_weight": 0.1, "max_weight": 0.3, "unit": "кг"},
    "Рыба-ангел": {"price": 40000, "rarity": 0.2, "min_weight": 0.2, "max_weight": 0.5, "unit": "кг"},
    "Рыба-бабочка": {"price": 35000, "rarity": 0.2, "min_weight": 0.05, "max_weight": 0.2, "unit": "кг"},
    "Хирург": {"price": 50000, "rarity": 0.15, "min_weight": 0.3, "max_weight": 1.0, "unit": "кг"},
    "Спинорог": {"price": 60000, "rarity": 0.14, "min_weight": 1.0, "max_weight": 5.0, "unit": "кг"},
    "Кузовок": {"price": 55000, "rarity": 0.13, "min_weight": 0.2, "max_weight": 0.8, "unit": "кг"},
    "Иглобрюх": {"price": 70000, "rarity": 0.12, "min_weight": 0.5, "max_weight": 3.0, "unit": "кг"},
    "Рыба-шар": {"price": 80000, "rarity": 0.11, "min_weight": 0.3, "max_weight": 2.0, "unit": "кг"},
    "Рыба-луна": {"price": 150000, "rarity": 0.1, "min_weight": 100.0, "max_weight": 1000.0, "unit": "кг"},
    "Рыба-меч": {"price": 200000, "rarity": 0.09, "min_weight": 50.0, "max_weight": 500.0, "unit": "кг"},
    "Марлин": {"price": 300000, "rarity": 0.08, "min_weight": 50.0, "max_weight": 600.0, "unit": "кг"},
    "Тунец": {"price": 250000, "rarity": 0.07, "min_weight": 10.0, "max_weight": 300.0, "unit": "кг"},
    "Акула-мако": {"price": 400000, "rarity": 0.06, "min_weight": 100.0, "max_weight": 500.0, "unit": "кг"},
    "Акула-тигровая": {"price": 500000, "rarity": 0.05, "min_weight": 200.0, "max_weight": 800.0, "unit": "кг"},
    "Акула-молот": {"price": 600000, "rarity": 0.04, "min_weight": 150.0, "max_weight": 450.0, "unit": "кг"},
    "Китовая акула": {"price": 1000000, "rarity": 0.03, "min_weight": 2000.0, "max_weight": 20000.0, "unit": "кг"},
    
    # Монстры (шанс ОЧЕНЬ маленький, цена 2-6 млн+)
    "Рыба-гадюка": {"price": 2000000, "rarity": 0.01, "min_weight": 1.0, "max_weight": 5.0, "unit": "кг"},
    "Рыба-дракон": {"price": 2500000, "rarity": 0.009, "min_weight": 2.0, "max_weight": 10.0, "unit": "кг"},
    "Рыба-скорпион": {"price": 2200000, "rarity": 0.008, "min_weight": 0.5, "max_weight": 2.0, "unit": "кг"},
    "Рыба-камень": {"price": 2800000, "rarity": 0.007, "min_weight": 1.0, "max_weight": 3.0, "unit": "кг"},
    "Мурена": {"price": 1500000, "rarity": 0.006, "min_weight": 5.0, "max_weight": 30.0, "unit": "кг"},
    "Гигантский групер": {"price": 3200000, "rarity": 0.005, "min_weight": 100.0, "max_weight": 400.0, "unit": "кг"},
    "Королевская макрель": {"price": 1800000, "rarity": 0.005, "min_weight": 10.0, "max_weight": 50.0, "unit": "кг"},
    "Змееголов": {"price": 1200000, "rarity": 0.004, "min_weight": 5.0, "max_weight": 15.0, "unit": "кг"},
    "Арапаима": {"price": 3500000, "rarity": 0.004, "min_weight": 50.0, "max_weight": 200.0, "unit": "кг"},
    "Пиранья": {"price": 900000, "rarity": 0.003, "min_weight": 0.5, "max_weight": 3.0, "unit": "кг"},
    "Электрический угорь": {"price": 2800000, "rarity": 0.003, "min_weight": 5.0, "max_weight": 20.0, "unit": "кг"},
    "Рыба-зебра": {"price": 1100000, "rarity": 0.002, "min_weight": 0.3, "max_weight": 1.0, "unit": "кг"},
    "Морской дракон": {"price": 4000000, "rarity": 0.002, "min_weight": 0.2, "max_weight": 0.5, "unit": "кг"},
    "Рыба-лягушка": {"price": 1800000, "rarity": 0.0015, "min_weight": 0.1, "max_weight": 0.4, "unit": "кг"},
    "Рыба-попугай": {"price": 900000, "rarity": 0.0015, "min_weight": 0.5, "max_weight": 2.0, "unit": "кг"},
    
    # Легендарные (шанс 0.001-0.0001%, цена 5-10 млн)
    "Золотой осётр": {"price": 5000000, "rarity": 0.001, "min_weight": 50.0, "max_weight": 200.0, "unit": "кг"},
    "Платиновая белуга": {"price": 6000000, "rarity": 0.0009, "min_weight": 100.0, "max_weight": 500.0, "unit": "кг"},
    "Королевский лосось": {"price": 4500000, "rarity": 0.0008, "min_weight": 10.0, "max_weight": 30.0, "unit": "кг"},
    "Рыба-фугу": {"price": 5500000, "rarity": 0.0007, "min_weight": 1.0, "max_weight": 3.0, "unit": "кг"},
    "Рыба-гадюка королевская": {"price": 7000000, "rarity": 0.0006, "min_weight": 2.0, "max_weight": 8.0, "unit": "кг"},
    "Морской змей": {"price": 8000000, "rarity": 0.0005, "min_weight": 50.0, "max_weight": 200.0, "unit": "кг"},
    "Кракен": {"price": 10000000, "rarity": 0.0004, "min_weight": 1000.0, "max_weight": 5000.0, "unit": "тонн"},
    "Левиафан": {"price": 15000000, "rarity": 0.0003, "min_weight": 2000.0, "max_weight": 10000.0, "unit": "тонн"},
    "Царь-рыба": {"price": 20000000, "rarity": 0.0002, "min_weight": 500.0, "max_weight": 2000.0, "unit": "тонн"},
    "Рыба судного дня": {"price": 50000000, "rarity": 0.0001, "min_weight": 5000.0, "max_weight": 50000.0, "unit": "тонн"},
}

# Функции для работы с рыбалкой
def get_fishing_user(user_id):
    """Получает данные пользователя рыбалки"""
    conn = sqlite3.connect(FISHING_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT rod_id, energy, max_energy, rod_durability, max_durability, 
               total_fish_caught, total_earned, total_spent, last_energy_regen, last_fishing_time 
        FROM fishing_users WHERE user_id = ?
    """, (user_id,))
    
    result = c.fetchone()
    
    if not result:
        # Создаем нового пользователя с деревянной удочкой
        now = datetime.now().isoformat()
        c.execute("""
            INSERT INTO fishing_users 
            (user_id, rod_id, energy, max_energy, rod_durability, max_durability, 
             total_fish_caught, total_earned, total_spent, last_energy_regen, last_fishing_time) 
            VALUES (?, 1, 100, 100, 100, 100, 0, 0, 0, ?, ?)
        """, (user_id, now, now))
        conn.commit()
        
        conn.close()
        return {
            "rod_id": 1,
            "energy": 100,
            "max_energy": 100,
            "rod_durability": 100,
            "max_durability": 100,
            "total_fish_caught": 0,
            "total_earned": 0,
            "total_spent": 0,
            "last_energy_regen": now,
            "last_fishing_time": now
        }
    
    conn.close()
    
    return {
        "rod_id": result[0],
        "energy": result[1],
        "max_energy": result[2],
        "rod_durability": result[3],
        "max_durability": result[4],
        "total_fish_caught": result[5],
        "total_earned": result[6],
        "total_spent": result[7],
        "last_energy_regen": result[8],
        "last_fishing_time": result[9]
    }

def update_fishing_user(user_id, data):
    """Обновляет данные пользователя рыбалки"""
    conn = sqlite3.connect(FISHING_DB)
    c = conn.cursor()
    
    c.execute("""
        UPDATE fishing_users SET 
        rod_id = ?, energy = ?, max_energy = ?, rod_durability = ?, 
        max_durability = ?, total_fish_caught = ?, total_earned = ?, 
        total_spent = ?, last_energy_regen = ?, last_fishing_time = ?
        WHERE user_id = ?
    """, (
        data["rod_id"], data["energy"], data["max_energy"], 
        data["rod_durability"], data["max_durability"], data["total_fish_caught"],
        data["total_earned"], data["total_spent"], data["last_energy_regen"], 
        data["last_fishing_time"], user_id
    ))
    
    conn.commit()
    conn.close()

def get_fish_inventory(user_id):
    """Получает инвентарь рыб пользователя"""
    conn = sqlite3.connect(FISHING_DB)
    c = conn.cursor()
    
    c.execute("SELECT fish_name, quantity, fish_price FROM fishing_inventory WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    inventory = {}
    total_value = 0
    
    for fish_name, quantity, fish_price in rows:
        inventory[fish_name] = {
            "quantity": quantity,
            "price": fish_price
        }
        total_value += fish_price * quantity
    
    return inventory, total_value

def add_fish_to_inventory(user_id, fish_name, fish_price, quantity=1):
    """Добавляет рыбу в инвентарь пользователя"""
    conn = sqlite3.connect(FISHING_DB)
    c = conn.cursor()
    
    # Проверяем, есть ли уже такая рыба
    c.execute("SELECT quantity, fish_price FROM fishing_inventory WHERE user_id = ? AND fish_name = ?", 
              (user_id, fish_name))
    result = c.fetchone()
    
    if result:
        # Уже есть такая рыба - обновляем среднюю цену
        old_quantity = result[0]
        old_price = result[1]
        
        # Вычисляем новую среднюю цену
        total_value = (old_price * old_quantity) + (fish_price * quantity)
        new_quantity = old_quantity + quantity
        new_avg_price = total_value // new_quantity  # Целочисленное деление
        
        c.execute("UPDATE fishing_inventory SET quantity = ?, fish_price = ? WHERE user_id = ? AND fish_name = ?", 
                 (new_quantity, new_avg_price, user_id, fish_name))
    else:
        # Добавляем новую рыбу
        c.execute("INSERT INTO fishing_inventory (user_id, fish_name, fish_price, quantity) VALUES (?, ?, ?, ?)", 
                 (user_id, fish_name, fish_price, quantity))
    
    conn.commit()
    conn.close()

def sell_all_fish(user_id):
    """Продаёт всю рыбу пользователя и возвращает выручку"""
    conn = sqlite3.connect(FISHING_DB)
    c = conn.cursor()
    
    # Получаем всю рыбу
    c.execute("SELECT fish_name, quantity, fish_price FROM fishing_inventory WHERE user_id = ?", (user_id,))
    fish_list = c.fetchall()
    
    if not fish_list:
        conn.close()
        return 0
    
    # Считаем общую стоимость
    total_value = 0
    for fish_name, quantity, fish_price in fish_list:
        total_value += fish_price * quantity
    
    # Удаляем всю рыбу
    c.execute("DELETE FROM fishing_inventory WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return total_value

def get_fish_inventory(user_id):
    """Получает инвентарь рыб пользователя"""
    conn = sqlite3.connect(FISHING_DB)
    c = conn.cursor()
    
    c.execute("SELECT fish_name, quantity, fish_price FROM fishing_inventory WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    inventory = {}
    total_value = 0
    
    for fish_name, quantity, fish_price in rows:
        inventory[fish_name] = {
            "quantity": quantity,
            "price": fish_price
        }
        total_value += fish_price * quantity
    
    return inventory, total_value

def regenerate_fishing_energy(user_id):
    """Восстанавливает энергию (2 энергии каждые 2 минуты)"""
    user_data = get_fishing_user(user_id)
    now = datetime.now()
    
    if user_data["last_energy_regen"]:
        last_regen = datetime.fromisoformat(user_data["last_energy_regen"])
        minutes_passed = (now - last_regen).total_seconds() / 60
        
        if minutes_passed >= 2 and user_data["energy"] < user_data["max_energy"]:
            # Восстанавливаем 2 энергии за каждые 2 минуты
            energy_to_add = int(minutes_passed // 2) * 2
            user_data["energy"] = min(user_data["max_energy"], user_data["energy"] + energy_to_add)
            user_data["last_energy_regen"] = now.isoformat()
            update_fishing_user(user_id, user_data)
    
    return user_data

def can_fish(user_id):
    """Проверяет, может ли пользователь рыбачить"""
    
    user_data = get_fishing_user(user_id)
    
    # Регенерация энергии
    user_data = regenerate_fishing_energy(user_id)

    # Проверяем наличие удочки
    if user_data["rod_id"] == 0:
        return False, "🎣 У тебя нет удочки! Купи её в магазине."
    
    # Если прочность уже 0 — окончательно удаляем удочку
    if user_data["rod_durability"] <= 0:
        user_data["rod_id"] = 0
        user_data["rod_durability"] = 0
        update_fishing_user(user_id, user_data)
        return False, "🎣 Твоя удочка износилась и сломалась."

    # Кулдаун (1 секунда)
    if user_data["last_fishing_time"]:
        last_fish = datetime.fromisoformat(user_data["last_fishing_time"])
        if (datetime.now() - last_fish).total_seconds() < 1:
            return False, "⏳ Подожди 1 секунду перед следующей рыбалкой!"

    # Проверка энергии
    if user_data["energy"] <= 0:
        return False, "⚡ Твоя энергия закончилась, подожди восстановления или восстанови за 2⭐"

    return True, user_data

def get_random_fish(rod_id):
    """Получает случайную рыбу с учетом бонуса удочки"""
    rod = FISHING_RODS[rod_id]
    rarity_bonus = rod["rarity_bonus"]
    
    weighted_fish = []
    for fish_name, fish_data in FISH_DATA.items():
        weight = max(1, int(fish_data["rarity"] * rarity_bonus * 100))
        weighted_fish.extend([fish_name] * weight)
    
    return random.choice(weighted_fish)

def check_fishing_button_owner(call, user_id):
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "🎣 Это не твоя кнопка!", show_alert=True)
        return False
    return True

def format_weight(weight, unit):
    """Форматирует вес рыбы"""
    if unit == "тонн":
        return f"{weight:.3f} т"
    elif weight >= 1000:
        return f"{weight/1000:.3f} т"
    elif weight >= 1:
        return f"{weight:.3f} кг"
    elif weight >= 0.001:
        return f"{weight*1000:.1f} г"
    else:
        return f"{weight*1000000:.0f} мг"
        
# ================== 🎣 КОМАНДА: РЫБАЛКА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["рыбалка", "рыбачить", "ловить рыбу"])
def fishing_command(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

    # Проверяем можно ли рыбачить
    can_fish_result, result_data = can_fish(user_id)

    if not can_fish_result:
        if "2⭐" in result_data:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton(
                    "⚡ Восстановить энергию",
                    callback_data=f"fishing_recover_energy_{user_id}"
                )
            )
            bot.reply_to(message, result_data, parse_mode="HTML", reply_markup=kb)
        else:
            bot.reply_to(message, result_data, parse_mode="HTML")
        return

    user_data = result_data

    # ===== ИЗНОС БЕЗ РАНДОМА =====
    user_data["rod_durability"] -= 1

    if user_data["rod_durability"] <= 0:
        user_data["rod_id"] = 0
        user_data["rod_durability"] = 0
        update_fishing_user(user_id, user_data)

        bot.reply_to(message, "🎣 Твоя удочка износилась и сломалась.", parse_mode="HTML")
        return

    # 20% шанс что ничего не клюнет
    if random.random() < 0.2:
        user_data["energy"] -= 1
        user_data["last_fishing_time"] = datetime.now().isoformat()
        update_fishing_user(user_id, user_data)

        bot.reply_to(message, "🎏 На удочку ничего не клюнуло, попробуй ещё раз.", parse_mode="HTML")
        return

    # Получаем рыбу
    fish_name = get_random_fish(user_data["rod_id"])
    fish_data = FISH_DATA[fish_name]

    weight = random.uniform(fish_data["min_weight"], fish_data["max_weight"])
    unit = fish_data["unit"]
    price_per_kg = fish_data["price"]

    if unit == "тонн":
        fish_price = int(price_per_kg * 1000 * weight)
    else:
        fish_price = int(price_per_kg * weight)

    add_fish_to_inventory(user_id, fish_name, fish_price, 1)

    # Обновляем данные
    user_data["energy"] -= 1
    user_data["total_fish_caught"] += 1
    user_data["last_fishing_time"] = datetime.now().isoformat()

    update_fishing_user(user_id, user_data)

    weight_display = format_weight(weight, unit)

    result_text = (
        f"{mention}, 🎣 тебе попалась рыба <b>{fish_name}</b>\n"
        f"⚖ Вес: <code>{weight_display}</code>\n"
        f"💰 Цена: <code>{format_number(fish_price)} izzzy</code>\n"
        f"⚡ Энергии осталось: <code>{user_data['energy']}/{user_data['max_energy']}</code>\n"
        f"🔧 Прочность удочки: <code>{user_data['rod_durability']}</code>"
    )

    bot.reply_to(message, result_text, parse_mode="HTML")

# ================== 🎣 ВОССТАНОВЛЕНИЕ ЭНЕРГИИ ЗА ЗВЁЗДЫ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_recover_energy_"))
def fishing_recover_energy_callback(call):
    try:
        user_id = int(call.data.split("_")[3])
        
        if not check_fishing_button_owner(call, user_id):
            return
        
        user_data = get_fishing_user(user_id)
        
        # Создаем платеж на 2 звезды
        stars_amount = 2
        payment_id = create_star_payment(user_id, stars_amount, 0)  # amount=0 так как это восстановление энергии
        
        title = "Восстановление энергии для рыбалки"
        description = f"Восстановление 100% энергии (2⭐)"
        currency = "XTR"  # Telegram Stars
        
        price = types.LabeledPrice(label="Восстановление энергии", amount=stars_amount)
        
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=title,
            description=description,
            invoice_payload=f"fishing_energy_{payment_id}_{user_id}",
            provider_token="",  # Telegram Stars
            currency=currency,
            prices=[price],
            start_parameter="fishing-energy"
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка восстановления энергии: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# Обработка успешной оплаты для восстановления энергии
@bot.pre_checkout_query_handler(func=lambda q: q.invoice_payload.startswith("fishing_energy_"))
def fishing_energy_pre_checkout(pre_q):
    bot.answer_pre_checkout_query(pre_q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'], func=lambda m: m.successful_payment.invoice_payload.startswith("fishing_energy_"))
def fishing_energy_payment_success(message):
    try:
        payload = message.successful_payment.invoice_payload
        parts = payload.split("_")
        payment_id = parts[2]
        user_id = int(parts[3])
        
        # Проверяем, что платёж принадлежит этому пользователю
        if message.from_user.id != user_id:
            bot.send_message(message.chat.id, "❌ Ошибка: платёж принадлежит другому пользователю!")
            return
        
        # Получаем информацию о платеже из базы
        payment_info = get_star_payment(payment_id)
        if not payment_info:
            bot.send_message(message.chat.id, "⚠️ Платёж не найден в базе.")
            return
        
        # Помечаем платёж как завершённый
        complete_star_payment(payment_id)
        
        # Восстанавливаем энергию
        user_data = get_fishing_user(user_id)
        user_data["energy"] = user_data["max_energy"]
        update_fishing_user(user_id, user_data)
        
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        bot.send_message(
            message.chat.id,
            f"⚡ {mention}, ты купил 100% энергии за 2⭐, можно дальше рыбачить.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки успешной оплаты энергии: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при восстановлении энергии!")

# ================== 🎣 КОМАНДА: МОЯ РЫБАЛКА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["моя рыбалка", "рыбалка профиль"])
def my_fishing(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    user_data = get_fishing_user(user_id)
    inventory, total_value = get_fish_inventory(user_id)
    
    # Регенерируем энергию
    user_data = regenerate_fishing_energy(user_id)
    
    # Получаем информацию о текущей удочке
    if user_data["rod_id"] == 0:
        rod_name = "Нет удочки"
    else:
        rod_info = FISHING_RODS.get(user_data["rod_id"], {})
        rod_name = rod_info.get("name", "Неизвестно")
    
    text = (
        f"{mention}, твоё меню рыбалки:\n\n"
        f"🎣 Удочка: <b>{rod_name}</b>\n"
        f"🐟 <b>Словлено всего рыб:</b> <code>{format_number(user_data['total_fish_caught'])}</code>\n"
        f"💡 <b>Энергий:</b> <code>{user_data['energy']}/{user_data['max_energy']}</code>\n"
        f"💵 <b>Выручка за все время:</b> <code>{format_number(user_data['total_earned'])} izzzy</code>\n"
        f"🏧 <b>Потрачено всего денег в рыбалке:</b> <code>{format_number(user_data['total_spent'])} izzzy</code>"
    )
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎣 Магазин удочек", callback_data=f"fishing_shop_{user_id}"),
        InlineKeyboardButton("🐟 Мои рыбы", callback_data=f"fishing_inventory_{user_id}")
    )
    
    try:
        bot.send_photo(
            message.chat.id,
            FISHING_IMAGE_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        # ================== 🎣 МАГАЗИН УДОЧЕК ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_shop_"))
def fishing_shop_callback(call):
    try:
        user_id = int(call.data.split("_")[2])

        if not check_fishing_button_owner(call, user_id):
            return

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        text = (
            f"{mention}, <b>🎣 Магазин удочек</b>\n\n"
            f"<b>⚠️ При покупке новой удочки старая исчезает.</b>\n\n"
        )

        for rod_id, rod_info in FISHING_RODS.items():
            if rod_info["sellable"]:
                text += (
                    f"<b>{rod_id}. {rod_info['name']}</b>\n"
                    f"💰 Цена: <code>{format_number(rod_info['price'])} izzzy</code>\n"
                    f"⚡ Бонус к редкой рыбе: x{rod_info['rarity_bonus']}\n"
                    f"🔧 Прочность: {rod_info['durability']} рыбалок\n\n"
                )

        kb = InlineKeyboardMarkup(row_width=1)

        for rod_id, rod_info in FISHING_RODS.items():
            if rod_info["sellable"]:
                kb.add(InlineKeyboardButton(
                    f"{rod_id}. {rod_info['name']}",
                    callback_data=f"fishing_buy_rod_{user_id}_{rod_id}"
                ))

        kb.add(InlineKeyboardButton("‹ Назад", callback_data=f"fishing_back_{user_id}"))

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка магазина удочек: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ================== 🎣 ПОКУПКА УДОЧКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_buy_rod_"))
def fishing_buy_rod_callback(call):
    try:
        parts = call.data.split("_")
        user_id = int(parts[3])
        rod_id = int(parts[4])

        if not check_fishing_button_owner(call, user_id):
            return

        if rod_id not in FISHING_RODS or not FISHING_RODS[rod_id]["sellable"]:
            bot.answer_callback_query(call.id, "❌ Неверная удочка!", show_alert=True)
            return

        rod_info = FISHING_RODS[rod_id]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        text = (
            f"{mention}, это <b>{rod_info['name']}</b>:\n\n"
            f"💰 Стоимость: <code>{format_number(rod_info['price'])} izzzy</code>\n"
            f"⚡ Бонус к редкой рыбе: x{rod_info['rarity_bonus']}\n"
            f"🔧 Прочность: {rod_info['durability']} рыбалок\n\n"
            f"<b>⛔ Ты точно хочешь купить эту удочку?</b>"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Да", callback_data=f"fishing_confirm_buy_{user_id}_{rod_id}"),
            InlineKeyboardButton("Нет", callback_data=f"fishing_shop_{user_id}")
        )

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка покупки удочки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_confirm_buy_"))
def fishing_confirm_buy_callback(call):
    try:
        parts = call.data.split("_")
        user_id = int(parts[3])
        rod_id = int(parts[4])

        if not check_fishing_button_owner(call, user_id):
            return

        if rod_id not in FISHING_RODS or not FISHING_RODS[rod_id]["sellable"]:
            bot.answer_callback_query(call.id, "❌ Неверная удочка!", show_alert=True)
            return

        rod_info = FISHING_RODS[rod_id]

        user_data_main = get_user_data(user_id)

        if user_data_main["balance"] < rod_info["price"]:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств!", show_alert=True)
            return

        user_data_main["balance"] -= rod_info["price"]
        save_casino_data()

        fishing_user = get_fishing_user(user_id)
        fishing_user["total_spent"] += rod_info["price"]

        fishing_user["rod_id"] = rod_id
        fishing_user["rod_durability"] = rod_info["durability"]
        fishing_user["max_durability"] = rod_info["durability"]

        update_fishing_user(user_id, fishing_user)

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        text = (
            f"{mention}, ты купил <b>{rod_info['name']}</b> "
            f"за <code>{format_number(rod_info['price'])} izzzy</code>.\n\n"
            f"Теперь удочка выдержит <b>{rod_info['durability']}</b> рыбалок."
        )

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("‹ Назад", callback_data=f"fishing_back_{user_id}"))

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )

        bot.answer_callback_query(call.id, "✅ Удочка куплена!")

    except Exception as e:
        logger.error(f"Ошибка подтверждения покупки удочки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
        
        # ================== 🎣 ИНВЕНТАРЬ РЫБ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_inventory_"))
def fishing_inventory_callback(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        if not check_fishing_button_owner(call, user_id):
            return
        
        inventory, total_value = get_fish_inventory(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        if not inventory:
            text = f"{mention}, ниже все виды рыб которые ты ловил:\n\n<i>У тебя пока нет рыб.</i>"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("‹ Назад", callback_data=f"fishing_back_{user_id}"))
        else:
            text = f"{mention}, ниже все виды рыб которые ты ловил:\n\n"
            
            # Сортируем по убыванию количества
            sorted_fish = sorted(inventory.items(), key=lambda x: x[1]["quantity"], reverse=True)
            
            for fish_name, data in sorted_fish:
                text += f"<b>{fish_name}</b> - <code>{data['quantity']}</code>\n"
            
            text += f"\n💰 Общая стоимость: <code>{format_number(total_value)} izzzy</code>"
            
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("💰 Продать все рыбы", callback_data=f"fishing_sell_all_{user_id}"))
            kb.add(InlineKeyboardButton("‹ Назад", callback_data=f"fishing_back_{user_id}"))
        
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка инвентаря рыб: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== 🎣 ПРОДАЖА ВСЕХ РЫБ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_sell_all_"))
def fishing_sell_all_callback(call):
    try:
        user_id = int(call.data.split("_")[3])
        
        if not check_fishing_button_owner(call, user_id):
            return
        
        inventory, total_value = get_fish_inventory(user_id)
        
        if not inventory:
            bot.answer_callback_query(call.id, "❌ У тебя нет рыб для продажи!", show_alert=True)
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"{mention}, ⚠️ Ты точно хочешь продать все рыбы?"
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Да", callback_data=f"fishing_confirm_sell_{user_id}"),
            InlineKeyboardButton("Нет", callback_data=f"fishing_inventory_{user_id}")
        )
        
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка продажи всех рыб: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_confirm_sell_"))
def fishing_confirm_sell_callback(call):
    try:
        user_id = int(call.data.split("_")[3])
        
        if not check_fishing_button_owner(call, user_id):
            return
        
        # Продаём всю рыбу
        total_value = sell_all_fish(user_id)
        
        if total_value <= 0:
            bot.answer_callback_query(call.id, "❌ У тебя нет рыб для продажи!", show_alert=True)
            return
        
        # Начисляем деньги на баланс
        user_data_main = get_user_data(user_id)
        user_data_main["balance"] += total_value
        
        # Обновляем статистику рыбалки
        fishing_user = get_fishing_user(user_id)
        fishing_user["total_earned"] += total_value
        
        save_casino_data()
        update_fishing_user(user_id, fishing_user)
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"{mention}, ты успешно продал всех своих рыб за <code>{format_number(total_value)} izzzy</code>"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("‹ Назад", callback_data=f"fishing_back_{user_id}"))
        
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )
        
        bot.answer_callback_query(call.id, f"✅ +{format_number(total_value)} izzzy")
        
    except Exception as e:
        logger.error(f"Ошибка подтверждения продажи рыб: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== 🎣 ВОЗВРАТ В МЕНЮ РЫБАЛКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("fishing_back_"))
def fishing_back_callback(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        if not check_fishing_button_owner(call, user_id):
            return
        
        # Создаем фейковое сообщение
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = from_user
        
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        my_fishing(fake_msg)
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка возврата в рыбалку: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

print("✅ Система рыбалки с 100+ видами рыб загружена и готова к работе! 🎣")
    



# ================== БАНКОВСКАЯ СИСТЕМА MEOW BANK ==================
BANK_DB = "meow_bank.db"

# Инициализация базы данных для банка
def init_bank_db():
    conn = sqlite3.connect(BANK_DB)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            account_number TEXT UNIQUE,
            balance REAL DEFAULT 0,
            deposit_amount REAL DEFAULT 0,
            interest_rate REAL DEFAULT 1.2,
            created_at TEXT,
            last_interest TEXT,
            interest_earned REAL DEFAULT 0,
            last_deposit TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_bank_db()

def generate_account_number():
    """Генерирует уникальный номер счета"""
    import random
    characters = "0123456789ABCDEF"
    while True:
        part1 = ''.join(random.choice(characters) for _ in range(5))
        part2 = ''.join(random.choice(characters) for _ in range(5))
        part3 = ''.join(random.choice(characters) for _ in range(5))
        account_number = f"{part1}-{part2}-{part3}"
        
        # Проверяем уникальность
        conn = sqlite3.connect(BANK_DB)
        c = conn.cursor()
        c.execute("SELECT 1 FROM bank_accounts WHERE account_number = ?", (account_number,))
        exists = c.fetchone()
        conn.close()
        
        if not exists:
            return account_number

def get_bank_account(user_id):
    """Получает информацию о банковском счете пользователя (с округлением)"""
    conn = sqlite3.connect(BANK_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT account_number, balance, deposit_amount, interest_rate, 
               created_at, last_interest, interest_earned, username, last_deposit
        FROM bank_accounts 
        WHERE user_id = ?
    """, (user_id,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        # Округляем все денежные значения до целых чисел
        balance = result[1]
        if isinstance(balance, float):
            balance = int(round(balance))
        
        deposit_amount = result[2]
        if isinstance(deposit_amount, float):
            deposit_amount = int(round(deposit_amount))
        
        interest_earned = result[6]
        if isinstance(interest_earned, float):
            interest_earned = int(round(interest_earned))
        
        return {
            "account_number": result[0],
            "balance": balance,
            "deposit_amount": deposit_amount,
            "interest_rate": result[3],
            "created_at": result[4],
            "last_interest": result[5],
            "interest_earned": interest_earned,
            "username": result[7],
            "last_deposit": result[8]
        }
    return None

def create_bank_account(user_id, username):
    """Создает новый банковский счет"""
    account = get_bank_account(user_id)
    if account:
        return False, "У тебя уже есть банковский счет!"
    
    account_number = generate_account_number()
    now = datetime.now().isoformat()
    
    conn = sqlite3.connect(BANK_DB)
    c = conn.cursor()
    
    try:
        c.execute("""
            INSERT INTO bank_accounts 
            (user_id, username, account_number, created_at, last_interest, last_deposit) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, account_number, now, now, now))
        
        conn.commit()
        return True, account_number
    except Exception as e:
        return False, f"Ошибка создания счета: {e}"
    finally:
        conn.close()

def deposit_to_account(user_id, amount):
    """Пополняет банковский счет"""
    account = get_bank_account(user_id)  # Используем исправленную функцию с округлением
    if not account:
        return False, "У тебя нет банковского счета!"
    
    # Проверяем, что amount - целое число
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return False, "❌ Сумма должна быть целым числом!"
    
    if amount <= 0:
        return False, "❌ Сумма должна быть больше 0!"
    
    # Проверяем баланс пользователя
    user_data = get_user_data(user_id)
    if user_data["balance"] < amount:
        return False, "🔴 На твоём счёту нет столько средств"
    
    # Списываем с баланса и добавляем на счет (целые числа)
    user_data["balance"] -= amount
    save_casino_data()
    
    conn = sqlite3.connect(BANK_DB)
    c = conn.cursor()
    
    # Получаем текущие значения из БД (не из кэшированного account)
    c.execute("SELECT balance, deposit_amount FROM bank_accounts WHERE user_id = ?", (user_id,))
    db_result = c.fetchone()
    
    if db_result:
        current_balance = db_result[0]
        if isinstance(current_balance, float):
            current_balance = int(round(current_balance))
        
        current_deposit = db_result[1]
        if isinstance(current_deposit, float):
            current_deposit = int(round(current_deposit))
    else:
        current_balance = 0
        current_deposit = 0
    
    # Рассчитываем новые значения (целые числа)
    new_balance = current_balance + amount
    new_deposit = current_deposit + amount
    now = datetime.now().isoformat()
    
    c.execute("""
        UPDATE bank_accounts 
        SET balance = ?, deposit_amount = ?, last_deposit = ?
        WHERE user_id = ?
    """, (new_balance, new_deposit, now, user_id))
    
    conn.commit()
    conn.close()
    
    return True, new_balance

def calculate_daily_interest():
    """Начисляет ежедневные проценты (вызывается автоматически в 03:00)"""
    conn = sqlite3.connect(BANK_DB)
    c = conn.cursor()
    
    c.execute("SELECT user_id, balance, interest_rate, last_interest FROM bank_accounts WHERE balance > 0")
    accounts = c.fetchall()
    
    now = datetime.now().isoformat()
    updated_count = 0
    
    for user_id, balance, interest_rate, last_interest in accounts:
        # Проверяем, не начислялись ли проценты сегодня
        if last_interest:
            last_date = datetime.fromisoformat(last_interest).date()
            today = datetime.now().date()
            if last_date >= today:
                continue
        
        # Рассчитываем проценты (1.2% годовых = 0.00328767% в день)
        daily_rate = interest_rate / 365 / 100
        interest = balance * daily_rate
        
        # ИЗМЕНЕНО: Округляем до ЦЕЛОГО числа (без копеек)
        interest = int(round(interest))
        
        if interest > 0:
            # Начисляем проценты
            new_balance = balance + interest
            
            # ИЗМЕНЕНО: Проценты за день тоже округляем
            new_interest_earned = int(round(balance * (interest_rate / 100) * (1/365)))
            
            c.execute("""
                UPDATE bank_accounts 
                SET balance = ?, interest_earned = interest_earned + ?, last_interest = ?
                WHERE user_id = ?
            """, (new_balance, interest, now, user_id))
            
            updated_count += 1
    
    conn.commit()
    conn.close()
    
    if updated_count > 0:
        logger.info(f"💰 Начислены проценты для {updated_count} счетов")
    
    return updated_count

def withdraw_from_account(user_id):
    """Снимает все средства со счета"""
    account = get_bank_account(user_id)
    if not account:
        return False, "У тебя нет банковского счета!"
    
    if account["balance"] <= 0:
        return False, "На счету нет средств для снятия!"
    
    # ИЗМЕНЕНО: Округляем баланс перед снятием
    amount_to_withdraw = int(round(account["balance"]))
    
    # Добавляем средства на баланс пользователя
    user_data = get_user_data(user_id)
    user_data["balance"] += amount_to_withdraw
    save_casino_data()
    
    # Обнуляем счет (но не удаляем)
    conn = sqlite3.connect(BANK_DB)
    c = conn.cursor()
    
    c.execute("""
        UPDATE bank_accounts 
        SET balance = 0, deposit_amount = 0, interest_earned = 0
        WHERE user_id = ?
    """, (user_id,))
    
    conn.commit()
    conn.close()
    
    return True, amount_to_withdraw

def delete_bank_account(user_id):
    """Удаляет банковский счет"""
    account = get_bank_account(user_id)
    if not account:
        return False, "🚥 У тебя нету счёта чтобы удалить."
    
    # Проверяем, есть ли деньги на счету
    # ИЗМЕНЕНО: Проверяем округленное значение
    account_balance = account.get("balance", 0)
    if isinstance(account_balance, float):
        account_balance = int(round(account_balance))
    
    if account_balance > 0:
        return False, "pending_confirmation"
    
    # Удаляем счет
    conn = sqlite3.connect(BANK_DB)
    c = conn.cursor()
    
    c.execute("DELETE FROM bank_accounts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return True, "✅ Счёт успешно удалён."
    
def calculate_time_info(created_at, last_deposit, last_interest):
    """Рассчитывает информацию о времени"""
    from datetime import datetime, timedelta
    
    created = datetime.fromisoformat(created_at)
    now = datetime.now()
    
    # Активный период (разница между созданием и сейчас)
    active_diff = now - created
    active_hours = active_diff.seconds // 3600
    active_minutes = (active_diff.seconds % 3600) // 60
    
    # Осталось (30 дней с момента создания)
    expires_at = created + timedelta(days=30)
    time_left = expires_at - now
    
    if time_left.total_seconds() <= 0:
        days_left = 0
        hours_left = 0
        minutes_left = 0
    else:
        days_left = time_left.days
        hours_left = time_left.seconds // 3600
        minutes_left = (time_left.seconds % 3600) // 60
    
    # Форматируем даты
    created_str = created.strftime("%d.%m.%Y в %H:%M")
    expires_str = expires_at.strftime("%d.%m.%Y в %H:%M")
    
    # Дата последнего пополнения
    deposit_str = "Нет пополнений"
    if last_deposit:
        deposit_date = datetime.fromisoformat(last_deposit)
        deposit_str = deposit_date.strftime("%d.%m.%Y в %H:%M")
    
    # Дата последнего начисления
    interest_str = "Ещё не начислялись"
    if last_interest:
        interest_date = datetime.fromisoformat(last_interest)
        interest_str = interest_date.strftime("%d.%m.%Y в %H:%M")
    
    return {
        "active_hours": active_hours,
        "active_minutes": active_minutes,
        "days_left": days_left,
        "hours_left": hours_left,
        "minutes_left": minutes_left,
        "created_str": created_str,
        "expires_str": expires_str,
        "deposit_str": deposit_str,
        "interest_str": interest_str
    }
    
    
    # ================== АВТОМАТИЧЕСКОЕ НАЧИСЛЕНИЕ ПРОЦЕНТОВ ==================

def start_interest_calculation_loop():
    """Запускает автоматическое начисление процентов каждый день в 03:00"""
    def interest_loop():
        while True:
            try:
                now = datetime.now()
                
                # Если сейчас 03:00, начисляем проценты
                if now.hour == 3 and now.minute == 0:
                    calculate_daily_interest()
                    logger.info("💰 Ежедневные проценты начислены")
                    
                    # Ждем 24 часа до следующей проверки
                    time.sleep(24 * 3600 - 60)  # Минус 60 секунд на случай погрешности
                else:
                    # Ждем 1 минуту до следующей проверки
                    time.sleep(60)
                    
            except Exception as e:
                logger.error(f"Ошибка в цикле начисления процентов: {e}")
                time.sleep(300)  # Ждем 5 минут при ошибке
    
    # Запускаем в отдельном потоке
    interest_thread = threading.Thread(target=interest_loop, daemon=True)
    interest_thread.start()
    logger.info("✅ Система начисления банковских процентов запущена (ежедневно в 03:00)")

# Запускаем систему начисления процентов
start_interest_calculation_loop()

# ================== КОМАНДЫ БАНКА ==================

@bot.message_handler(func=lambda m: m.text and (
    m.text.lower() == "открыть счёт" or 
    m.text.lower() == "открыть счет"
))
def open_bank_account(message):
    """Открывает банковский счет"""
    user_id = message.from_user.id
    username = message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{username}</a>'
    
    # Проверяем, есть ли уже счет
    existing_account = get_bank_account(user_id)
    if existing_account:
        bot.reply_to(message, f"{mention}, у тебя уже есть банковский счет!")
        return
    
    # Создаем счет
    success, result = create_bank_account(user_id, username)
    
    if success:
        bot.reply_to(
            message,
            f"✅ {mention}, твой банковский счет успешно создан!\n\n"
            f"🏛 <b>Meow Bank</b>\n"
            f"👤 Владелец: {mention}\n"
            f"🔢 Номер счета: <code>{result}</code>\n"
            f"🏦 Процентная ставка: <b>1.2% годовых</b>\n\n"
            f"📈 <b>Как работают проценты:</b>\n"
            f"• Начисляются <b>ежедневно в 03:00 по МСК</b>\n"
            f"• При 100,000 izzzy вы получите ~3.29 izzzy в день\n"
            f"• Это ~100 izzzy в месяц\n\n"
            f"💳 Пополнить счет:\n"
            f"<code>пополнить счёт [сумма]</code>",
            parse_mode="HTML"
        )
    else:
        bot.reply_to(message, f"❌ {result}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("пополнить счёт"))
def deposit_to_bank(message):
    """Пополняет банковский счет"""
    user_id = message.from_user.id
    username = message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{username}</a>'
    
    # Парсим сумму
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(
            message,
            f"❌ {mention}, неправильный формат!\n\n"
            f"Используй: <code>пополнить счёт [сумма]</code>\n"
            f"Пример: <code>пополнить счёт 100000</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        amount = int(parts[2])
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0!")
            return
        
        # Проверяем минимальный депозит
        if amount < 1000:
            bot.reply_to(message, "❌ Минимальная сумма депозита: 1,000 izzzy")
            return
            
    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом!")
        return
    
    # Пополняем счет
    success, result = deposit_to_account(user_id, amount)
    
    if success:
        user_data = get_user_data(user_id)
        account = get_bank_account(user_id)
        
        # Рассчитываем примерные ежедневные проценты
        daily_interest = amount * (account["interest_rate"] / 365 / 100)
        monthly_interest = daily_interest * 30
        
        bot.reply_to(
            message,
            f"✅ {mention}, счет успешно пополнен на <code>{format_number(amount)}$</code>\n\n"
            f"💰 На счету: <code>{format_number(result)} izzzy</code>\n"
            f"💵 На балансе: <code>{format_number(user_data['balance'])} izzzy</code>\n\n"
            f"📈 <b>Будущие начисления:</b>\n"
            f"• Ежедневно: ~<code>{format_number(round(daily_interest, 2))} izzzy</code>\n"
            f"• В месяц: ~<code>{format_number(round(monthly_interest, 2))} izzzy</code>\n\n"
            f"⏰ Проценты начисляются <b>ежедневно в 03:00 по МСК</b>",
            parse_mode="HTML"
        )
    else:
        bot.reply_to(message, result)

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "мой счёт")
def my_bank_account(message):
    """Показывает информацию о банковском счете"""
    user_id = message.from_user.id
    username = message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{username}</a>'
    
    account = get_bank_account(user_id)
    if not account:
        bot.reply_to(
            message,
            f"🏛 {mention}, у тебя еще нет банковского счета!\n\n"
            f"Открой счет командой: <code>открыть счёт</code>",
            parse_mode="HTML"
        )
        return
    
    # Рассчитываем информацию о времени
    time_info = calculate_time_info(
        account["created_at"], 
        account.get("last_deposit"),
        account.get("last_interest")
    )
    
    # Рассчитываем прогнозные проценты
    daily_interest = account["balance"] * (account["interest_rate"] / 365 / 100)
    monthly_interest = daily_interest * 30
    
    # Форматируем текст
    text = (
        f"🏛 <b>Банковский депозит</b>\n\n"
        f"👤 Пользователь: {mention}\n"
        f"🆔 Счёт: <code>{account['account_number']}</code>\n\n"
        f"⏳ Активный период: {time_info['active_hours']} час. {time_info['active_minutes']} мин.\n"
        f"⏱ Осталось: {time_info['days_left']} дн. {time_info['hours_left']} час. {time_info['minutes_left']} мин.\n\n"
        f"💰 <b>Финансовая информация</b>\n"
        f"├ 💳 Текущий баланс: {format_number(account['balance'])} izzzy\n"
        f"├ 📈 Начислено: {format_number(round(account['interest_earned'], 2))} izzzy\n"
        f"└ 🏦 Ставка: {account['interest_rate']}% годовых\n\n"
        f"📈 <b>Прогноз начислений:</b>\n"
        f"├ 📊 В день: ~{format_number(round(daily_interest, 2))} izzzy\n"
        f"└ 📅 В месяц: ~{format_number(round(monthly_interest, 2))} izzzy\n\n"
        f"📅 <b>Даты операций</b>\n"
        f"├ 📌 Открытие: {time_info['created_str']}\n"
        f"├ ➕ Последнее пополнение: {time_info['deposit_str']}\n"
        f"└ 🏁 Последнее начисление: {time_info['interest_str']} по МСК\n\n"
        f"⏰ <i>Проценты начисляются ежедневно в 03:00 по МСК</i>"
    )
    
    # Создаем кнопку
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Снять с банка", callback_data=f"bank_withdraw_{user_id}"))
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)
    
@bot.callback_query_handler(func=lambda c: c.data.startswith("bank_withdraw_"))
def bank_withdraw_callback(call):
    """Обработка кнопки снятия средств"""
    try:
        # Разбираем callback data
        parts = call.data.split("_")
        
        # Определяем, какая кнопка нажата
        if len(parts) == 3:
            # Это основная кнопка "Снять с банка"
            user_id = int(parts[2])
            
            # Проверяем владельца кнопки
            if call.from_user.id != user_id:
                bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
                return
            
            mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
            
            text = f"{mention}, ты точно хочешь снять весь баланс?"
            
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("Да", callback_data=f"bank_withdraw_confirm_{user_id}"),
                InlineKeyboardButton("Нет", callback_data=f"bank_withdraw_cancel_{user_id}")
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )
            bot.answer_callback_query(call.id)
            
        elif len(parts) == 4:
            # Это кнопка "Да" или "Нет"
            action = parts[2]  # confirm или cancel
            user_id = int(parts[3])
            
            # Проверяем владельца кнопки
            if call.from_user.id != user_id:
                bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
                return
            
            if action == "confirm":
                # Подтверждение снятия средств
                success, amount = withdraw_from_account(user_id)
                
                if success:
                    mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
                    user_data = get_user_data(user_id)
                    
                    text = (
                        f"{mention}, средства с банка успешно сняты и отправлены на твой баланс ✅\n\n"
                        f"💰 Снято: <code>{format_number(amount)} izzzy</code>\n"
                        f"💵 Текущий баланс: <code>{format_number(user_data['balance'])} izzzy</code>"
                    )
                    
                    bot.edit_message_text(
                        text,
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML"
                    )
                    bot.answer_callback_query(call.id, f"Деньги на балике вацок")
                else:
                    bot.answer_callback_query(call.id, f"❌ {amount}", show_alert=True)
                    
            elif action == "cancel":
                # Отмена снятия средств
                mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
                
                # Возвращаем к информации о счете
                bot.edit_message_text(
                    f"❌ {mention}, снятие средств отменено.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML"
                )
                bot.answer_callback_query(call.id, "❌ Снятие отменено")
                
    except Exception as e:
        logger.error(f"Ошибка снятия средств: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bank_withdraw_confirm_"))
def bank_withdraw_confirm(call):
    """Подтверждение снятия средств"""
    try:
        user_id = int(call.data.split("_")[3])
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Снимаем средства
        success, amount = withdraw_from_account(user_id)
        
        if success:
            mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
            user_data = get_user_data(user_id)
            
            text = (
                f"{mention}, средства с банка успешно сняты и отправлены на твой баланс ✅\n\n"
                f"💰 Снято: <code>{format_number(amount)} izzzy</code>\n"
                f"💵 Текущий баланс: <code>{format_number(user_data['balance'])} izzzy</code>"
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            bot.answer_callback_query(call.id, f"Вацок")
        else:
            bot.answer_callback_query(call.id, f"❌ {amount}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка подтверждения снятия: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при снятии средств!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bank_withdraw_cancel_"))
def bank_withdraw_cancel(call):
    """Отмена снятия средств"""
    try:
        user_id = int(call.data.split("_")[3])
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Возвращаем к информации о счете
        my_bank_account(call.message)
        
        # Удаляем старое сообщение
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
            
        bot.answer_callback_query(call.id, "❌ Снятие отменено")
        
    except Exception as e:
        logger.error(f"Ошибка отмены снятия: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.message_handler(func=lambda m: m.text and (
    m.text.lower() == "удалить счёт" or 
    m.text.lower() == "удалить счет"
))
def delete_account_command(message):
    """Удаляет банковский счет (работает с 'ё' и 'е')"""
    user_id = message.from_user.id
    username = message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{username}</a>'
    
    # Пытаемся удалить счет
    success, result = delete_bank_account(user_id)
    
    if not success:
        # Если вернулась строка "pending_confirmation" - это не ошибка
        if result == "pending_confirmation":
            # Нужно подтверждение, т.к. есть деньги на счету
            account = get_bank_account(user_id)
            if account:
                text = (
                    f"{mention}, вы точно хотите удалить счёт прямо сейчас?\n\n"
                    f"⚠️ На вашем счёту лежат <code>{format_number(account['balance'])} izzzy</code>\n"
                    f"📈 Накопленные проценты: <code>{format_number(round(account['interest_earned'], 2))} izzzy</code>\n\n"
                    f"❗ После удаления деньги не вернутся и вам их администратор не вернет!"
                )
                
                kb = InlineKeyboardMarkup(row_width=2)
                kb.add(
                    InlineKeyboardButton("Да, удалить", callback_data=f"bank_delete_confirm_{user_id}"),
                    InlineKeyboardButton("Нет, отменить", callback_data=f"bank_delete_cancel_{user_id}")
                )
                
                bot.reply_to(message, text, parse_mode="HTML", reply_markup=kb)
            else:
                bot.reply_to(message, "❌ Ошибка: счет не найден!")
        else:
            # Это обычная ошибка (например, "У тебя нет счета")
            bot.reply_to(message, result)
    else:
        # Счет успешно удален (когда денег не было)
        bot.reply_to(message, "✅ Счёт успешно удалён.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("bank_delete_confirm_"))
def bank_delete_confirm(call):
    """Подтверждение удаления счета с деньгами"""
    try:
        user_id = int(call.data.split("_")[3])
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Получаем информацию о счете
        account = get_bank_account(user_id)
        if not account:
            bot.answer_callback_query(call.id, "❌ Счет не найден!", show_alert=True)
            return
        
        # Если есть деньги на счету, снимаем их
        if account["balance"] > 0:
            success, amount = withdraw_from_account(user_id)
            if not success:
                bot.answer_callback_query(call.id, f"❌ Ошибка при снятии средств: {amount}", show_alert=True)
                return
        
        # Удаляем счет
        conn = sqlite3.connect(BANK_DB)
        c = conn.cursor()
        c.execute("DELETE FROM bank_accounts WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # Редактируем сообщение
        bot.edit_message_text(
            "✅ Счёт успешно удалён.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, "✅ Счет удален")
        
    except Exception as e:
        logger.error(f"Ошибка подтверждения удаления: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при удалении счета!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bank_delete_cancel_"))
def bank_delete_cancel(call):
    """Отмена удаления счета"""
    try:
        user_id = int(call.data.split("_")[3])
        
        # Проверяем владельца кнопки
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Просто удаляем сообщение с кнопками
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
            
        bot.answer_callback_query(call.id, "❌ Удаление отменено")
        
    except Exception as e:
        logger.error(f"Ошибка отмены удаления: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

print("✅ Банковская система Meow Bank загружена и готова к работе! 🏛")
        
 
# ================== СИСТЕМА ШАХТЫ (МАЙНИНГ) ==================
MINING_DB = "mining.db"

# Инициализация базы данных для шахты
def init_mining_db():
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    # Таблица пользователей шахты
    c.execute("""
        CREATE TABLE IF NOT EXISTS mining_users (
            user_id INTEGER PRIMARY KEY,
            pickaxe_id INTEGER DEFAULT 1,
            energy INTEGER DEFAULT 50,
            max_energy INTEGER DEFAULT 50,
            pickaxe_durability INTEGER DEFAULT 100,
            max_durability INTEGER DEFAULT 100,
            total_ores_mined INTEGER DEFAULT 0,
            last_energy_regen TEXT,
            last_mining_time TEXT
        )
    """)
    
    # Таблица инвентаря руд
    c.execute("""
        CREATE TABLE IF NOT EXISTS mining_ores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ore_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES mining_users(user_id)
        )
    """)
    
    # Таблица рекламы
    c.execute("""
        CREATE TABLE IF NOT EXISTS mining_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            link TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_mining_db()

# Конфигурация кирок
PICKAXES = {
    1: {"id": 1, "name": "⛏️ Деревянная кирка", "price": 15000, "rarity_bonus": 1.0, "durability": 100},
    2: {"id": 2, "name": "🔨 Каменная кирка", "price": 40000, "rarity_bonus": 1.2, "durability": 150},
    3: {"id": 3, "name": "⚒️ Железная кирка", "price": 65000, "rarity_bonus": 1.5, "durability": 200},
    4: {"id": 4, "name": "⛓️ Стальная кирка", "price": 90000, "rarity_bonus": 1.8, "durability": 250},
    5: {"id": 5, "name": "💎 Алмазная кирка", "price": 150000, "rarity_bonus": 2.2, "durability": 300},
    6: {"id": 6, "name": "🔥 Огненная кирка", "price": 300000, "rarity_bonus": 2.7, "durability": 350},
    7: {"id": 7, "name": "✨ Божественная кирка", "price": 600000, "rarity_bonus": 3.5, "durability": 500}
}

# Конфигурация руд (30 видов)
ORES = {
    "🪨 Камень": {"price": 50, "rarity": 30},
    "🪵 Уголь": {"price": 100, "rarity": 25},
    "🔶 Медь": {"price": 200, "rarity": 20},
    "⚪ Олово": {"price": 350, "rarity": 18},
    "🟡 Железо": {"price": 500, "rarity": 15},
    "🔘 Свинец": {"price": 700, "rarity": 13},
    "🟢 Цинк": {"price": 900, "rarity": 12},
    "🟤 Никель": {"price": 1200, "rarity": 10},
    "🔵 Алюминий": {"price": 1500, "rarity": 9},
    "🟣 Магний": {"price": 1800, "rarity": 8},
    "🔴 Титан": {"price": 2200, "rarity": 7},
    "⚫ Вольфрам": {"price": 2700, "rarity": 6},
    "🟠 Кобальт": {"price": 3200, "rarity": 5},
    "🔷 Серебро": {"price": 4000, "rarity": 4},
    "🟡 Золото": {"price": 5000, "rarity": 3.5},
    "🔶 Платина": {"price": 6500, "rarity": 3},
    "💎 Изумруд": {"price": 8500, "rarity": 2.0},
    "🔵 Сапфир": {"price": 11000, "rarity": 2},
    "🔴 Рубин": {"price": 14000, "rarity": 1.1},
    "💎 Алмаз": {"price": 18000, "rarity": 1.0},
    "✨ Кристалл": {"price": 23000, "rarity": 0.7},
    "🌟 Звездная пыль": {"price": 29000, "rarity": 0.7},
    "🌕 Лунный камень": {"price": 36000, "rarity": 0.6},
    "☀️ Солнечный камень": {"price": 45000, "rarity": 0.3},
    "⚡ Громовой камень": {"price": 55000, "rarity": 0.3},
    "❄️ Ледяной кристалл": {"price": 68000, "rarity": 0.2},
    "🔥 Огненный кристалл": {"price": 82000, "rarity": 0.2},
    "💫 Космическая руда": {"price": 100000, "rarity": 0.19},
    "🌈 Радужная руда": {"price": 120000, "rarity": 0.12},
    "👑 Королевская руда": {"price": 150000, "rarity": 0.1}
}

def get_mining_user(user_id):
    """Получает данные пользователя шахты"""
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT pickaxe_id, energy, max_energy, pickaxe_durability, max_durability, 
               total_ores_mined, last_energy_regen, last_mining_time 
        FROM mining_users WHERE user_id = ?
    """, (user_id,))
    
    result = c.fetchone()
    
    if not result:
        # Создаем нового пользователя
        now = datetime.now().isoformat()
        c.execute("""
            INSERT INTO mining_users 
            (user_id, pickaxe_id, energy, max_energy, pickaxe_durability, max_durability, 
             total_ores_mined, last_energy_regen, last_mining_time) 
            VALUES (?, 1, 50, 50, 100, 100, 0, ?, ?)
        """, (user_id, now, now))
        conn.commit()
        
        conn.close()
        return {
            "pickaxe_id": 1,
            "energy": 50,
            "max_energy": 50,
            "pickaxe_durability": 100,
            "max_durability": 100,
            "total_ores_mined": 0,
            "last_energy_regen": now,
            "last_mining_time": now
        }
    
    conn.close()
    
    return {
        "pickaxe_id": result[0],
        "energy": result[1],
        "max_energy": result[2],
        "pickaxe_durability": result[3],
        "max_durability": result[4],
        "total_ores_mined": result[5],
        "last_energy_regen": result[6],
        "last_mining_time": result[7]
    }

def update_mining_user(user_id, data):
    """Обновляет данные пользователя шахты"""
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    c.execute("""
        UPDATE mining_users SET 
        pickaxe_id = ?, energy = ?, max_energy = ?, pickaxe_durability = ?, 
        max_durability = ?, total_ores_mined = ?, last_energy_regen = ?, last_mining_time = ?
        WHERE user_id = ?
    """, (
        data["pickaxe_id"], data["energy"], data["max_energy"], 
        data["pickaxe_durability"], data["max_durability"], data["total_ores_mined"],
        data["last_energy_regen"], data["last_mining_time"], user_id
    ))
    
    conn.commit()
    conn.close()

def get_user_ores(user_id):
    """Получает все руды пользователя"""
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    c.execute("SELECT ore_name, quantity FROM mining_ores WHERE user_id = ?", (user_id,))
    ores = c.fetchall()
    
    conn.close()
    return {ore_name: quantity for ore_name, quantity in ores}

def add_ore_to_user(user_id, ore_name, quantity=1):
    """Добавляет руду пользователю"""
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    # Проверяем, есть ли уже такая руда
    c.execute("SELECT quantity FROM mining_ores WHERE user_id = ? AND ore_name = ?", (user_id, ore_name))
    result = c.fetchone()
    
    if result:
        # Обновляем количество
        new_quantity = result[0] + quantity
        c.execute("UPDATE mining_ores SET quantity = ? WHERE user_id = ? AND ore_name = ?", 
                 (new_quantity, user_id, ore_name))
    else:
        # Добавляем новую руду
        c.execute("INSERT INTO mining_ores (user_id, ore_name, quantity) VALUES (?, ?, ?)", 
                 (user_id, ore_name, quantity))
    
    conn.commit()
    conn.close()

def clear_user_ores(user_id):
    """Очищает все руды пользователя"""
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    c.execute("DELETE FROM mining_ores WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def calculate_ores_value(user_id):
    """Вычисляет общую стоимость всех руд пользователя"""
    ores = get_user_ores(user_id)
    total_value = 0
    
    for ore_name, quantity in ores.items():
        if ore_name in ORES:
            total_value += ORES[ore_name]["price"] * quantity
    
    return total_value

def get_total_ores_count(user_id):
    """Получает общее количество всех руд"""
    ores = get_user_ores(user_id)
    return sum(quantity for quantity in ores.values())

def regenerate_energy(user_id):
    """Восстанавливает энергию (1 энергия каждые 2 минуты)"""
    user_data = get_mining_user(user_id)
    now = datetime.now()
    
    if user_data["last_energy_regen"]:
        last_regen = datetime.fromisoformat(user_data["last_energy_regen"])
        minutes_passed = (now - last_regen).total_seconds() / 60
        
        if minutes_passed >= 2 and user_data["energy"] < user_data["max_energy"]:
            # Восстанавливаем энергию (1 за каждые 2 минуты)
            energy_to_add = int(minutes_passed // 2)
            user_data["energy"] = min(user_data["max_energy"], user_data["energy"] + energy_to_add)
            user_data["last_energy_regen"] = now.isoformat()
            update_mining_user(user_id, user_data)
    
    return user_data

def can_mine(user_id):
    """Проверяет, может ли пользователь копать"""
    user_data = get_mining_user(user_id)
    
    # Регенерируем энергию
    user_data = regenerate_energy(user_id)
    
    # Проверяем кулдаун (2 секунды)
    if user_data["last_mining_time"]:
        last_mine = datetime.fromisoformat(user_data["last_mining_time"])
        if (datetime.now() - last_mine).total_seconds() < 2:
            return False, "⏳ Подожди 2 секунды перед следующим копанием!"
    
    # Проверяем энергию
    if user_data["energy"] <= 0:
        return False, "⚡ У тебя закончилась энергия! Подожди пока восстановится."
    
    # Проверяем прочность кирки
    if user_data["pickaxe_durability"] <= 0:
        return False, "⛏️ Твоя кирка сломалась! Купи новую в магазине."
    
    return True, "✅ Можно копать"

def get_random_ore(pickaxe_id):
    """Получает случайную руду с учетом бонуса кирки"""
    pickaxe = PICKAXES[pickaxe_id]
    rarity_bonus = pickaxe["rarity_bonus"]
    
    # Создаем взвешенный список с учетом бонуса кирки
    weighted_ores = []
    for ore_name, ore_data in ORES.items():
        # Улучшаем шансы на редкие руды в зависимости от кирки
        weight = max(1, int(ore_data["rarity"] * rarity_bonus * 100))
        weighted_ores.extend([ore_name] * weight)
    
    return random.choice(weighted_ores)

def get_active_ad():
    """Получает активную рекламу"""
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    c.execute("SELECT text, link FROM mining_ads WHERE active = 1 ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    
    conn.close()
    
    if result:
        return {"text": result[0], "link": result[1]}
    return None

def check_button_owner(call, user_id):
    """Проверяет владельца кнопки для шахты"""
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "⛏️ Это не твоя кнопка!", show_alert=True)
        return False
    return True
    
    # ================== КОМАНДА: МОЯ ШАХТА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["моя шахта", "шахта"])
def my_mine(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Получаем активную рекламу
    ad = get_active_ad()
    
    text = f"⛏️ {mention}, это твоя шахта, зарабатывай и находи много редких видов руд 💎"
    
    # Добавляем рекламу если есть
    if ad:
        text += f"\n\n📢 {ad['text']}\n{ad['link']}"
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("⛏️ Кирки", callback_data=f"mine_pickaxe_shop_{user_id}"),
        InlineKeyboardButton("🎒 Инвентарь", callback_data=f"mine_inventory_{user_id}")
    )
    kb.add(InlineKeyboardButton("👤 Профиль", callback_data=f"mine_profile_{user_id}"))
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

# ================== МАГАЗИН КИРОК ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_pickaxe_shop_"))
def pickaxe_shop(call):
    try:
        user_id = int(call.data.split("_")[3])
        if not check_button_owner(call, user_id):
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"🛒 {mention}, магазин кирок:\n\n"
        
        for pick_id, pick_data in PICKAXES.items():
            if pick_id == 1:
                text += f"⛏️ <b>{pick_data['name']}</b> (Дешёвая)\n"
            else:
                text += f"⛏️ <b>{pick_data['name']}</b> - {format_number(pick_data['price'])} izzzy\n"
            text += f"   └─ Бонус: x{pick_data['rarity_bonus']} | Прочность: {pick_data['durability']}\n\n"
        
        kb = InlineKeyboardMarkup(row_width=2)
        
        # Кнопки для покупки кирок (кроме деревянной)
        for pick_id in range(1, 8):
            pick_data = PICKAXES[pick_id]
            kb.add(InlineKeyboardButton(
                pick_data["name"], 
                callback_data=f"mine_buy_pickaxe_{user_id}_{pick_id}"
            ))
        
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"mine_back_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка магазина кирок: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== ПОКУПКА КИРКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_buy_pickaxe_"))
def buy_pickaxe(call):
    try:
        parts = call.data.split("_")
        user_id = int(parts[3])
        pickaxe_id = int(parts[4])
        
        if not check_button_owner(call, user_id):
            return
        
        if pickaxe_id not in PICKAXES:
            bot.answer_callback_query(call.id, "❌ Неверная кирка!", show_alert=True)
            return
        
        pickaxe_data = PICKAXES[pickaxe_id]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"{mention}, ты точно хочешь купить именно <b>{pickaxe_data['name']}</b>?"
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Да", callback_data=f"mine_confirm_buy_{user_id}_{pickaxe_id}"),
            InlineKeyboardButton("Нет", callback_data=f"mine_pickaxe_shop_{user_id}")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка покупки кирки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_confirm_buy_"))
def confirm_buy_pickaxe(call):
    try:
        parts = call.data.split("_")
        user_id = int(parts[3])
        pickaxe_id = int(parts[4])
        
        if not check_button_owner(call, user_id):
            return
        
        if pickaxe_id not in PICKAXES:
            bot.answer_callback_query(call.id, "❌ Неверная кирка!", show_alert=True)
            return
        
        pickaxe_data = PICKAXES[pickaxe_id]
        
        # Проверяем баланс
        user_data = get_user_data(user_id)
        
        if user_data["balance"] < pickaxe_data["price"]:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств!", show_alert=True)
            return
        
        # Списываем деньги
        user_data["balance"] -= pickaxe_data["price"]
        save_casino_data()
        
        # Обновляем кирку пользователя
        mining_user = get_mining_user(user_id)
        mining_user["pickaxe_id"] = pickaxe_id
        mining_user["pickaxe_durability"] = pickaxe_data["durability"]
        mining_user["max_durability"] = pickaxe_data["durability"]
        update_mining_user(user_id, mining_user)
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"✅ {mention}, успешная покупка кирки <b>{pickaxe_data['name']}</b>!"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ В шахту", callback_data=f"mine_back_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id, "✅ Кирка куплена!")
        
    except Exception as e:
        logger.error(f"Ошибка подтверждения покупки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
# ================== ИНВЕНТАРЬ ШАХТЫ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_inventory_"))
def mine_inventory(call):
    try:
        user_id = int(call.data.split("_")[2])
        if not check_button_owner(call, user_id):
            return
        
        mining_user = get_mining_user(user_id)
        pickaxe_data = PICKAXES[mining_user["pickaxe_id"]]
        total_ores = get_total_ores_count(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = (
            f"🎒 {mention}, это твой инвентарь в шахте:\n\n"
            f"⚡ Энергий: {mining_user['energy']}/{mining_user['max_energy']}\n"
            f"⛏️ Твоя кирка: {pickaxe_data['name']}\n"
            f"🎒 Всего найдено руд: {total_ores}"
        )
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("💱 Мои руды", callback_data=f"mine_my_ores_{user_id}"),
            InlineKeyboardButton("⬅️ Назад", callback_data=f"mine_back_{user_id}")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка инвентаря: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== МОИ РУДЫ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_my_ores_"))
def my_ores(call):
    try:
        user_id = int(call.data.split("_")[3])
        if not check_button_owner(call, user_id):
            return
        
        ores = get_user_ores(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        if not ores:
            text = f"{mention}, к сожалению ты ещё не добывал руду, начни добывать по команде: <code>копать</code> или <code>копать шахту</code>"
        else:
            text = f"{mention}, все твои руды:\n\n"
            total_value = 0
            
            for ore_name, quantity in sorted(ores.items(), key=lambda x: ORES[x[0]]["price"], reverse=True):
                ore_price = ORES[ore_name]["price"]
                ore_value = ore_price * quantity
                total_value += ore_value
                text += f"{ore_name} ×{quantity} - {format_number(ore_value)}$\n"
            
            text += f"\n💰 Общая стоимость: {format_number(total_value)} izzzy"
        
        kb = InlineKeyboardMarkup(row_width=1)

        if ores:
            kb.add(InlineKeyboardButton(" Продать все", callback_data=f"mine_sell_all_{user_id}"))
            for ore_name, quantity in ores.items():
                kb.add(
                    InlineKeyboardButton(
                        f"Продать {ore_name} ×{quantity}",
                        callback_data=f"mine_sell_ore_{user_id}_{ore_name}"
                    )
                )

        kb.add(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"mine_inventory_{user_id}"),
            InlineKeyboardButton("⛏️ В шахту", callback_data=f"mine_back_{user_id}")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка показа руд: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== ПРОДАЖА ВСЕХ РУД ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_sell_all_"))
def sell_all_ores(call):
    try:
        user_id = int(call.data.split("_")[3])
        
        if not check_button_owner(call, user_id):
            return

        ores = get_user_ores(user_id)
        if not ores:
            bot.answer_callback_query(call.id, "❌ У тебя нет руд для продажи!", show_alert=True)
            return

        # Считаем общую стоимость
        total_value = 0
        for ore_name, quantity in ores.items():
            if ore_name in ORES:
                total_value += ORES[ore_name]["price"] * quantity

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        text = (
            f"{mention}, ты точно хочешь продать ВСЕ руды?\n\n"
            f"💰 Общая стоимость: <code>{format_number(total_value)} izzzy</code>"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Дв", callback_data=f"mine_confirm_sell_all_{user_id}"),
            InlineKeyboardButton("Нет", callback_data=f"mine_my_ores_{user_id}")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка продажи всех руд: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при продаже!", show_alert=True)

# ================== ПОДТВЕРЖДЕНИЕ ПРОДАЖИ ВСЕХ РУД ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_confirm_sell_all_"))
def confirm_sell_all_ores(call):
    try:
        user_id = int(call.data.split("_")[4])
        
        if not check_button_owner(call, user_id):
            return

        ores = get_user_ores(user_id)
        if not ores:
            bot.answer_callback_query(call.id, "❌ У тебя нет руд для продажи!", show_alert=True)
            return

        # Считаем общую стоимость
        total_value = 0
        sold_items = []
        for ore_name, quantity in ores.items():
            if ore_name in ORES:
                ore_value = ORES[ore_name]["price"] * quantity
                total_value += ore_value
                sold_items.append(f"{ore_name} ×{quantity}")

        # Начисляем деньги
        user_data = get_user_data(user_id)
        user_data["balance"] += total_value
        
        # Очищаем инвентарь
        clear_user_ores(user_id)
        
        save_casino_data()

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        # Формируем список проданных руд (первые 5, если много)
        sold_list = "\n".join(sold_items[:5])
        if len(sold_items) > 5:
            sold_list += f"\n... и ещё {len(sold_items) - 5} видов руд"

        text = (
            f"✅ {mention}, ты продал ВСЕ руды!\n\n"
            f"💰 Получено: <code>{format_number(total_value)} izzzy</code>\n"
            f"📦 Баланс: <code>{format_number(user_data['balance'])} izzzy</code>\n\n"
            f"📋 Проданные руды:\n{sold_list}"
        )

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К рудам", callback_data=f"mine_my_ores_{user_id}"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id, f"+{format_number(total_value)} izzzy")

    except Exception as e:
        logger.error(f"Ошибка подтверждения продажи всех руд: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при продаже!", show_alert=True)

# ================== ПРОДАЖА ОДНОГО ТИПА РУД ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_sell_ore_"))
def sell_single_ore(call):
    try:
        parts = call.data.split("_")
        user_id = int(parts[3])
        ore_name = parts[4]
        
        if not check_button_owner(call, user_id):
            return

        ores = get_user_ores(user_id)
        if ore_name not in ores:
            bot.answer_callback_query(call.id, "❌ У тебя нет этой руды!", show_alert=True)
            return

        quantity = ores[ore_name]
        price = ORES[ore_name]["price"]
        total = price * quantity

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        text = (
            f"{mention}, ты точно хочешь продать\n"
            f"<b>{ore_name} ×{quantity}</b>\n"
            f"за <code>{format_number(total)} izzzy</code>?"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Да", callback_data=f"mine_confirm_sell_ore_{user_id}_{ore_name}"),
            InlineKeyboardButton("Нет", callback_data=f"mine_my_ores_{user_id}")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка продажи руды: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== ПОДТВЕРЖДЕНИЕ ПРОДАЖИ ОДНОГО ТИПА РУД ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_confirm_sell_ore_"))
def confirm_sell_single_ore(call):
    try:
        parts = call.data.split("_")
        user_id = int(parts[4])
        ore_name = parts[5]
        
        if not check_button_owner(call, user_id):
            return

        ores = get_user_ores(user_id)
        if ore_name not in ores:
            bot.answer_callback_query(call.id, "❌ Руда не найдена!", show_alert=True)
            return

        quantity = ores[ore_name]
        price = ORES[ore_name]["price"]
        total = price * quantity

        # Начисляем деньги
        user_data = get_user_data(user_id)
        user_data["balance"] += total
        
        # Удаляем руду из инвентаря
        add_ore_to_user(user_id, ore_name, -quantity)
        
        save_casino_data()

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        text = f"✅ {mention}, ты продал <b>{ore_name} ×{quantity}</b> за <code>{format_number(total)} izzzy</code>"

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К рудам", callback_data=f"mine_my_ores_{user_id}"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id, f"+{format_number(total)}$")

    except Exception as e:
        logger.error(f"Ошибка подтверждения продажи руды: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
        
        # ================== ПРОФИЛЬ ШАХТЫ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_profile_"))
def mine_profile(call):
    try:
        user_id = int(call.data.split("_")[2])
        if not check_button_owner(call, user_id):
            return
        
        mining_user = get_mining_user(user_id)
        pickaxe_data = PICKAXES[mining_user["pickaxe_id"]]
        total_ores = get_total_ores_count(user_id)
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = (
            f"👤 {mention}, это твой профиль для ознакомления с текущими данными:\n\n"
            f"⚡ Энергий всего: {mining_user['energy']}/{mining_user['max_energy']}\n"
            f"⛏️ Твоя кирка: {pickaxe_data['name']} | {mining_user['pickaxe_durability']}/{mining_user['max_durability']}\n"
            f"🚥 Всего руд: {total_ores}\n"
            f"💰 Текущий баланс: {format_number(user_data['balance'])} izzzy"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"mine_back_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка профиля: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КОПАНИЕ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["копать", "копать шахту"])
def mine_ore(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Проверяем, может ли пользователь копать
    can_mine_result, message_text = can_mine(user_id)
    
    if not can_mine_result:
        bot.reply_to(message, message_text, parse_mode="HTML")
        return
    
    mining_user = get_mining_user(user_id)
    
    # Проверяем наличие кирки
    if mining_user["pickaxe_id"] == 1 and PICKAXES[1]["name"] == "⛏️ Деревянная кирка":
        # У всех есть деревянная кирка по умолчанию
        pass
    
    # Получаем случайную руду
    ore_found = get_random_ore(mining_user["pickaxe_id"])
    ore_price = ORES[ore_found]["price"]
    
    # Обновляем данные пользователя
    mining_user["energy"] -= 1
    mining_user["pickaxe_durability"] -= 2
    mining_user["total_ores_mined"] += 1
    mining_user["last_mining_time"] = datetime.now().isoformat()
    
    # Проверяем, не сломалась ли кирка
    if mining_user["pickaxe_durability"] <= 0:
        mining_user["pickaxe_durability"] = 0
    
    update_mining_user(user_id, mining_user)
    
    # Добавляем руду в инвентарь
    add_ore_to_user(user_id, ore_found)
    
    # Формируем ответ
    text = (
        f"⛏️ Копая шахту ты нашёл {ore_found} ({ore_price}$), потратив 1 энергию и две силы своей кирки\n"
        f"⚡ Осталось энергии: {mining_user['energy']}/50\n"
        f"⛏️ Осталось силы кирки: {mining_user['pickaxe_durability']}/{mining_user['max_durability']}"
    )
    
    # Проверяем, не сломалась ли кирка
    if mining_user["pickaxe_durability"] <= 0:
        text += "\n\n⚠️ <b>Твоя кирка сломалась! Купи новую в магазине.</b>"
    
    bot.reply_to(message, text, parse_mode="HTML")

# ================== ВОЗВРАТ В ШАХТУ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("mine_back_"))
def mine_back(call):
    try:
        user_id = int(call.data.split("_")[2])
        if not check_button_owner(call, user_id):
            return
        
        # Создаем фейковое сообщение
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = from_user
        
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        my_mine(fake_msg)
        
        # Удаляем старое сообщение
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка возврата в шахту: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== АДМИН КОМАНДА: +РЕКЛАМА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "+реклама")
def add_advertisement(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Эта команда только для администраторов!")
        return
    
    bot.reply_to(message, "📢 Отправьте текст рекламы:")
    bot.register_next_step_handler(message, process_ad_text)

def process_ad_text(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    ad_text = message.text
    
    bot.reply_to(message, "🔗 Теперь отправьте ссылку для рекламы (Telegram чат/канал):")
    bot.register_next_step_handler(message, process_ad_link, ad_text)

def process_ad_link(message, ad_text):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    ad_link = message.text
    
    # Сохраняем рекламу в базу
    conn = sqlite3.connect(MINING_DB)
    c = conn.cursor()
    
    # Деактивируем старую рекламу
    c.execute("UPDATE mining_ads SET active = 0 WHERE active = 1")
    
    # Добавляем новую рекламу
    c.execute("INSERT INTO mining_ads (text, link, active, created_at) VALUES (?, ?, 1, ?)",
              (ad_text, ad_link, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    bot.reply_to(message, "✅ Реклама занесена в профиль шахты всем участникам бота")

print("✅ Система шахты загружена и готова к работе! ⛏️")

PREFIX_DB = "prefixes.db"

# ======================================================
# УЛУЧШЕННАЯ СИСТЕМА ПРЕФИКСОВ (БЕЗОПАСНАЯ ДЛЯ СУЩЕСТВУЮЩЕЙ БАЗЫ)
# ======================================================

def init_prefix_db():
    """Инициализация базы с защитой от ошибок при миграции"""
    conn = sqlite3.connect(PREFIX_DB, check_same_thread=False)
    c = conn.cursor()
    
    try:
        # Создаем таблицу префиксов если не существует
        c.execute("""
        CREATE TABLE IF NOT EXISTS prefixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price INTEGER NOT NULL
        )
        """)
        
        # Создаем таблицу префиксов пользователей если не существует
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_prefixes (
            user_id INTEGER PRIMARY KEY,
            prefix_id INTEGER NOT NULL,
            price_paid INTEGER NOT NULL,
            FOREIGN KEY (prefix_id) REFERENCES prefixes(id)
        )
        """)
        
        conn.commit()
        
        # Проверяем наличие префиксов
        c.execute("SELECT COUNT(*) FROM prefixes")
        count = c.fetchone()[0]
        
        if count == 0:
            # Обновленный список префиксов с новыми ценами
            default_prefixes = [
                ("🔰 Новичок", 500000),        # 500к
                ("🔥 Огонь", 1500000),         # 1.5M
                ("⚡ Молния", 3000000),        # 3M (новый)
                ("🌟 Звезда", 5000000),        # 5M (новый)
                ("👑 Король", 10000000),       # 10M
                ("💎 Алмаз", 25000000),        # 25M
                ("🐲 Дракон", 50000000),       # 50M
                ("🌙 Луна", 75000000),         # 75M (новый)
                ("☀️ Солнце", 100000000),      # 100M (новый)
                ("✨ Божественный", 250000000), # 250M (новый)
            ]
            c.executemany("INSERT INTO prefixes (name, price) VALUES (?, ?)", default_prefixes)
            conn.commit()
            logger.info(f"✅ Создано {len(default_prefixes)} префиксов по умолчанию")
        else:
            logger.info(f"✅ В базе уже есть {count} префиксов")
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы префиксов: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_all_prefixes():
    """Получить все префиксы"""
    try:
        conn = sqlite3.connect(PREFIX_DB)
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM prefixes ORDER BY price ASC")
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка префиксов: {e}")
        return []


def get_prefix(prefix_id):
    """Получить префикс по ID"""
    try:
        conn = sqlite3.connect(PREFIX_DB)
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM prefixes WHERE id = ?", (prefix_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "name": row[1], "price": row[2]}
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка получения префикса {prefix_id}: {e}")
        return None


def get_user_prefix(user_id):
    """Безопасное получение префикса пользователя (без ошибок если нет данных)"""
    try:
        conn = sqlite3.connect(PREFIX_DB)
        c = conn.cursor()
        
        # Проверяем существование таблицы
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_prefixes'")
        if not c.fetchone():
            conn.close()
            return None
            
        c.execute("""
            SELECT p.id, p.name, p.price, up.price_paid
            FROM user_prefixes up
            JOIN prefixes p ON p.id = up.prefix_id
            WHERE up.user_id = ?
        """, (user_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        return {"id": row[0], "name": row[1], "price": row[2], "price_paid": row[3]}
        
    except sqlite3.OperationalError as e:
        # Таблица не существует или другая SQL ошибка
        logger.warning(f"⚠️ Таблица префиксов не найдена для пользователя {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка получения префикса пользователя {user_id}: {e}")
        return None


def set_user_prefix(user_id, prefix_id, price_paid):
    """Установить префикс пользователю (безопасно)"""
    try:
        conn = sqlite3.connect(PREFIX_DB)
        c = conn.cursor()
        
        # Проверяем существование таблицы
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_prefixes'")
        if not c.fetchone():
            # Создаем таблицу если не существует
            c.execute("""
                CREATE TABLE IF NOT EXISTS user_prefixes (
                    user_id INTEGER PRIMARY KEY,
                    prefix_id INTEGER NOT NULL,
                    price_paid INTEGER NOT NULL,
                    FOREIGN KEY (prefix_id) REFERENCES prefixes(id)
                )
            """)
        
        c.execute("INSERT OR REPLACE INTO user_prefixes (user_id, prefix_id, price_paid) VALUES (?, ?, ?)",
                  (user_id, prefix_id, price_paid))
        conn.commit()
        logger.info(f"✅ Установлен префикс {prefix_id} для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка установки префикса для {user_id}: {e}")
        conn.rollback()
    finally:
        conn.close()


def remove_user_prefix(user_id):
    """Удалить префикс пользователя (безопасно)"""
    try:
        conn = sqlite3.connect(PREFIX_DB)
        c = conn.cursor()
        
        # Проверяем существование таблицы
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_prefixes'")
        if not c.fetchone():
            conn.close()
            return
            
        c.execute("DELETE FROM user_prefixes WHERE user_id = ?", (user_id,))
        conn.commit()
        logger.info(f"✅ Удален префикс пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления префикса у {user_id}: {e}")
    finally:
        conn.close()


# Инициализируем базу при старте
init_prefix_db()

print("✅ Улучшенная система префиксов загружена и готова к работе")



# ================== КОМАНДА ДЛЯ УДАЛЕНИЯ СООБЩЕНИЙ (ТОЛЬКО ДЛЯ АДМИНОВ) ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "-смс")
def delete_message_cmd(message):
    """Удаляет сообщение, на которое ответили (только для администраторов)"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем права администратора в боте
        is_bot_admin = user_id in ADMIN_IDS
        
        # Проверяем права администратора в чате (для групповых чатов)
        is_chat_admin = False
        if message.chat.type in ["group", "supergroup"]:
            try:
                member = bot.get_chat_member(chat_id, user_id)
                is_chat_admin = member.status in ["administrator", "creator"]
            except:
                pass
        
        # Если не администратор ни в боте, ни в чате - игнорируем
        if not (is_bot_admin or is_chat_admin):
            # Отправляем сообщение и удаляем его через 5 секунд
            warning = bot.send_message(chat_id, 
                                     "❌ Эта команда доступна только администраторам!", 
                                     parse_mode="HTML")
            time.sleep(5)
            try:
                bot.delete_message(chat_id, warning.message_id)
                bot.delete_message(chat_id, message.message_id)
            except:
                pass
            return
        
        # Проверяем, что команда отправлена в ответ на сообщение
        if not message.reply_to_message:
            # Отправляем подсказку и удаляем через 5 секунд
            hint = bot.send_message(chat_id, 
                                   "❌ Ответьте на сообщение, которое нужно удалить!\n\n"
                                   "<b>Использование:</b> Ответьте на сообщение и напишите <code>-смс</code>", 
                                   parse_mode="HTML")
            time.sleep(5)
            try:
                bot.delete_message(chat_id, hint.message_id)
                bot.delete_message(chat_id, message.message_id)
            except:
                pass
            return
        
        # Удаляем целевое сообщение
        try:
            bot.delete_message(chat_id, message.reply_to_message.message_id)
        except Exception as e:
            error_msg = bot.send_message(chat_id, 
                                       f"❌ Не удалось удалить сообщение!", 
                                       parse_mode="HTML")
            time.sleep(5)
            try:
                bot.delete_message(chat_id, error_msg.message_id)
                bot.delete_message(chat_id, message.message_id)
            except:
                pass
            return
        
        # Удаляем команду
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        
        # Отправляем подтверждение (автоматически удалится через 2 секунды)
        confirm_msg = bot.send_message(chat_id, 
                                      "✅ Сообщение удалено!", 
                                      parse_mode="HTML")
        
        # Автоматически удаляем подтверждение через 2 секунды
        time.sleep(1)
        try:
            bot.delete_message(chat_id, confirm_msg.message_id)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Ошибка в команде -смс: {e}")
        try:
            bot.send_message(chat_id, 
                           "❌ Произошла ошибка!", 
                           parse_mode="HTML")
        except:
            pass
        
     # ================== ОБНОВЛЁННАЯ ПАНЕЛЬ РАССЫЛКИ С АВТОМАТИЧЕСКИМ СОХРАНЕНИЕМ ЧАТОВ ==================

BROADCAST_FILE = "broadcast_chats.json"
_broadcast_states = {}

def load_broadcast_chats():
    try:
        if os.path.exists(BROADCAST_FILE):
            with open(BROADCAST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        return []
    except Exception as e:
        logger.error(f"Ошибка загрузки чатов рассылки: {e}")
        return []

def save_broadcast_chats(chats):
    try:
        with open(BROADCAST_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения чатов рассылки: {e}")
        return False

def add_chat_to_broadcast(chat_id):
    """Автоматически добавляет чат в базу для рассылки"""
    try:
        chats = load_broadcast_chats()
        if chat_id not in chats:
            chats.append(chat_id)
            save_broadcast_chats(chats)
            logger.info(f"✅ Чат {chat_id} автоматически добавлен в рассылку")
    except Exception as e:
        logger.error(f"Ошибка автоматического добавления чата: {e}")

# ==========================
#   ДНЕВНОЙ БОНУС
# ==========================
DAILY_BONUS_AMOUNT = 3500

def can_take_daily_bonus(user_id):
    data = get_user_data(user_id)
    today = date.today().isoformat()
    return data.get("daily_bonus_claimed") != today

def give_daily_bonus(user_id):
    data = get_user_data(user_id)
    data["balance"] += DAILY_BONUS_AMOUNT
    data["daily_bonus_claimed"] = date.today().isoformat()
    save_casino_data()

# ======================================================
# 🎁 АВТО-ВЫДАЧА БОНУСА ПО ССЫЛКЕ: /start bonus
# ======================================================
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start bonus"))
def start_bonus(message):
    user_id = message.from_user.id

    if not can_take_daily_bonus(user_id):
        bot.send_message(
            message.chat.id,
            "❌ <b>Вы уже получили бонус сегодня!</b>",
            parse_mode="HTML"
        )
        return

    give_daily_bonus(user_id)
    
    user_data = get_user_data(user_id)
    
    bot.send_message(
        message.chat.id,
        f"🎁 <b>Бонус автоматически выдан!</b>\n💸 +{DAILY_BONUS_AMOUNT}$\n\n💰 <b>Текущий баланс:</b> <code>{format_number(user_data['balance'])}$</code>",
        parse_mode="HTML"
    )





# ======================================================
# ======================================================
#    ПОЛНАЯ КОМАНДА: б / баланс
# ======================================================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["б", "баланс"])
def balance_cmd(message):
    # ❗ Авто-добавление чата в рассылку
    add_chat_to_broadcast(message.chat.id)

    user_id = message.from_user.id
    user = bot.get_chat(user_id)
    data = get_user_data(user_id)

    # Префикс
    prefix_data = get_user_prefix(user_id)
    prefix_display = prefix_data["name"] if prefix_data else "Нет"

    # VIP статус
    vip_data = data.get("vip", {})
    vip_level = vip_data.get("level", 0)
    if vip_level > 0:
        vip_info = VIP_LEVELS.get(vip_level, {})
        vip_display = f"{vip_info.get('prefix', '⭐')} {vip_info.get('name', 'VIP')}"
    else:
        vip_display = "Нет"

    # Имя + префикс
    clickable = f"<a href='tg://user?id={user_id}'>{user.first_name}</a>"
    if prefix_data:
        prefix_emoji = (
            prefix_data["name"].split()[0]
            if " " in prefix_data["name"]
            else prefix_data["name"]
        )
        clickable = f"{prefix_emoji} {clickable}"

    # Текст
    text = (
        f"👤 <b>Имя:</b> {clickable}\n"
        f"💰 <b>Баланс:</b> <code>{format_number(data['balance'])} izzzy</code>\n"
        f"💎 <b>VIP:</b> {vip_display}"
    )

    # Кнопки
    kb = types.InlineKeyboardMarkup()

    if prefix_data:
        kb.row(
            types.InlineKeyboardButton(
                "💸 Продать префикс",
                callback_data=f"sell_prefix_{user_id}"
            )
        )
    else:
        kb.row(
            types.InlineKeyboardButton(
                "🛒 Купить префикс",
                callback_data=f"buy_prefix_menu_{user_id}"
            )
        )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=kb
    )

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "панель рассылки")
def broadcast_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ У тебя нет прав администратора.")
        return

    chats = load_broadcast_chats()
    total_chats = len(chats)
    
    # Быстрая проверка - только количество доступных
    active_chats = 0
    for chat_id in chats:
        try:
            bot.get_chat(chat_id)
            active_chats += 1
        except:
            pass
    
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("➕ Добавить чат", callback_data="broadcast_add_chat"),
        types.InlineKeyboardButton("🗑 Удалить чат", callback_data="broadcast_remove_chat")
    )
    kb.add(
        types.InlineKeyboardButton("📢 Сделать рассылку", callback_data="broadcast_send"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="broadcast_refresh")
    )

    bot.send_message(
        message.chat.id,
        f"🛠 <b>Панель рассылки</b>\n\n"
        f"📊 Статистика:\n"
        f"• Чатов в базе: <b>{total_chats}</b>\n"
        f"• Активных: <b>{active_chats}</b>\n"
        f"• Мёртвых: <b>{total_chats - active_chats}</b>\n\n"
        f"Выбери действие:",
        reply_markup=kb,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_stats")
def broadcast_stats(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    
    chats = load_broadcast_chats()
    total_chats = len(chats)
    active_chats = 0
    
    for chat_id in chats:
        try:
            bot.get_chat(chat_id)
            active_chats += 1
        except:
            pass
    
    text = (
        f"📊 <b>Статистика рассылки</b>\n\n"
        f"• Чатов в базе: <b>{total_chats}</b>\n"
        f"• Активных: <b>{active_chats}</b>\n"
        f"• Мёртвых: <b>{total_chats - active_chats}</b>\n\n"
        f"<i>Активные - где бот есть в чате</i>"
    )
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="broadcast_back"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_list_chats")
def broadcast_list_chats(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    
    chats = load_broadcast_chats()
    if not chats:
        bot.answer_callback_query(call.id, "❌ Список чатов пуст!")
        return
    
    # Показываем просто список ID
    text = f"📋 <b>Чаты для рассылки: {len(chats)} шт</b>\n\n"
    
    # Разбиваем на колонки для компактности
    cols = 3
    for i in range(0, len(chats), cols):
        row_chats = chats[i:i+cols]
        row_text = " | ".join(f"<code>{cid}</code>" for cid in row_chats)
        text += f"{row_text}\n"
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🗑 Удалить чат", callback_data="broadcast_remove_chat"))
    kb.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="broadcast_list_chats"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="broadcast_back"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_remove_chat")
def broadcast_remove_chat(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    chats = load_broadcast_chats()
    if not chats:
        bot.send_message(call.message.chat.id, "❌ Список чатов пуст!")
        # Создаем фейковое сообщение для возврата в панель
        class FakeMessage:
            def __init__(self, chat, from_user):
                self.chat = chat
                self.from_user = from_user
        fake_msg = FakeMessage(call.message.chat, call.from_user)
        broadcast_panel(fake_msg)
        return

    text = "🗑 <b>Удаление чата из рассылки</b>\n\nВыбери ID чата для удаления:\n\n"
    for i, chat_id in enumerate(chats, 1):
        try:
            chat = bot.get_chat(chat_id)
            members = bot.get_chat_members_count(chat_id)
            title = chat.title or "Без названия"
            text += f"{i}. <code>{chat_id}</code> - {title} ({members} участ.)\n"
        except:
            text += f"{i}. <code>{chat_id}</code> - ⚠️ Недоступен\n"
    text += "\nОтправь ID чата для удаления:"
    msg = bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_broadcast_remove_chat)


def process_broadcast_remove_chat(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not message.text:
        bot.send_message(message.chat.id, "❌ Нужно отправить ID чата!")
        # Создаем фейковое сообщение для возврата в панель
        class FakeMessage:
            def __init__(self, chat, from_user):
                self.chat = chat
                self.from_user = from_user
        fake_msg = FakeMessage(message.chat, message.from_user)
        broadcast_panel(fake_msg)
        return
    
    try:
        chat_id = int(message.text.strip())
        chats = load_broadcast_chats()
        if chat_id not in chats:
            bot.send_message(message.chat.id, f"❌ Чат <code>{chat_id}</code> не найден!", parse_mode="HTML")
            class FakeMessage:
                def __init__(self, chat, from_user):
                    self.chat = chat
                    self.from_user = from_user
            fake_msg = FakeMessage(message.chat, message.from_user)
            broadcast_panel(fake_msg)
            return
        
        chats.remove(chat_id)
        if save_broadcast_chats(chats):
            bot.send_message(message.chat.id, f"✅ Чат <code>{chat_id}</code> удалён из рассылки!", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Ошибка сохранения в файл!")
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ID! Отправь только цифры.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")
    
    # Возвращаемся в панель рассылки
    class FakeMessage:
        def __init__(self, chat, from_user):
            self.chat = chat
            self.from_user = from_user
    fake_msg = FakeMessage(message.chat, message.from_user)
    broadcast_panel(fake_msg)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_list_chats")
def broadcast_list_chats(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    chats = load_broadcast_chats()
    if not chats:
        bot.answer_callback_query(call.id, "❌ Список чатов пуст!")
        return
    text = "📋 <b>Список чатов для рассылки:</b>\n\n"
    total_members = 0
    active_chats = 0
    for i, chat_id in enumerate(chats, 1):
        try:
            chat = bot.get_chat(chat_id)
            members = bot.get_chat_members_count(chat_id)
            title = chat.title or "Без названия"
            username = f"@{chat.username}" if getattr(chat, "username", None) else "Нет"
            text += f"<b>{i}. {title}</b>\n   🆔: <code>{chat_id}</code>\n   👥: {members} участников\n   📎: {username}\n\n"
            total_members += members
            active_chats += 1
        except:
            text += f"<b>{i}. ⚠️ Недоступен</b>\n   🆔: <code>{chat_id}</code>\n   ❌ Бот не в чате или нет прав\n\n"
    text += f"<b>Итого:</b>\n• Всего в базе: {len(chats)} чатов\n• Активных: {active_chats} чатов\n• Недоступных: {len(chats) - active_chats} чатов\n• Общая аудитория: ~{total_members} участников"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🗑 Удалить чат", callback_data="broadcast_remove_chat"))
    kb.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="broadcast_list_chats"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="broadcast_back"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

def _store_broadcast_content_from_message(msg):
    """Сохраняет контент с правильным разделением entities"""
    
    if msg.text:
        return {
            "type": "text",
            "text": msg.text,
            "entities": msg.entities  # Только для текста
        }
    
    if getattr(msg, "photo", None):
        return {
            "type": "photo",
            "file_id": msg.photo[-1].file_id,
            "caption": msg.caption or "",
            "caption_entities": msg.caption_entities  # Только для подписи
        }
    
    if getattr(msg, "video", None):
        return {
            "type": "video",
            "file_id": msg.video.file_id,
            "caption": msg.caption or "",
            "caption_entities": msg.caption_entities  # Только для подписи
        }
    
    if getattr(msg, "animation", None):
        return {
            "type": "animation",
            "file_id": msg.animation.file_id,
            "caption": msg.caption or "",
            "caption_entities": msg.caption_entities  # Только для подписи
        }
    
    return {"type": "unknown"}


@bot.callback_query_handler(func=lambda c: c.data == "broadcast_send")
def broadcast_send(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    
    chats = load_broadcast_chats()
    if not chats:
        bot.answer_callback_query(call.id, "❌ Список чатов пуст!")
        return
    
    active_chats = 0
    for chat_id in chats:
        try:
            bot.get_chat(chat_id)
            active_chats += 1
        except:
            pass
    
    if active_chats == 0:
        bot.answer_callback_query(call.id, "❌ Нет доступных чатов!")
        return
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    msg = bot.send_message(
        call.message.chat.id,
        f"📢 <b>Создание рассылки</b>\n\nБудет отправлено в: <b>{active_chats}</b> чатов\n\n"
        f"Отправь сообщение для рассылки (текст / фото / видео / гиф / с подписью):",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, process_broadcast_send)


def process_broadcast_send(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    admin_id = message.from_user.id

    # Сохраняем контент с правильными полями
    content = _store_broadcast_content_from_message(message)

    # Инициализируем состояние рассылки
    _broadcast_states[admin_id] = {
        "content": content,
        "pin": False,
        "inline_buttons": []
    }

    # Клавиатура управления
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("➕ Добавить инлайн кнопку", callback_data="broadcast_add_inline"))
    kb.add(types.InlineKeyboardButton("📌 Закрепить: ❌", callback_data="broadcast_toggle_pin"))
    kb.add(types.InlineKeyboardButton("👁 Просмотр", callback_data="broadcast_preview"))
    kb.add(types.InlineKeyboardButton("✅ Начать рассылку", callback_data="broadcast_confirm"))
    kb.add(types.InlineKeyboardButton("📊 Статистика", callback_data="broadcast_stats"))
    kb.add(types.InlineKeyboardButton("❌ Отменить", callback_data="broadcast_back"))

    # Подсчет активных чатов
    chats = load_broadcast_chats()
    active_chats = []
    for chat_id in chats:
        try:
            bot.get_chat(chat_id)
            active_chats.append(chat_id)
        except:
            pass

    # Информация о кнопках
    buttons_text = ""
    state = _broadcast_states[admin_id]
    if state["inline_buttons"]:
        buttons_text = f"\n📎 Кнопок: {len(state['inline_buttons'])}"
        for i, btn in enumerate(state["inline_buttons"], 1):
            buttons_text += f"\n{i}. {btn['text']} -> {btn['url']}"

    # Превью информация
    preview_info = (
        f"📋 <b>Превью рассылки</b>\n\n"
        f"📤 Будет отправлено в: <b>{len(active_chats)}</b> чатов\n"
        f"📌 Закрепить: <b>{'Да' if state['pin'] else 'Нет'}</b>"
        f"{buttons_text}\n\n"
        f"Нажми «Просмотр» чтобы увидеть сообщение или «Начать рассылку» для отправки."
    )

    bot.send_message(
        message.chat.id,
        preview_info,
        parse_mode="HTML",  # Это служебное сообщение — здесь HTML нужен
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_add_inline")
def broadcast_add_inline(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    admin_id = call.from_user.id
    state = _broadcast_states.get(admin_id)
    if not state:
        bot.answer_callback_query(call.id, "❌ Сначала отправь содержимое для рассылки.")
        return
    
    # Показываем меню управления кнопками
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Добавить новую кнопку", callback_data="broadcast_add_new_button"))
    if state["inline_buttons"]:
        kb.add(types.InlineKeyboardButton("🗑 Удалить кнопку", callback_data="broadcast_remove_button"))
        kb.add(types.InlineKeyboardButton("📋 Список кнопок", callback_data="broadcast_list_buttons"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="broadcast_back_to_preview"))
    
    text = "🔘 <b>Управление инлайн кнопками</b>\n\n"
    if state["inline_buttons"]:
        text += f"📎 Всего кнопок: {len(state['inline_buttons'])}\n"
        text += "Вы можете добавлять неограниченное количество кнопок!"
    else:
        text += "Пока нет кнопок. Добавьте первую!"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_add_new_button")
def broadcast_add_new_button(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    
    bot.send_message(call.message.chat.id, "✏️ Отправь название для инлайн-кнопки:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_inline_text_step, call.from_user.id)

def process_inline_text_step(message, admin_id):
    if message.from_user.id not in ADMIN_IDS:
        return
    admin = message.from_user.id
    if admin != admin_id:
        bot.send_message(message.chat.id, "❌ Это не тот админ.")
        return
    state = _broadcast_states.get(admin)
    if not state:
        bot.send_message(message.chat.id, "❌ Нет состояния рассылки.")
        return
    btn_text = message.text.strip()
    if not btn_text:
        bot.send_message(message.chat.id, "❌ Название не может быть пустым. Отправь ещё раз.")
        bot.register_next_step_handler(message, lambda m: process_inline_text_step(m, admin_id))
        return
    
    # Сохраняем текст и просим URL
    state.setdefault("_tmp", {})["btn_text"] = btn_text
    bot.send_message(message.chat.id, "🔗 Теперь отправь ссылку (URL) для этой кнопки:")
    bot.register_next_step_handler(message, lambda m: process_inline_url_step(m, admin_id))

def process_inline_url_step(message, admin_id):
    if message.from_user.id not in ADMIN_IDS:
        return
    admin = message.from_user.id
    if admin != admin_id:
        bot.send_message(message.chat.id, "❌ Это не тот админ.")
        return
    state = _broadcast_states.get(admin)
    if not state or "_tmp" not in state or "btn_text" not in state["_tmp"]:
        bot.send_message(message.chat.id, "❌ Неожиданная ошибка — попробуйте снова.")
        return
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://") or url.startswith("mailto:")):
        bot.send_message(message.chat.id, "❌ Ссылка должна начинаться с http:// или https:// или tg:// или mailto:. Отправь снова.")
        bot.register_next_step_handler(message, lambda m: process_inline_url_step(m, admin_id))
        return
    
    btn_text = state["_tmp"].pop("btn_text")
    # Добавляем кнопку в список
    state["inline_buttons"].append({"text": btn_text, "url": url})
    
    # Показываем обновленный превью
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("➕ Добавить инлайн кнопку", callback_data="broadcast_add_inline"))
    kb.add(types.InlineKeyboardButton("📌 Закрепить: ❌", callback_data="broadcast_toggle_pin"))
    kb.add(types.InlineKeyboardButton("👁 Просмотр", callback_data="broadcast_preview"))
    kb.add(types.InlineKeyboardButton("✅ Начать рассылку", callback_data="broadcast_confirm"))
    kb.add(types.InlineKeyboardButton("📊 Статистика", callback_data="broadcast_stats"))
    kb.add(types.InlineKeyboardButton("❌ Отменить", callback_data="broadcast_back"))

    chats = load_broadcast_chats()
    active_chats = []
    for chat_id in chats:
        try:
            bot.get_chat(chat_id)
            active_chats.append(chat_id)
        except:
            pass

    buttons_text = ""
    if state["inline_buttons"]:
        buttons_text = f"\n📎 Кнопок: {len(state['inline_buttons'])}"
        for i, btn in enumerate(state["inline_buttons"], 1):
            buttons_text += f"\n{i}. {btn['text']} -> {btn['url']}"

    preview_info = (
        f"📋 <b>Превью рассылки</b>\n\n"
        f"📤 Будет отправлено в: <b>{len(active_chats)}</b> чатов\n"
        f"📌 Закрепить: <b>{'Да' if state['pin'] else 'Нет'}</b>"
        f"{buttons_text}\n\n"
        f"✅ Кнопка <b>'{btn_text}'</b> добавлена!\n\n"
        f"Нажми «Просмотр» чтобы увидеть сообщение или «Начать рассылку» для отправки."
    )

    bot.send_message(message.chat.id, preview_info, parse_mode="HTML", reply_markup=kb)
    state.pop("_tmp", None)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_list_buttons")
def broadcast_list_buttons(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    admin_id = call.from_user.id
    state = _broadcast_states.get(admin_id)
    if not state or not state["inline_buttons"]:
        bot.answer_callback_query(call.id, "❌ Нет кнопок для показа!")
        return
    
    text = "📋 <b>Список инлайн кнопок:</b>\n\n"
    for i, btn in enumerate(state["inline_buttons"], 1):
        text += f"{i}. <b>{btn['text']}</b>\n   🔗 {btn['url']}\n\n"
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Добавить ещё", callback_data="broadcast_add_new_button"))
    kb.add(types.InlineKeyboardButton("🗑 Удалить кнопку", callback_data="broadcast_remove_button"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="broadcast_add_inline"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_remove_button")
def broadcast_remove_button(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    admin_id = call.from_user.id
    state = _broadcast_states.get(admin_id)
    if not state or not state["inline_buttons"]:
        bot.answer_callback_query(call.id, "❌ Нет кнопок для удаления!")
        return
    
    text = "🗑 <b>Удаление кнопки</b>\n\nВыбери номер кнопки для удаления:\n\n"
    for i, btn in enumerate(state["inline_buttons"], 1):
        text += f"{i}. <b>{btn['text']}</b>\n"
    
    text += "\nОтправь номер кнопки для удаления:"
    
    msg = bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_remove_button_step, admin_id)

def process_remove_button_step(message, admin_id):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not message.text:
        bot.send_message(message.chat.id, "❌ Нужно отправить номер кнопки!")
        return
    
    try:
        btn_num = int(message.text.strip())
        state = _broadcast_states.get(admin_id)
        if not state or not state["inline_buttons"]:
            bot.send_message(message.chat.id, "❌ Нет кнопок для удаления!")
            return
        
        if btn_num < 1 or btn_num > len(state["inline_buttons"]):
            bot.send_message(message.chat.id, f"❌ Неверный номер! Должен быть от 1 до {len(state['inline_buttons'])}")
            return
        
        removed_btn = state["inline_buttons"].pop(btn_num - 1)
        bot.send_message(message.chat.id, f"✅ Кнопка <b>'{removed_btn['text']}'</b> удалена!", parse_mode="HTML")
        
        # Возвращаем к превью
        fake_msg = _FakeMessage(message.chat.id, message.from_user)
        process_broadcast_send(fake_msg)
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат! Отправь только номер.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_back_to_preview")
def broadcast_back_to_preview(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    
    fake_msg = _FakeMessage(call.message.chat.id, call.from_user)
    process_broadcast_send(fake_msg)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_preview")
def broadcast_preview(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return

    admin_id = call.from_user.id
    state = _broadcast_states.get(admin_id)
    if not state:
        bot.answer_callback_query(call.id, "❌ Нет подготовленной рассылки.")
        return

    content = state["content"]
    entities = content.get("entities", [])

    # Клавиатура
    rm = None
    if state["inline_buttons"]:
        kb = types.InlineKeyboardMarkup()
        for btn in state["inline_buttons"]:
            kb.add(types.InlineKeyboardButton(btn["text"], url=btn["url"]))
        rm = kb

    # 🔹 ТЕКСТ
    if content["type"] == "text":
        bot.send_message(call.message.chat.id, "📥 Превью текста:")

        if entities:
            bot.send_message(
                call.message.chat.id,
                content["text"],
                entities=entities,
                reply_markup=rm
            )
        else:
            bot.send_message(
                call.message.chat.id,
                content["text"],
                reply_markup=rm
            )

    # 🔹 ФОТО
    elif content["type"] == "photo":
        bot.send_message(call.message.chat.id, "📷 Превью фото:")

        bot.send_photo(
            call.message.chat.id,
            content["file_id"],
            caption=content.get("caption", "") or "",
            caption_entities=entities if entities else None,
            reply_markup=rm
        )

    # 🔹 ВИДЕО
    elif content["type"] == "video":
        bot.send_message(call.message.chat.id, "📹 Превью видео:")

        bot.send_video(
            call.message.chat.id,
            content["file_id"],
            caption=content.get("caption", "") or "",
            caption_entities=entities if entities else None,
            reply_markup=rm
        )

    # 🔹 ГИФ
    elif content["type"] == "animation":
        bot.send_message(call.message.chat.id, "🔁 Превью гифки:")

        bot.send_animation(
            call.message.chat.id,
            content["file_id"],
            caption=content.get("caption", "") or "",
            caption_entities=entities if entities else None,
            reply_markup=rm
        )

    else:
        bot.send_message(call.message.chat.id, "❌ Невозможно показать этот тип сообщения.")

    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_toggle_pin")
def broadcast_toggle_pin(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    admin_id = call.from_user.id
    state = _broadcast_states.get(admin_id)
    if not state:
        bot.answer_callback_query(call.id, "❌ Нет подготовленной рассылки.")
        return
    state["pin"] = not state["pin"]
    
    fake_msg = _FakeMessage(call.message.chat.id, call.from_user)
    process_broadcast_send(fake_msg)
    
    bot.answer_callback_query(call.id, f"Закрепление: {'включено' if state['pin'] else 'выключено'}")

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_confirm")
def broadcast_confirm(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return

    admin_id = call.from_user.id
    state = _broadcast_states.get(admin_id)
    if not state:
        bot.answer_callback_query(call.id, "❌ Нет подготовленной рассылки.")
        return

    chats = load_broadcast_chats()
    active_chats = []

    for chat_id in chats:
        try:
            bot.get_chat(chat_id)
            active_chats.append(chat_id)
        except:
            pass

    if not active_chats:
        bot.send_message(call.message.chat.id, "❌ Нет доступных чатов для рассылки!")
        # Создаем фейковое сообщение для возврата в панель
        class FakeMessage:
            def __init__(self, chat, from_user):
                self.chat = chat
                self.from_user = from_user
        fake_msg = FakeMessage(call.message.chat, call.from_user)
        broadcast_panel(fake_msg)
        return

    content = state["content"]
    pin = state["pin"]
    inline_buttons = state.get("inline_buttons", [])

    text_entities = content.get("entities")
    caption_entities = content.get("caption_entities")

    rm = None
    if inline_buttons:
        kb = types.InlineKeyboardMarkup()
        for btn in inline_buttons:
            kb.add(types.InlineKeyboardButton(btn["text"], url=btn["url"]))
        rm = kb

    total = len(active_chats)
    sent = 0
    failed = 0

    progress_msg = bot.send_message(
        call.message.chat.id,
        f"📤 Начинаю рассылку...\n\n⏳ Прогресс: 0/{total}\n✅ Успешно: 0\n❌ Ошибок: 0"
    )

    for i, chat_id in enumerate(active_chats, 1):
        try:
            if content["type"] == "text":
                sent_msg = bot.send_message(
                    chat_id,
                    content["text"],
                    entities=text_entities,
                    reply_markup=rm
                )

            elif content["type"] == "photo":
                sent_msg = bot.send_photo(
                    chat_id,
                    content["file_id"],
                    caption=content.get("caption"),
                    caption_entities=caption_entities,
                    reply_markup=rm
                )

            elif content["type"] == "video":
                sent_msg = bot.send_video(
                    chat_id,
                    content["file_id"],
                    caption=content.get("caption"),
                    caption_entities=caption_entities,
                    reply_markup=rm
                )

            elif content["type"] == "animation":
                sent_msg = bot.send_animation(
                    chat_id,
                    content["file_id"],
                    caption=content.get("caption"),
                    caption_entities=caption_entities,
                    reply_markup=rm
                )

            else:
                sent_msg = bot.send_message(
                    chat_id,
                    "📢 Сообщение от администрации.",
                    reply_markup=rm
                )

            sent += 1

            if pin and sent_msg and getattr(sent_msg, "message_id", None):
                try:
                    bot.pin_chat_message(chat_id, sent_msg.message_id, disable_notification=True)
                except:
                    pass

        except Exception as e:
            failed += 1
            logger.error(f"Ошибка рассылки в {chat_id}: {e}")

        if i % 5 == 0 or i == total:
            try:
                bot.edit_message_text(
                    f"📤 Рассылка в процессе...\n\n⏳ Прогресс: {i}/{total}\n✅ Успешно: {sent}\n❌ Ошибок: {failed}",
                    call.message.chat.id,
                    progress_msg.message_id
                )
            except:
                pass

        time.sleep(0.3)

    eff = round((sent/total)*100, 1) if total else 0

    bot.edit_message_text(
        f"🎉 Рассылка завершена!\n\n📊 Результаты:\n• Всего чатов: {total}\n• ✅ Успешно: {sent}\n• ❌ Ошибок: {failed}\n• 📈 Эффективность: {eff}%",
        call.message.chat.id,
        progress_msg.message_id
    )

    _broadcast_states.pop(admin_id, None)
    
    # Создаем фейковое сообщение для возврата в панель
    class FakeMessage:
        def __init__(self, chat, from_user):
            self.chat = chat
            self.from_user = from_user

    fake_msg = FakeMessage(call.message.chat, call.from_user)
    broadcast_panel(fake_msg)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_back")
def broadcast_back(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    fake = _make_fake_message_from_call(call)
    broadcast_panel(fake)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_refresh")
def broadcast_refresh(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return
    fake = _make_fake_message_from_call(call)
    broadcast_panel(fake)

# ------------------ КОНЕЦ: Обновлённая панель рассылки ------------------

def _store_broadcast_content_from_message(msg):
    # Текстовое форматирование (для обычных сообщений)
    text_entities = msg.entities
    # Форматирование подписи (для фото/видео/гифок)
    caption_entities = msg.caption_entities
    
    if msg.text:
        return {
            "type": "text",
            "text": msg.text,
            "entities": text_entities  # ← для текста
        }
    
    if getattr(msg, "photo", None):
        return {
            "type": "photo",
            "file_id": msg.photo[-1].file_id,
            "caption": msg.caption or "",
            "caption_entities": caption_entities  # ← для подписи к фото
        }
    
    if getattr(msg, "video", None):
        return {
            "type": "video",
            "file_id": msg.video.file_id,
            "caption": msg.caption or "",
            "caption_entities": caption_entities  # ← для подписи к видео
        }
    
    if getattr(msg, "animation", None):
        return {
            "type": "animation",
            "file_id": msg.animation.file_id,
            "caption": msg.caption or "",
            "caption_entities": caption_entities  # ← для подписи к гифке
        }
    
    return {"type": "unknown"}

@bot.message_handler(commands=["parviz"])
def full_backup_zip(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    import os
    import zipfile
    import shutil
    from datetime import datetime

    workdir = os.getcwd()
    temp_dir = "backup_temp"
    os.makedirs(temp_dir, exist_ok=True)

    backed_up_files = []

    # Ищем ВСЕ .db, .json и .txt файлы
    for file in os.listdir(workdir):
        if file.endswith((".db", ".json", ".txt")):
            try:
                shutil.copy(file, os.path.join(temp_dir, file))
                backed_up_files.append(file)
            except Exception as e:
                print(f"Не удалось скопировать {file}: {e}")

    if not backed_up_files:
        bot.send_message(message.chat.id, "❌ Файлы для бэкапа не найдены")
        return

    # Имя ZIP
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = f"backup_{timestamp}.zip"

    # Создаём ZIP
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in backed_up_files:
            zipf.write(
                os.path.join(temp_dir, file),
                arcname=file
            )

    # Отправляем ZIP
    with open(zip_name, "rb") as f:
        bot.send_document(
            message.chat.id,
            f,
            caption=(
                "🗂 <b>Полный бэкап бота</b>\n\n"
                f"📦 Файлов: <code>{len(backed_up_files)}</code>\n"
                "📁 Формат: <code>.zip</code>\n"
                "🛡 База безопасна\n\n"
                f"<b>Типы файлов:</b>\n"
                f"• Базы данных: <code>.db</code>\n"
                f"• Конфиги: <code>.json</code>\n"
                f"• Логи: <code>.txt</code>"
            ),
            parse_mode="HTML"
        )

    # Убираем за собой
    try:
        shutil.rmtree(temp_dir)
        os.remove(zip_name)
    except:
        pass
        
# ================== УЛУЧШЕННАЯ СИСТЕМА БРАКОВ (SQLite) ==================
MARRIAGE_DB = "marriages.db"

# Инициализация базы данных браков
def init_marriage_db():
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    # Основная таблица браков
    c.execute("""
        CREATE TABLE IF NOT EXISTS marriages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            user1_name TEXT NOT NULL,
            user2_name TEXT NOT NULL,
            married_at TEXT NOT NULL,
            divorce_count INTEGER DEFAULT 0,
            UNIQUE(user1_id, user2_id)
        )
    """)
    
    # Таблица запросов на брак
    c.execute("""
        CREATE TABLE IF NOT EXISTS marriage_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            from_user_name TEXT NOT NULL,
            to_user_id INTEGER NOT NULL,
            to_user_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            UNIQUE(from_user_id, to_user_id)
        )
    """)
    
    # Таблица статистики браков
    c.execute("""
        CREATE TABLE IF NOT EXISTS marriage_stats (
            user_id INTEGER PRIMARY KEY,
            total_marriages INTEGER DEFAULT 0,
            total_days_married INTEGER DEFAULT 0,
            longest_marriage_days INTEGER DEFAULT 0,
            last_marriage_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_marriage_db()

def cleanup_expired_requests():
    """Очищает просроченные запросы на брак (24 часа)"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    expired_time = (datetime.now() - timedelta(hours=24)).isoformat()
    c.execute("DELETE FROM marriage_requests WHERE expires_at < ?", (expired_time,))
    conn.commit()
    conn.close()

def get_marriage(user_id):
    """Получает информацию о браке пользователя"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT user1_id, user2_id, user1_name, user2_name, married_at, divorce_count 
        FROM marriages 
        WHERE user1_id = ? OR user2_id = ?
    """, (user_id, user_id))
    
    marriage = c.fetchone()
    conn.close()
    
    if marriage:
        user1_id, user2_id, user1_name, user2_name, married_at, divorce_count = marriage
        partner_id = user2_id if user1_id == user_id else user1_id
        partner_name = user2_name if user1_id == user_id else user1_name
        
        return {
            "partner_id": partner_id,
            "partner_name": partner_name,
            "married_at": married_at,
            "divorce_count": divorce_count,
            "user1_id": user1_id,
            "user2_id": user2_id
        }
    return None

def get_marriage_stats(user_id):
    """Получает статистику браков пользователя"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    c.execute("SELECT total_marriages, total_days_married, longest_marriage_days FROM marriage_stats WHERE user_id = ?", (user_id,))
    stats = c.fetchone()
    
    if not stats:
        # Создаем запись если нет статистики
        c.execute("INSERT INTO marriage_stats (user_id) VALUES (?)", (user_id,))
        conn.commit()
        stats = (0, 0, 0)
    
    conn.close()
    return {
        "total_marriages": stats[0],
        "total_days_married": stats[1],
        "longest_marriage_days": stats[2]
    }

def update_marriage_stats(user_id, marriage_days):
    """Обновляет статистику браков пользователя"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    stats = get_marriage_stats(user_id)
    new_total_marriages = stats["total_marriages"] + 1
    new_total_days = stats["total_days_married"] + marriage_days
    new_longest = max(stats["longest_marriage_days"], marriage_days)
    
    c.execute("""
        INSERT OR REPLACE INTO marriage_stats 
        (user_id, total_marriages, total_days_married, longest_marriage_days, last_marriage_date) 
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, new_total_marriages, new_total_days, new_longest, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def create_marriage_request(from_user_id, from_user_name, to_user_id, to_user_name):
    """Создает запрос на брак"""
    cleanup_expired_requests()  # Очищаем старые запросы
    
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    try:
        # Проверяем, нет ли уже брака
        if get_marriage(from_user_id) or get_marriage(to_user_id):
            return False, "💔 Один из пользователей уже в браке!"
        
        # Проверяем существующий запрос
        c.execute("SELECT 1 FROM marriage_requests WHERE from_user_id = ? AND to_user_id = ?", 
                 (from_user_id, to_user_id))
        if c.fetchone():
            return False, "⏳ Запрос на брак уже отправлен!"
        
        # Создаем запрос (действует 24 часа)
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        c.execute("""
            INSERT INTO marriage_requests 
            (from_user_id, from_user_name, to_user_id, to_user_name, created_at, expires_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (from_user_id, from_user_name, to_user_id, to_user_name, 
              datetime.now().isoformat(), expires_at))
        
        conn.commit()
        return True, "💌 Запрос на брак отправлен! Действует 24 часа."
        
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def accept_marriage_request(from_user_id, to_user_id):
    """Принимает запрос на брак"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    try:
        # Получаем информацию о запросе
        c.execute("SELECT from_user_name, to_user_name FROM marriage_requests WHERE from_user_id = ? AND to_user_id = ?", 
                 (from_user_id, to_user_id))
        request = c.fetchone()
        
        if not request:
            return False, "❌ Запрос на брак не найден или истек!"
        
        from_user_name, to_user_name = request
        
        # Создаем брак
        c.execute("""
            INSERT INTO marriages 
            (user1_id, user2_id, user1_name, user2_name, married_at) 
            VALUES (?, ?, ?, ?, ?)
        """, (from_user_id, to_user_id, from_user_name, to_user_name, datetime.now().isoformat()))
        
        # Удаляем запрос
        c.execute("DELETE FROM marriage_requests WHERE from_user_id = ? AND to_user_id = ?", 
                 (from_user_id, to_user_id))
        
        conn.commit()
        return True, "💍 Брак заключен! Желаем счастья! 💕"
        
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def reject_marriage_request(from_user_id, to_user_id):
    """Отклоняет запрос на брак"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM marriage_requests WHERE from_user_id = ? AND to_user_id = ?", 
                 (from_user_id, to_user_id))
        conn.commit()
        return True, "Запрос на брак отклонен"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def divorce_marriage(user_id):
    """Расторгает брак и обновляет статистику"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    try:
        marriage = get_marriage(user_id)
        if not marriage:
            return False, "❌ Вы не в браке!"
        
        # Вычисляем длительность брака
        marriage_days = get_marriage_days(marriage["married_at"])
        
        # Обновляем статистику для обоих партнеров
        update_marriage_stats(user_id, marriage_days)
        update_marriage_stats(marriage["partner_id"], marriage_days)
        
        # Увеличиваем счетчик разводов
        c.execute("UPDATE marriages SET divorce_count = divorce_count + 1 WHERE user1_id = ? OR user2_id = ?", 
                 (user_id, user_id))
        
        # Удаляем брак
        c.execute("DELETE FROM marriages WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        
        conn.commit()
        return True, f"💔 Брак расторгнут! Вы были вместе {marriage_days} дней."
        
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def get_all_marriages(limit=40):
    """Получает список всех браков"""
    conn = sqlite3.connect(MARRIAGE_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT user1_id, user2_id, user1_name, user2_name, married_at 
        FROM marriages 
        ORDER BY married_at DESC 
        LIMIT ?
    """, (limit,))
    
    marriages = c.fetchall()
    conn.close()
    return marriages

def get_marriage_days(married_at):
    """Вычисляет количество дней в браке"""
    married_date = datetime.fromisoformat(married_at)
    current_date = datetime.now()
    return (current_date - married_date).days

def get_marriage_rank(marriage_days):
    """Определяет ранг брака по количеству дней"""
    if marriage_days >= 365 * 10:
        return "👑 Золотая свадьба"
    elif marriage_days >= 365 * 5:
        return "💎 Сапфировая свадьба"
    elif marriage_days >= 365 * 2:
        return "💍 Стеклянная свадьба"
    elif marriage_days >= 365:
        return "📜 Бумажная свадьба"
    elif marriage_days >= 180:
        return "🍯 Медовый месяц"
    elif marriage_days >= 30:
        return "🌹 Романтический период"
    else:
        return "💕 Начало отношений"

# ================== КОМАНДА БРАК ==================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("+брак"))
def marriage_proposal(message):
    try:
        user_id = message.from_user.id
        from_user_name = message.from_user.first_name
        
        # Очищаем просроченные запросы
        cleanup_expired_requests()
        
        # Определяем целевого пользователя
        target_user = None
        target_user_id = None
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            target_user_id = target_user.id
        else:
            parts = message.text.split()
            if len(parts) > 1:
                mention = parts[1]
                if mention.startswith('@'):
                    try:
                        target_user = bot.get_chat(mention)
                        target_user_id = target_user.id
                    except:
                        bot.send_message(message.chat.id, "❌ Пользователь не найден!")
                        return
                else:
                    try:
                        target_user_id = int(mention)
                        target_user = bot.get_chat(target_user_id)
                    except:
                        bot.send_message(message.chat.id, "❌ Неверный формат ID!")
                        return
        
        if not target_user or not target_user_id:
            bot.send_message(message.chat.id, 
                           "💍 <b>Использование команды:</b>\n\n"
                           "• Ответь на сообщение: <code>+брак</code>\n"
                           "• Или укажи ID: <code>+брак [ID]</code>\n"
                           "• Или укажи @username: <code>+брак @username</code>",
                           parse_mode="HTML")
            return
        
        # Проверки
        if target_user_id == user_id:
            bot.send_message(message.chat.id, "❌ Нельзя предложить брак самому себе!")
            return
        
        if target_user.is_bot:
            bot.send_message(message.chat.id, "❌ Нельзя предложить брак боту!")
            return
        
        # Создаем запрос на брак
        success, result_msg = create_marriage_request(
            user_id, from_user_name, 
            target_user_id, target_user.first_name
        )
        
        if success:
            from_mention = f'<a href="tg://user?id={user_id}">{from_user_name}</a>'
            to_mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
            
            text = (
                f"💞 {from_mention} решил(а) сделать предложение руки и сердца {to_mention}\n\n"
                f"💌 Запрос действует 24 часа\n"
                f"🧸 Соглашайся или отказывайся..."
            )
            
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton(" Согласиться", callback_data=f"marriage_accept_{user_id}_{target_user_id}"),
                InlineKeyboardButton(" Отказать", callback_data=f"marriage_reject_{user_id}_{target_user_id}")
            )
            
            msg = bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)
            
            # Сохраняем ID сообщения для возможного обновления
            return True
            
        else:
            bot.send_message(message.chat.id, result_msg)
            return False
            
    except Exception as e:
        logger.error(f"Ошибка предложения брака: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при предложении брака!")
        return False

# ================== ОБРАБОТЧИКИ КНОПОК БРАКА ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("marriage_accept_"))
def accept_marriage_callback(call):
    try:
        # Разбираем callback data
        parts = call.data.split("_")
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "❌ Ошибка в данных!", show_alert=True)
            return
            
        from_user_id = int(parts[2])
        to_user_id = int(parts[3])
        
        # Проверяем, что нажимает именно тот, кому предложили брак
        if call.from_user.id != to_user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Принимаем брак
        success, result_msg = accept_marriage_request(from_user_id, to_user_id)
        
        if success:
            # Получаем информацию о пользователях
            try:
                from_user = bot.get_chat(from_user_id)
                to_user = bot.get_chat(to_user_id)
                
                from_mention = f'<a href="tg://user?id={from_user_id}">{from_user.first_name}</a>'
                to_mention = f'<a href="tg://user?id={to_user_id}">{to_user.first_name}</a>'
                
                text = (
                    f"💞 {to_mention}, ты принял(а) предложение о вступлении в брак с {from_mention}\n\n"
                    f"💍 С ребёнком не тяните "
                )
                
            except Exception as e:
                text = f"💞 Брак заключен! 💍\n\n{result_msg}"
            
            # Редактируем исходное сообщение
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            
            bot.answer_callback_query(call.id, "💍 Вы приняли предложение!")
        else:
            bot.answer_callback_query(call.id, f"❌ {result_msg}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка принятия брака: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при принятии брака!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("marriage_reject_"))
def reject_marriage_callback(call):
    try:
        # Разбираем callback data
        parts = call.data.split("_")
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "❌ Ошибка в данных!", show_alert=True)
            return
            
        from_user_id = int(parts[2])
        to_user_id = int(parts[3])
        
        # Проверяем, что нажимает именно тот, кому предложили брак
        if call.from_user.id != to_user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Отклоняем брак
        success, result_msg = reject_marriage_request(from_user_id, to_user_id)
        
        if success:
            # Получаем информацию о пользователях
            try:
                from_user = bot.get_chat(from_user_id)
                to_user = bot.get_chat(to_user_id)
                
                from_mention = f'<a href="tg://user?id={from_user_id}">{from_user.first_name}</a>'
                to_mention = f'<a href="tg://user?id={to_user_id}">{to_user.first_name}</a>'
                
                text = (
                    f"💔 {to_mention}, к большому сожалению {from_mention} отказался(ась) быть с тобой вместе 😔"
                )
                
            except Exception as e:
                text = "💔 Запрос на брак отклонен"
            
            # Редактируем исходное сообщение
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            
            bot.answer_callback_query(call.id, "❌ Вы отклонили предложение!")
        else:
            bot.answer_callback_query(call.id, f"❌ {result_msg}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка отклонения брака: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при отклонении брака!", show_alert=True)

# ================== КОМАНДА "МОЙ БРАК" (УЛУЧШЕННЫЙ ДИЗАЙН) ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой брак", "бракэыжчж", "статистика брака"])
def my_marriage(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'
        
        marriage = get_marriage(user_id)
        stats = get_marriage_stats(user_id)
        
        if not marriage:
            text = (
                f"<b>💍 Информация о браке</b>\n\n"
                f"Пользователь: {mention}\n"
                f"Статус: Не состоите в браке\n\n"
                f"<b>📈 Статистика:</b>\n"
                f"• Общее количество браков: {stats['total_marriages']}\n"
                f"• Всего дней в браке: {stats['total_days_married']}\n"
                f"• Самый продолжительный брак: {stats['longest_marriage_days']} дней\n\n"
                f"Для создания брака используйте команду +брак [ответ на сообщение]"
            )
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            return
        
        # Получаем информацию о партнере
        partner_id = marriage["partner_id"]
        partner_mention = f'<a href="tg://user?id={partner_id}">{marriage["partner_name"]}</a>'
        
        # Вычисляем количество дней в браке
        days_married = get_marriage_days(marriage["married_at"])
        marriage_rank = get_marriage_rank(days_married)
        
        text = (
            f"<b>💍 Информация о браке</b>\n\n"
            f"Пользователь: {mention}\n"
            f"Супруг(а): {partner_mention}\n"
            f"Статус: Состоите в браке\n\n"
            f"<b>📊 Детали брака:</b>\n"
            f"• Продолжительность: {days_married} дней\n"
            f"• Уровень отношений: {marriage_rank}\n"
            f"• Дата заключения: {datetime.fromisoformat(marriage['married_at']).strftime('%d.%m.%Y')}\n"
            f"• Количество разводов: {marriage['divorce_count']}\n\n"
            f"<b>📈 Общая статистика:</b>\n"
            f"• Всего браков: {stats['total_marriages']}\n"
            f"• Суммарное время в браке: {stats['total_days_married']} дней\n"
            f"• Рекордная продолжительность: {stats['longest_marriage_days']} дней"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(" Развестись", callback_data=f"marriage_divorce_{user_id}"))
        kb.add(InlineKeyboardButton("Статистика", callback_data=f"marriage_stats_{user_id}"))
        
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка показа брака: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении информации о браке.")

# ================== ОБРАБОТЧИК КНОПКИ РАЗВОДА ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("marriage_divorce_"))
def divorce_marriage_callback(call):
    try:
        parts = call.data.split("_")
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "Ошибка обработки запроса.", show_alert=True)
            return
            
        user_id = int(parts[2])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "Эта функция доступна только участнику брака.", show_alert=True)
            return
        
        success, result_msg = divorce_marriage(user_id)
        
        if success:
            try:
                user = bot.get_chat(user_id)
                mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
                text = f"Брак успешно расторгнут. {result_msg}"
            except:
                text = result_msg
            
            bot.edit_message_text(
                f"<b>💔 Расторжение брака</b>\n\n{text}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            
            bot.answer_callback_query(call.id, "Брак расторгнут")
        else:
            bot.answer_callback_query(call.id, result_msg, show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка развода: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при обработке запроса.", show_alert=True)

# ================== ОБРАБОТЧИК СТАТИСТИКИ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("marriage_stats_"))
def show_marriage_stats_callback(call):
    try:
        parts = call.data.split("_")
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "Ошибка обработки запроса.", show_alert=True)
            return
            
        user_id = int(parts[2])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "Доступ к статистике ограничен.", show_alert=True)
            return
        
        stats = get_marriage_stats(user_id)
        user = bot.get_chat(user_id)
        mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
        
        text = (
            f"<b>📊 Статистика браков</b>\n\n"
            f"Пользователь: {mention}\n\n"
            f"<b>Общие показатели:</b>\n"
            f"• Количество браков: {stats['total_marriages']}\n"
            f"• Общее время в браке: {stats['total_days_married']} дней\n"
            f"• Самый долгий брак: {stats['longest_marriage_days']} дней\n\n"
        )
        
        achievements = []
        if stats['total_marriages'] >= 10:
            achievements.append("• Серийный брачующийся")
        if stats['longest_marriage_days'] >= 365:
            achievements.append("• Годовой юбилей")
        if stats['longest_marriage_days'] >= 365 * 5:
            achievements.append("• Ветеран семейной жизни")
        
        if achievements:
            text += "<b>🏆 Достижения:</b>\n" + "\n".join(achievements)
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("← Назад к браку", callback_data=f"back_to_marriage_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при загрузке статистики.", show_alert=True)

# ================== ОБРАБОТЧИК НАЗАД К БРАКУ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("back_to_marriage_"))
def back_to_marriage_callback(call):
    try:
        parts = call.data.split("_")
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "Ошибка обработки запроса.", show_alert=True)
            return
            
        user_id = int(parts[3])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "Доступ ограничен.", show_alert=True)
            return
        
        class FakeMsg:
            def __init__(self, chat_id, from_user):
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = from_user
        
        fake_msg = FakeMsg(call.message.chat.id, call.from_user)
        my_marriage(fake_msg)
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка возврата к браку: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка.", show_alert=True)

# ================== КОМАНДА "БРАКИ" (ТОП-10 С МЕСТОМ ПОЛЬЗОВАТЕЛЯ) ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["браки", "список браков", "топ браков"])
def marriages_list(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        # Получаем список всех активных браков
        marriages = get_all_marriages(100)  # Получаем больше для поиска места
        
        if not marriages:
            bot.send_message(
                message.chat.id, 
                "<b>Информация о браках</b>\n\nВ настоящее время нет активных браков среди пользователей."
            )
            return
        
        # СОРТИРУЕМ браки по убыванию продолжительности
        marriages_with_days = []
        for marriage in marriages:
            user1_id, user2_id, user1_name, user2_name, married_at = marriage
            days_married = get_marriage_days(married_at)
            marriages_with_days.append((days_married, marriage))
        
        # Сортируем по убыванию дней
        marriages_with_days.sort(key=lambda x: x[0], reverse=True)
        
        # Извлекаем отсортированные браки
        sorted_marriages = [m[1] for m in marriages_with_days]
        
        text = "<b>Список браков</b>\n\n"
        
        # Показываем только топ-10 (самые долгие браки)
        top_marriages = sorted_marriages[:10]
        
        # Формируем список браков с индексацией
        for i, (user1_id, user2_id, user1_name, user2_name, married_at) in enumerate(top_marriages, 1):
            # Рассчитываем продолжительность брака
            days_married = get_marriage_days(married_at)
            marriage_rank = get_marriage_rank(days_married)
            
            # Форматируем строку с информацией о паре
            text += (
                f"<b>{i}.</b> "
                f"<a href='tg://user?id={user1_id}'>{user1_name}</a> и "
                f"<a href='tg://user?id={user2_id}'>{user2_name}</a>\n"
                f"   Продолжительность: {days_married} дней ({marriage_rank})\n\n"
            )
        
        text += "------------------------------\n\n"
        
        # Проверяем, состоит ли пользователь в браке
        marriage = get_marriage(user_id)
        if marriage:
            # Находим место пользователя в ОТСОРТИРОВАННОМ списке
            user_place = None
            for idx, (u1_id, u2_id, u1_name, u2_name, married_at) in enumerate(sorted_marriages, 1):
                if user_id in (u1_id, u2_id):
                    user_place = idx
                    partner_id = u2_id if u1_id == user_id else u1_id
                    partner_name = u2_name if u1_id == user_id else u1_name
                    days_married = get_marriage_days(married_at)
                    break
            
            if user_place:
                partner_mention = f'<a href="tg://user?id={partner_id}">{partner_name}</a>'
                text += (
                    f"<a href='tg://user?id={user_id}'>{user_name}</a>, вы находитесь на <b>{user_place}</b> месте в списке."
                )
            else:
                text += f"<a href='tg://user?id={user_id}'>{user_name}</a>, вы не входите в топ-10 браков."
        else:
            text += f"<a href='tg://user?id={user_id}'>{user_name}</a>, вы не состоите в браке."
        
        bot.send_message(
            message.chat.id, 
            text, 
            parse_mode="HTML", 
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка при формировании списка браков: {e}")
        bot.send_message(
            message.chat.id, 
            "Произошла ошибка при загрузке списка браков. Пожалуйста, попробуйте позже."
        )



# ================== БЛОКИРОВКА ПОЛЬЗОВАТЕЛЕЙ ==================
BLOCKED_USERS_DB = "blocked_users.db"

# Инициализация базы данных для заблокированных пользователей
def init_blocked_users_db():
    conn = sqlite3.connect(BLOCKED_USERS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS blocked_users
                 (user_id INTEGER PRIMARY KEY, username TEXT, blocked_by INTEGER, blocked_at TEXT)''')
    conn.commit()
    conn.close()

init_blocked_users_db()

def is_user_blocked(user_id):
    """Проверяет, заблокирован ли пользователь"""
    conn = sqlite3.connect(BLOCKED_USERS_DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM blocked_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def block_user(user_id, username, blocked_by_id):
    """Блокирует пользователя"""
    conn = sqlite3.connect(BLOCKED_USERS_DB)
    c = conn.cursor()
    blocked_at = datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO blocked_users (user_id, username, blocked_by, blocked_at) VALUES (?, ?, ?, ?)",
              (user_id, username, blocked_by_id, blocked_at))
    conn.commit()
    conn.close()

def unblock_user(user_id):
    """Разблокирует пользователя"""
    conn = sqlite3.connect(BLOCKED_USERS_DB)
    c = conn.cursor()
    c.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Глобальный обработчик для блокировки команд
@bot.message_handler(func=lambda m: is_user_blocked(m.from_user.id))
def handle_blocked_users(message):
    """Игнорирует все сообщения от заблокированных пользователей"""
    return

# ================== КОМАНДА ЗАБЛОКИРОВАТЬ С ПРИЧИНОЙ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("заблокировать"))
def block_user_cmd(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Проверка прав администратора
    if user_id not in ADMIN_IDS:
        bot.send_message(message.chat.id, f"<blockquote>❌ {mention} Тебе не доступна эта команда</blockquote>", parse_mode="HTML")
        return
    
    try:
        target_user = None
        target_id = None
        reason = "Не указана"
        
        # Проверяем, есть ли реплай
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            target_id = target_user.id
            
            # Извлекаем причину из текста (всё после "заблокировать")
            parts = message.text.split()
            if len(parts) > 1:
                reason = ' '.join(parts[1:])
        else:
            # Пытаемся получить ID и причину из текста команды
            parts = message.text.split()
            if len(parts) >= 3:
                target_id = int(parts[1])
                target_user = bot.get_chat(target_id)
                reason = ' '.join(parts[2:])
            elif len(parts) >= 2:
                target_id = int(parts[1])
                target_user = bot.get_chat(target_id)
                reason = "Не указана"
            else:
                bot.send_message(message.chat.id, 
                               f"<blockquote>"
                               f"<b>📝 Использование команды:</b>\n\n"
                               f"• <code>заблокировать [ID] [причина]</code>\n"
                               f"• Ответь на сообщение: <code>заблокировать [причина]</code>\n\n"
                               f"<b>Примеры:</b>\n"
                               f"• <code>заблокировать 7985048553 Махинации</code>\n"
                               f"• Ответь: <code>заблокировать Нарушение правил</code>"
                               f"</blockquote>", 
                               parse_mode="HTML")
                return
        
        if not target_user:
            bot.send_message(message.chat.id, 
                           f"<blockquote>"
                           f"<b>📝 Использование команды:</b>\n\n"
                           f"• <code>заблокировать [ID] [причина]</code>\n"
                           f"• Ответь на сообщение: <code>заблокировать [причина]</code>"
                           f"</blockquote>", 
                           parse_mode="HTML")
            return
        
        # Проверяем, не пытается ли админ заблокировать сам себя
        if target_id == user_id:
            bot.send_message(message.chat.id, f"<blockquote>❌ {mention} Нельзя заблокировать самого себя!</blockquote>", parse_mode="HTML")
            return
        
        # Проверяем, не является ли целевой пользователь админом
        if target_id in ADMIN_IDS:
            bot.send_message(message.chat.id, f"<blockquote>❌ {mention} Нельзя заблокировать администратора!</blockquote>", parse_mode="HTML")
            return
        
        # Блокируем пользователя
        block_user(target_id, target_user.first_name, user_id)
        
        target_mention = f'<a href="tg://user?id={target_id}">{target_user.first_name}</a>'
        admin_mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        # Сообщение в чате
        bot.send_message(message.chat.id, 
                       f"<blockquote>"
                       f"🔒 <b>БЛОКИРОВКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
                       f"👤 <b>Пользователь:</b> {target_mention}\n"
                       f"🛡 <b>Администратор:</b> {admin_mention}\n"
                       f"📝 <b>Причина:</b> <i>{reason}</i>\n\n"
                       f"❌ Доступ к основным командам бота ограничен"
                       f"</blockquote>", 
                       parse_mode="HTML")
        
        # Уведомляем заблокированного пользователя
        try:
            bot.send_message(target_id, 
                           f"<blockquote>"
                           f"🔒 <b>ВЫ БЫЛИ ЗАБЛОКИРОВАНЫ В БОТЕ</b>\n\n"
                           f"🛡 <b>Администратор:</b> {admin_mention}\n"
                           f"📝 <b>Причина:</b> <i>{reason}</i>\n\n"
                           f"❌ Доступ к командам бота ограничен"
                           f"</blockquote>", 
                           parse_mode="HTML")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, 
                       f"<blockquote>"
                       f"❌ <b>Неверный формат ID!</b>\n\n"
                       f"<b>📋 Примеры использования:</b>\n\n"
                       f"• <code>заблокировать 123456789 Махинации</code>\n"
                       f"• Ответь на сообщение: <code>заблокировать Нарушение правил</code>\n\n"
                       f"<i>ID должен состоять только из цифр</i>"
                       f"</blockquote>", 
                       parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, 
                       f"<blockquote>"
                       f"❌ <b>Ошибка выполнения команды</b>\n\n"
                       f"<i>Ошибка: {e}</i>\n\n"
                       f"Проверьте правильность введенных данных."
                       f"</blockquote>", 
                       parse_mode="HTML")

# ================== КОМАНДА РАЗБЛОКИРОВАТЬ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("разблокировать"))
def unblock_user_cmd(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Проверка прав администратора
    if user_id not in ADMIN_IDS:
        bot.send_message(message.chat.id, f"<blockquote>❌ {mention} Тебе не доступна эта команда</blockquote>", parse_mode="HTML")
        return
    
    try:
        target_user = None
        target_id = None
        
        # Проверяем, есть ли реплай
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            target_id = target_user.id
        else:
            # Пытаемся получить ID из текста команды
            parts = message.text.split()
            if len(parts) >= 2:
                target_id = int(parts[1])
                target_user = bot.get_chat(target_id)
        
        if not target_user:
            bot.send_message(message.chat.id, 
                           f"<blockquote>"
                           f"<b>📝 Использование команды:</b>\n\n"
                           f"• <code>разблокировать [ID]</code>\n"
                           f"• Ответь на сообщение пользователя\n\n"
                           f"<b>Пример:</b>\n"
                           f"• <code>разблокировать 123456789</code>"
                           f"</blockquote>", 
                           parse_mode="HTML")
            return
        
        # Проверяем, заблокирован ли пользователь
        if not is_user_blocked(target_id):
            bot.send_message(message.chat.id, f"<blockquote>⚠️ {mention} Этот пользователь не заблокирован!</blockquote>", parse_mode="HTML")
            return
        
        # Разблокируем пользователя
        unblock_user(target_id)
        
        target_mention = f'<a href="tg://user?id={target_id}">{target_user.first_name}</a>'
        admin_mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        # Сообщение в чате
        bot.send_message(message.chat.id, 
                       f"<blockquote>"
                       f"🔓 <b>РАЗБЛОКИРОВКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
                       f"👤 <b>Пользователь:</b> {target_mention}\n"
                       f"🛡 <b>Администратор:</b> {admin_mention}\n\n"
                       f"✅ Доступ к командам бота восстановлен"
                       f"</blockquote>", 
                       parse_mode="HTML")
        
        # Уведомляем разблокированного пользователя
        try:
            bot.send_message(target_id, 
                           f"<blockquote>"
                           f"🔓 <b>ВЫ БЫЛИ РАЗБЛОКИРОВАНЫ В БОТЕ</b>\n\n"
                           f"🛡 <b>Администратор:</b> {admin_mention}\n\n"
                           f"✅ Доступ к командам бота восстановлен"
                           f"</blockquote>", 
                           parse_mode="HTML")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, 
                       f"<blockquote>"
                       f"❌ <b>Неверный формат ID!</b>\n\n"
                       f"<b>📋 Примеры использования:</b>\n\n"
                       f"• <code>разблокировать 123456789</code>\n"
                       f"• Ответь на сообщение пользователя\n\n"
                       f"<i>ID должен состоять только из цифр</i>"
                       f"</blockquote>", 
                       parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, 
                       f"<blockquote>"
                       f"❌ <b>Ошибка выполнения команды</b>\n\n"
                       f"<i>Ошибка: {e}</i>\n\n"
                       f"Проверьте правильность введенных данных."
                       f"</blockquote>", 
                       parse_mode="HTML")

# ================== КОМАНДА БОТ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["бот", "bot", "meow"])
def bot_response(message):
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Список случайных ответов
    responses = [
        f"<b>⭐ {mention} Izzzy спит</b>",
        f"<b>🌟 {mention} Иззичат</b>",
        f"<b>💫 {mention} Сафонов - плати</b>",
        f"<b>✨ {mention} Зови - мне лень приходить</b>",
        f"<b>🎯 {mention} Батя в здании</b>",
        f"<b>Izzzy tyta</b>"
    ]
    
    # Выбираем случайный ответ
    response = random.choice(responses)
    
    # Отправляем ответ
    if message.reply_to_message:
        # Если команда отправлена ответом на сообщение
        bot.reply_to(message.reply_to_message, response, parse_mode="HTML")
    else:
        # Если команда отправлена просто так
        bot.send_message(message.chat.id, response, parse_mode="HTML")





# ======================================================
# БОНУС
# ======================================================

DAILY_BONUS_AMOUNT = 3500

def can_take_daily_bonus(user_id):
    data = get_user_data(user_id)
    today = date.today().isoformat()
    return data.get("daily_bonus_claimed") != today

def give_daily_bonus(user_id):
    data = get_user_data(user_id)
    data["balance"] += DAILY_BONUS_AMOUNT
    data["daily_bonus_claimed"] = date.today().isoformat()
    save_user_data(user_id, data)


# ======================================================
# VIP СТАТУС
# ======================================================

def get_vip_status(user_id):
    data = get_user_data(user_id)
    vip = data.get("vip", {})

    if isinstance(vip, dict):
        return vip.get("level", 0) > 0

    return False


# ======================================================
# АВТО-ВЫДАЧА БОНУСА ПО ССЫЛКЕ /start bonus
# ======================================================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start bonus"))
def start_bonus(message):
    user_id = message.from_user.id

    if not can_take_daily_bonus(user_id):
        return bot.send_message(
            user_id,
            "❌ <b>Вы уже получили бонус сегодня!</b>",
            parse_mode="HTML"
        )

    give_daily_bonus(user_id)

    bot.send_message(
        user_id,
        f"🎁 <b>Бонус автоматически выдан!</b>\n💸 +{DAILY_BONUS_AMOUNT}$",
        parse_mode="HTML"
    )


# ======================================================
# ======================================================
#    БАЛАНС (С VIP)
# ======================================================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["б", "баланс"])
def balance_cmd(message):
    user_id = message.from_user.id
    user = bot.get_chat(user_id)
    data = get_user_data(user_id)

    # Префикс
    prefix_data = get_user_prefix(user_id)
    prefix_display = prefix_data["name"] if prefix_data else "Нет"

    # VIP статус
    vip_data = data.get("vip", {})
    vip_level = vip_data.get("level", 0)
    if vip_level > 0:
        vip_info = VIP_LEVELS.get(vip_level, {})
        vip_display = f"{vip_info.get('prefix', '⭐')} {vip_info.get('name', 'VIP')}"
    else:
        vip_display = "Нет"

    # Имя с префиксом
    clickable = f"<a href='tg://user?id={user_id}'>{user.first_name}</a>"
    if prefix_data:
        prefix_emoji = (
            prefix_data["name"].split()[0]
            if " " in prefix_data["name"]
            else prefix_data["name"]
        )
        clickable = f"{prefix_emoji} {clickable}"

    # Текст
    text = (
        f"👤 <b>Имя:</b> {clickable}\n"
        f"💰 <b>Баланс:</b> <code>{format_number(data['balance'])} izzzy</code>\n"
        f"💎 <b>VIP:</b> {vip_display}"
    )

    # Кнопки
    kb = types.InlineKeyboardMarkup()

    if prefix_data:
        kb.add(
            types.InlineKeyboardButton(
                "💸 Продать префикс",
                callback_data=f"sell_prefix_{user_id}"
            )
        )
    else:
        kb.add(
            types.InlineKeyboardButton(
                "🛒 Купить префикс",
                callback_data=f"buy_prefix_menu_{user_id}"
            )
        )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=kb
    )


# ======================================================
# МАГАЗИН ПРЕФИКСОВ
# ======================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_prefix_menu_"))
def buy_prefix_menu(call):
    user_id = int(call.data.split("_")[-1])
    
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твой баланс!", show_alert=True)
        return

    prefixes = get_all_prefixes()

    text = "<b>🛒 Магазин префиксов</b>\n\n"
    for p in prefixes:
        text += f"{p['name']} — <b>{format_number(p['price'])} izzzy</b>\n"

    kb = types.InlineKeyboardMarkup()
    for p in prefixes:
        kb.add(types.InlineKeyboardButton(
            f"Купить {p['name']}",
            callback_data=f"buy_prefix_{p['id']}_{user_id}"
        ))

    kb.add(types.InlineKeyboardButton("‹ Назад", callback_data=f"back_to_balance_{user_id}"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="HTML", reply_markup=kb)
    bot.answer_callback_query(call.id)


# ======================================================
# ПОКУПКА ПРЕФИКСА
# ======================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_prefix_"))
def buy_prefix(call):
    _, _, prefix_id, owner_id = call.data.split("_")
    prefix_id = int(prefix_id)
    owner_id = int(owner_id)

    if call.from_user.id != owner_id:
        bot.answer_callback_query(call.id, "❌ Это не твой баланс!", show_alert=True)
        return

    data = get_user_data(owner_id)
    prefix = get_prefix(prefix_id)

    if data["balance"] < prefix["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно средств!", show_alert=True)
        return

    data["balance"] -= prefix["price"]
    save_casino_data()

    set_user_prefix(owner_id, prefix_id, prefix["price"])

    user = bot.get_chat(owner_id)
    mention = f"<a href='tg://user?id={owner_id}'>{user.first_name}</a>"

    text = f"🎉 {mention}, ты купил префикс {prefix['name']}!"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("‹ Назад", callback_data=f"back_to_balance_{owner_id}"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="HTML", reply_markup=kb)

    bot.answer_callback_query(call.id)


# ======================================================
# ПРОДАЖА ПРЕФИКСА
# ======================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("sell_prefix_"))
def sell_prefix(call):
    owner_id = int(call.data.split("_")[-1])

    if call.from_user.id != owner_id:
        bot.answer_callback_query(call.id, "❌ Это не твой баланс!", show_alert=True)
        return

    prefix = get_user_prefix(owner_id)
    if not prefix:
        bot.answer_callback_query(call.id, "❌ У тебя нет префикса!", show_alert=True)
        return

    sell_price = prefix["price_paid"] // 4

    data = get_user_data(owner_id)
    data["balance"] += sell_price
    save_casino_data()

    remove_user_prefix(owner_id)

    user = bot.get_chat(owner_id)
    mention = f"<a href='tg://user?id={owner_id}'>{user.first_name}</a>"

    text = f"💸 {mention}, префикс продан за <b>{format_number(sell_price)} izzzy</b>!"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("‹ Назад", callback_data=f"back_to_balance_{owner_id}"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="HTML", reply_markup=kb)

    bot.answer_callback_query(call.id)


# ======================================================
# НАЗАД В БАЛАНС
# ======================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_balance_"))
def back_balance(call):
    uid = int(call.data.split("_")[-1])
    
    if call.from_user.id != uid:
        bot.answer_callback_query(call.id, "❌ Это не твой баланс!", show_alert=True)
        return
        
    fake = type("msg", (), {})()
    fake.chat = call.message.chat
    fake.from_user = type("user", (), {"id": uid})()
    bot.delete_message(call.message.chat.id, call.message.message_id)
    balance_cmd(fake)
    bot.answer_callback_query(call.id)

# ======================================================
# ======================================================
# ================== ТОПЫ ==================
# ======================================================

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("топ"))
def top_cmd(message):
    # Парсим количество из команды
    parts = message.text.lower().split()
    limit = 50  # По умолчанию 50
    
    if len(parts) > 1:
        try:
            requested_limit = int(parts[1])
            # Проверяем допустимые значения
            if requested_limit in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500]:
                limit = requested_limit
            else:
                bot.reply_to(message, 
                    "❌ Допустимые значения: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500\n"
                    "Примеры: <code>топ 10</code>, <code>топ 50</code>, <code>топ 100</code>",
                    parse_mode="HTML")
                return
        except ValueError:
            pass
    
    # Собираем данные пользователей
    users = []
    for uid_str, data in casino_data.items():
        try:
            uid = int(uid_str)
            bal = data.get("balance", 0)
            if bal > 0:
                users.append((uid, bal))
        except:
            continue

    # Сортируем по балансу
    users.sort(key=lambda x: x[1], reverse=True)
    
    # Если топ пустой
    if not users:
        bot.send_message(message.chat.id, f"🏆 <b>Топ {limit} игроков:</b>\n\n📊 Пока нет данных для топа", 
                        parse_mode="HTML", disable_web_page_preview=True)
        return
    
    # Если лимит <= 100 - показываем сразу
    if limit <= 100:
        send_top_page(message, users, limit, 1, message.from_user.id)
    else:
        # Для больших списков показываем с пагинацией
        send_top_page_with_pagination(message, users, limit, 1, message.from_user.id)

def send_top_page(message, users, limit, page, owner_id):
    """Отправляет или редактирует сообщение с одной страницей топа"""
    start_idx = (page - 1) * 100
    end_idx = min(start_idx + 100, limit)
    
    # Берем нужное количество
    top_users = users[:limit][start_idx:end_idx]
    
    # Формируем текст
    if limit <= 100:
        text = f"🏆 <b>Топ {limit} игроков:</b>\n\n"
    else:
        text = f"🏆 <b>Топ {limit} игроков (страница {page} из { (limit + 99) // 100 }):</b>\n\n"
    
    # Нумерация с учетом страницы
    for i, (uid, bal) in enumerate(top_users, start_idx + 1):
        try:
            # Получаем имя пользователя
            user_data = get_user_data(uid)
            first_name = user_data.get("_first_name", f"User {uid}")
            
            if first_name == f"User {uid}":
                try:
                    user = bot.get_chat(uid)
                    first_name = user.first_name
                    user_data["_first_name"] = first_name
                    save_casino_data()
                except:
                    first_name = f"User {uid}"
            
            # Получаем префикс
            up = get_user_prefix(uid)
            if up:
                prefix_emoji = up['name'].split()[0] if up['name'] else ""
                text += f"{i}. {prefix_emoji} <a href=\"tg://user?id={uid}\">{first_name}</a> — {format_number(bal)} izzzy\n"
            else:
                text += f"{i}. <a href=\"tg://user?id={uid}\">{first_name}</a> — {format_number(bal)} izzzy\n"
            
        except Exception as e:
            text += f"{i}. User {uid} — {format_number(bal)} izzzy\n"
            continue
    
    # Проверяем, нужно ли отправить новое сообщение или отредактировать существующее
    if hasattr(message, 'message_id') and message.chat.id:
        # Редактируем существующее сообщение
        try:
            bot.edit_message_text(
                text,
                message.chat.id,
                message.message_id,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            # Если не получилось отредактировать (например, сообщение не найдено), отправляем новое
            bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)
    else:
        # Отправляем новое сообщение
        bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)

def send_top_page_with_pagination(message, users, limit, page, owner_id):
    """Отправляет или редактирует сообщение с пагинацией"""
    start_idx = (page - 1) * 100
    end_idx = min(start_idx + 100, limit)
    
    # Берем нужное количество
    top_users = users[:limit][start_idx:end_idx]
    
    # Рассчитываем общее количество страниц
    total_pages = (limit + 99) // 100
    
    # Формируем текст
    text = f"🏆 <b>Топ {limit} игроков (страница {page} из {total_pages}):</b>\n\n"
    
    # Нумерация с учетом страницы
    for i, (uid, bal) in enumerate(top_users, start_idx + 1):
        try:
            user_data = get_user_data(uid)
            first_name = user_data.get("_first_name", f"User {uid}")
            
            if first_name == f"User {uid}":
                try:
                    user = bot.get_chat(uid)
                    first_name = user.first_name
                    user_data["_first_name"] = first_name
                    save_casino_data()
                except:
                    first_name = f"User {uid}"
            
            up = get_user_prefix(uid)
            if up:
                prefix_emoji = up['name'].split()[0] if up['name'] else ""
                text += f"{i}. {prefix_emoji} <a href=\"tg://user?id={uid}\">{first_name}</a> — {format_number(bal)} izzzy\n"
            else:
                text += f"{i}. <a href=\"tg://user?id={uid}\">{first_name}</a> — {format_number(bal)} izzzy\n"
            
        except Exception as e:
            text += f"{i}. User {uid} — {format_number(bal)} izzzy\n"
            continue
    
    # Создаем клавиатуру с пагинацией (без эмодзи)
    kb = InlineKeyboardMarkup()
    
    # Кнопки навигации (только текст, без эмодзи)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("Назад", callback_data=f"top_page_{limit}_{page-1}_{owner_id}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперед", callback_data=f"top_page_{limit}_{page+1}_{owner_id}"))
    
    if nav_buttons:
        if len(nav_buttons) == 2:
            kb.row(nav_buttons[0], nav_buttons[1])
        else:
            kb.row(nav_buttons[0])
    
    # Кнопка для возврата к обычному топу (без эмодзи)
    kb.add(InlineKeyboardButton("Показать всё", callback_data=f"top_all_{limit}_{owner_id}"))
    
    # Проверяем, нужно ли отправить новое сообщение или отредактировать существующее
    if hasattr(message, 'message_id') and message.chat.id:
        # Редактируем существующее сообщение
        try:
            bot.edit_message_text(
                text,
                message.chat.id,
                message.message_id,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=kb
            )
        except Exception as e:
            # Если не получилось отредактировать, отправляем новое
            bot.send_message(
                message.chat.id, 
                text, 
                parse_mode="HTML", 
                disable_web_page_preview=True, 
                reply_markup=kb
            )
    else:
        # Отправляем новое сообщение
        bot.send_message(
            message.chat.id, 
            text, 
            parse_mode="HTML", 
            disable_web_page_preview=True, 
            reply_markup=kb
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith("top_page_"))
def top_page_callback(call):
    """Обработчик переключения страниц топа с защитой от чужих нажатий"""
    try:
        parts = call.data.split("_")
        limit = int(parts[2])
        page = int(parts[3])
        owner_id = int(parts[4])
        
        # ЗАЩИТА: проверяем, что нажимает владелец кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Собираем данные пользователей
        users = []
        for uid_str, data in casino_data.items():
            try:
                uid = int(uid_str)
                bal = data.get("balance", 0)
                if bal > 0:
                    users.append((uid, bal))
            except:
                continue
        
        users.sort(key=lambda x: x[1], reverse=True)
        
        # Обновляем сообщение (редактируем существующее)
        send_top_page_with_pagination(call.message, users, limit, page, owner_id)
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка загрузки страницы")
        logger.error(f"Ошибка в top_page_callback: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("top_all_"))
def top_all_callback(call):
    """Обработчик показа полного топа с защитой от чужих нажатий"""
    try:
        parts = call.data.split("_")
        limit = int(parts[2])
        owner_id = int(parts[3])
        
        # ЗАЩИТА: проверяем, что нажимает владелец кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Собираем данные пользователей
        users = []
        for uid_str, data in casino_data.items():
            try:
                uid = int(uid_str)
                bal = data.get("balance", 0)
                if bal > 0:
                    users.append((uid, bal))
            except:
                continue
        
        users.sort(key=lambda x: x[1], reverse=True)
        
        # Показываем первую страницу без пагинации (редактируем существующее)
        send_top_page(call.message, users, limit, 1, owner_id)
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка")
        logger.error(f"Ошибка в top_all_callback: {e}")



# ================== START МЕНЮ ==================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    get_user_referral_data(user_id)

    # Получаем username бота для создания ссылки добавления в группу
    bot_username = bot.get_me().username
    add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"
    
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    welcome_text = (
        f"Привет {mention}, я игровой чат бот, для того чтобы узнать обо мне по больше, "
        f"напиши команду /help или <code>помощь</code>. "
        f"Если хочешь добавить меня в свой чат, <a href='{add_to_group_url}'>нажми сюда</a> "
    )

    # Создаем инлайн клавиатуру с кнопкой для показа списка групп
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📋 Список групп для бота", callback_data="show_group_list"))

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=kb
    )

# ================== CALLBACK: ПОКАЗАТЬ СПИСОК ГРУПП ==================

@bot.callback_query_handler(func=lambda c: c.data == "show_group_list")
def show_group_list(call):
    bot_username = bot.get_me().username
    
    text = (
        "📋 <b>Присоединяйся в наш чат и канал</b>\n\n"
        
        "🏠 <b>Наш канал и чат </b>\n"
        f"• <a href='https://t.me/meowchatgame'>Игровой чат</a> - основной чат\n"
        f"• <a href='https://t.me/MeowGameNews'>Канал бота</a> - канал с новостями и изменениями в боте\n"
        
        f"🔗 <b>Добавить бота в свой чат:</b>\n"
        f"<a href='https://t.me/{bot_username}?startgroup=true'>Нажми сюда</a>\n\n"
        
        "<i>💫 Бот работает в любых группах и чатах!</i>"
    )
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ Добавить бота в чат", url=f"https://t.me/{bot_username}?startgroup=true"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start"))

    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=kb
        )
    except:
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=kb
        )

# ================== CALLBACK: НАЗАД К СТАРТУ ==================

@bot.callback_query_handler(func=lambda c: c.data == "back_to_start")
def back_to_start(call):
    user_id = call.from_user.id
    bot_username = bot.get_me().username
    add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"
    
    mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
    
    welcome_text = (
        f"Привет {mention}, я игровой чат бот, для того чтобы узнать обо мне по больше, "
        f"напиши команду /help или <code>помощь</code>. "
        f"Если хочешь добавить меня в свой чат, <a href='{add_to_group_url}'>нажми сюда</a> "
    )

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📋 Список групп для бота", callback_data="show_group_list"))

    try:
        bot.edit_message_text(
            welcome_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=kb
        )
    except:
        bot.send_message(
            call.message.chat.id,
            welcome_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=kb
        )
        
@bot.message_handler(commands=["dkskxlp"])
def cmd_help(message):
    user = message.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    text = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "📖 <b>Панель помощи MEOW Bot</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Пользователь: {mention}\n"
        f"🆔 Твой ID: <code>{user.id}</code>\n\n"
        "✨ Здесь ты можешь узнать всё о функциях бота:\n"
        "— Команды 💬\n"
        "— Випы 💎\n"
        "— Игры 🎮\n"
        "— Тянки 💞\n"
        "— Питомцы 🐾\n"
        "— Донат 💰\n\n"
        "━━━━━━━━━━━━━━━━━━━"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💬 Команды", callback_data="help_commands"),
        InlineKeyboardButton("🎮 Игры", callback_data="help_games")
    )
    kb.add(
        InlineKeyboardButton("💎 Випы", callback_data="help_vip"),
        InlineKeyboardButton("💞 Тянки", callback_data="help_tyanki")
    )
    kb.add(
        InlineKeyboardButton("🐾 Питомцы", callback_data="help_pets"),
        InlineKeyboardButton("💍 Брак", callback_data="help_marriage")
    )
    kb.add(
        InlineKeyboardButton("❄️ Снежок", callback_data="help_snow"),
        InlineKeyboardButton("💰 Донат", callback_data="help_donate")
    )
    kb.add(
        InlineKeyboardButton("🆘 Support", callback_data="help_support"),
        InlineKeyboardButton("📢 Наш канал", url="https://t.me/MeowGameNews")
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb,
        parse_mode="HTML"
    )
    
    # УДАЛИТЕ эту строку (второй вызов bot.send_message):
    # bot.send_message(message.chat.id, help_text, parse_mode="HTML")
# Ограничения экономики
MAX_DAILY_INCOME = 10000000000000000000000  # Максимум в день с пассивных источников
MAX_BALANCE = 1000000000000000000000000000000   # Абсолютный максимум баланса
TRANSFER_DAILY_LIMIT = 100000000  # Лимит на переводы в день
TRANSFER_FEE = 0.1  # Комиссия 10% на переводы

# Данные тянок (5 штук)
TYANKA_DATA = {
    # Старые тянки
    "катя": {"price": 60000, "profit_per_hour": 600, "image": "https://cdna.artstation.com/p/assets/images/images/019/314/290/large/syahrul-eka-935136.jpg?1562928035", "rarity": "⚪ Обычная", "feed_cost": 120},
    "соня": {"price": 100000, "profit_per_hour": 1000, "image": "https://i.ytimg.com/vi/TK0SVAPAw0U/maxresdefault.jpg?sqp=-oaymwEmCIAKENAF8quKqQMa8AEB-AH-DoACuAiKAgwIABABGBYgLSh_MA8=&rs=AOn4CLBMsae4GYTK1xHOwy95T0zBCXuWqQ", "rarity": "🟢 Средняя", "feed_cost": 200},
    "айсель": {"price": 300000, "profit_per_hour": 1500, "image": "https://i.ytimg.com/vi/-BTpCnN2-bQ/maxresdefault.jpg", "rarity": "🟣 Мифическая", "feed_cost": 100},
    "эля": {"price": 1000000, "profit_per_hour": 2000, "image": "https://avatars.mds.yandex.net/i?id=bfb20e2218dfae1a2e5b571f0ad7764b_l-4255243-images-thumbs&n=33&w=1279&h=720", "rarity": "🟡 Легендарная", "feed_cost": 300},
    "даша": {"price": 2500000, "profit_per_hour": 3500, "image": "https://avatars.mds.yandex.net/i?id=38673228b026971e8913e31fd40c5644_l-7992926-images-thumbs&n=13", "rarity": "🟡 Сверх Легендарная", "feed_cost": 300},

    # Новые тянки (стоимость >10 млн)
    "ангелина": {"price": 15000000, "profit_per_hour": 8000, "image": "https://avatars.mds.yandex.net/i?id=a771344e740c281a424adb04fcf1f8cb_l-9854613-images-thumbs&n=33&w=960&h=720", "rarity": "🔥 Божественная", "feed_cost": 800},
    "виктория": {"price": 30000000, "profit_per_hour": 15000, "image": "https://avatars.mds.yandex.net/i?id=c90c4c1ed3daba7c1f5914c08c4fb832_l-5288402-images-thumbs&n=13", "rarity": "🌈 Небесная", "feed_cost": 1200},
    "миранда": {"price": 50000000, "profit_per_hour": 25000, "image": "https://i.ytimg.com/vi/NcJGC8xAeO0/maxresdefault.jpg", "rarity": "💎 Алмазная", "feed_cost": 1500},
    "сатори": {"price": 100000000, "profit_per_hour": 40000, "image": "https://avatars.mds.yandex.net/i?id=c3c3f2ba908a0204176d02840a076014_l-4012489-images-thumbs&n=33&w=1016&h=720", "rarity": "🌌 Космическая", "feed_cost": 2000},
    "изабелла": {"price": 250000000, "profit_per_hour": 75000, "image": "https://i.pinimg.com/736x/6e/05/76/6e0576744cb793202908355bc748b00a.jpg", "rarity": "👑 Императорская", "feed_cost": 3000},
    "хельга": {"price": 500000000, "profit_per_hour": 125000, "image": "https://i.ytimg.com/vi/ePP9WITZxtM/maxresdefault.jpg", "rarity": "✨ Вечная", "feed_cost": 5000},
}


# Данные бизнесов (10 штук)
BUSINESS_DATA = {
    "магазин оружия": {"price": 100000, "profit_per_hour": 500, "image": "https://avatars.mds.yandex.net/i?id=5b8d6645275b05fec658b4685140b5a80744085a-5602402-images-thumbs&n=13", "material_cost": 50, "material_units": 100},
    "ночной клуб": {"price": 200000, "profit_per_hour": 1250, "image": "https://avatars.mds.yandex.net/i?id=e57c40498724bb7d6d279d69690c187402305de2-16187200-images-thumbs&n=13", "material_cost": 100, "material_units": 100},
    "ресторан": {"price": 300000, "profit_per_hour": 2000, "image": "https://avatars.mds.yandex.net/i?id=0b7f983489b1eff7714485591319ce17_l-5443655-images-thumbs&n=33&w=960&h=524", "material_cost": 300, "material_units": 100},
    "автосалон": {"price": 600000, "profit_per_hour": 5000, "image": "https://avatars.mds.yandex.net/i?id=73a269d06a8062b5381bfb9a306aff5d219c105a-4136742-images-thumbs&n=13", "material_cost": 500, "material_units": 100},
    "отель": {"price": 2000000, "profit_per_hour": 10000, "image": "https://i.pinimg.com/originals/11/55/a0/1155a0328ae73020846a5f6d3e4eedbd.jpg", "material_cost": 1000, "material_units": 100}
}


# ================== ДАННЫЕ ДОМОВ (5 ШТУК) ==================
HOUSE_DATA = {
    "Хижина": {
        "price": 2000000,  # 2 млн
        "profit_per_hour": 500,  # 500$/час
        "upkeep_cost": 2000,  # 10к/день
        "image": "https://png.pngtree.com/background/20230516/original/pngtree-ancient-thatched-huts-in-a-forest-picture-image_2611775.jpg"
    },
    "Коттедж": {
        "price": 5000000,  # 5 млн
        "profit_per_hour": 1200,  # 1.2к/час
        "upkeep_cost": 5000,  # 25к/день
        "image": "https://pic.rutubelist.ru/video/2024-12-12/fb/9e/fb9e3caca7807585073e47c12be4c0c6.jpg"
    },
    "Вилла": {
        "price": 10000000,  # 10 млн
        "profit_per_hour": 2500,  # 2.5к/час
        "upkeep_cost": 10000,  # 50к/день
        "image": "https://img.freepik.com/premium-photo/contemporary-villa-with-pool-garden-sleek-design_1270611-8380.jpg?semt=ais_hybrid"
    },
    "Особняк": {
        "price": 25000000,  # 25 млн
        "profit_per_hour": 6000,  # 6к/час
        "upkeep_cost": 20000,  # 120к/день
        "image": "https://i.pinimg.com/736x/46/f9/a4/46f9a4c8705a5763d59912e2d82b337c.jpg"
    },
    "Дворец": {
        "price": 50000000,  # 50 млн
        "profit_per_hour": 12000,  # 12к/час
        "upkeep_cost": 30000,  # 250к/день
        "image": "https://img.goodfon.com/wallpaper/nbig/b/c1/enchanted-castle-ancient-gloomy-fairytale-zamok-skazochnyi-2.webp"
    }
}

# Данные машин (9 штук)
CAR_DATA = {
    "Zhiguli": {
        "price": 50000,
        "profit_per_hour": 200,
        "image": "https://avatars.mds.yandex.net/i?id=321f5469a7649d65f9be8e1e8dbbb8a4_l-12486332-images-thumbs&n=33&w=1280&h=720",  # Замените на реальную ссылку
        "upkeep_cost": 20
    },
    "Tesla": {
        "price": 100000,
        "profit_per_hour": 300,
        "image": "https://i.pinimg.com/736x/a8/be/df/a8bedf61f982bdf5614c79ff8a658e67.jpg",
        "upkeep_cost": 50
    },
    "Toyota Camry 3.5": {
        "price": 350000,
        "profit_per_hour": 600,
        "image": "https://avatars.yandex.net/get-music-content/14270105/c0e2d3f4.a.36766958-1/m1000x1000",
        "upkeep_cost": 100
    },
    "Lexus": {
        "price": 800000,
        "profit_per_hour": 900,
        "image": "https://carsweek.ru/upload/medialibrary/7cb/7cb01468d2623b3691d408bc36335bd0.jpg",  # Замените на реальную ссылку
        "upkeep_cost": 150
    },
    "Audi": {
        "price": 1200000,
        "profit_per_hour": 1100,
        "image": "https://avatars.mds.yandex.net/i?id=39a501a19248fa5c57c2e1772baecf30_l-5710176-images-thumbs&n=13",
        "upkeep_cost": 180
    },
    "Bmw M8": {
        "price": 1500000,
        "profit_per_hour": 1300,
        "image": "https://avatars.mds.yandex.net/i?id=7531fa35c137db91df18107ecf47ddb8_l-5234178-images-thumbs&n=13",
        "upkeep_cost": 200
    },
    "Mercedes G63": {
        "price": 3000000,
        "profit_per_hour": 2500,
        "image": "https://avatars.mds.yandex.net/i?id=168522fc4baeb489f9881bdf32eea6678cd9777b-3717621-images-thumbs&n=13",
        "upkeep_cost": 400
    },
    "Toyota Land Cruiser 300": {
        "price": 3500000,
        "profit_per_hour": 2800,
        "image": "https://a.d-cd.net/gggEUIqvkTy-EMvt5A6cNUZ1EG8-1920.jpg",  # Замените на реальную ссылку
        "upkeep_cost": 450
    },
    "Mercedes Maybach": {
        "price": 5000000,
        "profit_per_hour": 4000,
        "image": "https://i.ytimg.com/vi/9zIz78K0ZWU/maxresdefault.jpg",
        "upkeep_cost": 600
    }
}

# ================== ПИТОМЦЫ (SQLite) - ПОЛНАЯ ВЕРСИЯ С ИГРАМИ ==================
PETS_DB = "pets.db"

# Создание таблицы питомцев
conn = sqlite3.connect(PETS_DB)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS pets (
    user_id INTEGER PRIMARY KEY,
    pet_id INTEGER,
    name TEXT,
    price INTEGER,
    satiety INTEGER,
    level INTEGER,
    xp INTEGER,
    last_update TEXT
)
""")
conn.commit()
conn.close()

# --- Редкость питомцев ---
PET_RARITY = {
    1: {"name": "Обычный", "emoji": "⚪", "multiplier": 1.0},
    2: {"name": "Редкий", "emoji": "🔵", "multiplier": 1.5},
    3: {"name": "Эпический", "emoji": "🟣", "multiplier": 2.0},
    4: {"name": "Легендарный", "emoji": "🟡", "multiplier": 3.0},
    5: {"name": "Мифический", "emoji": "🔴", "multiplier": 5.0}
}

# --- данные питомцев ---
PETS_DATA = {
    1: {"name": "Кошка", "price": 10000, "rarity": 1, "image": "https://avatars.mds.yandex.net/i?id=c3a3713878f9e67805276d4888894aea-5295832-images-thumbs&n=33&w=960&h=540"},
    2: {"name": "Собака", "price": 20000, "rarity": 1, "image": "https://avatars.mds.yandex.net/i?id=44a36b708a553d9d214e3396c11cc748_l-4809743-images-thumbs&n=33&w=1152&h=720"},
    3: {"name": "Попугай", "price": 50000, "rarity": 2, "image": "https://cdn1.youla.io/files/images/780_780/68/52/68527f7e44e4570a840da59a-2.jpg"},
    4: {"name": "Кролик", "price": 100000, "rarity": 2, "image": "https://i.pinimg.com/originals/83/c8/43/83c843f5f61089cecd64bddb8a8274ae.jpg"},
    5: {"name": "Коровка", "price": 250000, "rarity": 3, "image": "https://i.pinimg.com/736x/16/8d/63/168d634e6abeb738eb8e3b016d9d2d11.jpg"},
    6: {"name": "Хомяк", "price": 5000, "rarity": 1, "image": "https://i.pinimg.com/736x/01/72/e3/0172e3d52de4ff28241e7ce6eae6d4a1.jpg"},
    7: {"name": "Лошадь", "price": 100000, "rarity": 3, "image": "https://agrobook.ru/sites/default/files/20-09/blog/2560x1706_765016_www.artfile.ru_.jpg"},
    8: {"name": "Фенек", "price": 150000, "rarity": 4, "image": "https://avatars.mds.yandex.net/i?id=69b9f5f9b41b507ced6f50e2699bd513_l-13313278-images-thumbs&n=13"},
    9: {"name": "Дракон", "price": 500000, "rarity": 5, "image": "https://img.freepik.com/free-photo/3d-rendering-cute-cartoon-dragon_23-2151701949.jpg?semt=ais_hybrid&w=740"},
    10: {"name": "Феникс", "price": 750000, "rarity": 5, "image": "https://avatars.mds.yandex.net/i?id=f3b1d9d2706912bb4a8bdfdad10c62a3_l-5467799-images-thumbs&n=33&w=1280&h=720"}
}

# --- Мини-игры ---
PET_GAMES = {
    "ball": {"name": "🎾 Игра в мяч", "xp_min": 15, "xp_max": 30, "cost": 0, "description": "Простая игра с мячиком"},
    "race": {"name": "🏃 Бег наперегонки", "xp_min": 25, "xp_max": 40, "cost": 500, "description": "Соревнование в скорости"},
    "puzzle": {"name": "🧩 Головоломка", "xp_min": 35, "xp_max": 50, "cost": 1000, "description": "Развивающая игра для ума"},
    "treasure": {"name": "💰 Поиск сокровищ", "xp_min": 45, "xp_max": 60, "cost": 2000, "description": "Приключение с наградой"}
}

# --- Визуальные индикаторы уровня ---
def get_level_emoji(level):
    if level < 5:
        return "🐣"
    elif level < 10:
        return "🐥"
    elif level < 20:
        return "🐶"
    elif level < 30:
        return "🐺"
    elif level < 40:
        return "🦁"
    elif level < 50:
        return "🐉"
    else:
        return "👑"

def get_level_title(level):
    if level < 5:
        return "Новичок"
    elif level < 10:
        return "Ученик"
    elif level < 20:
        return "Опытный"
    elif level < 30:
        return "Сильный"
    elif level < 40:
        return "Мастер"
    elif level < 50:
        return "Легенда"
    else:
        return "Бог"

# --- Работа с базой ---
def get_pet(user_id):
    conn = sqlite3.connect(PETS_DB)
    c = conn.cursor()
    c.execute("SELECT pet_id, name, price, satiety, level, xp, last_update FROM pets WHERE user_id = ?", (user_id,))
    pet = c.fetchone()
    conn.close()
    return pet

def set_pet(user_id, pet_id, name, price):
    conn = sqlite3.connect(PETS_DB)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("""
        INSERT OR REPLACE INTO pets (user_id, pet_id, name, price, satiety, level, xp, last_update)
        VALUES (?, ?, ?, ?, 100, 1, 0, ?)
    """, (user_id, pet_id, name, price, now))
    conn.commit()
    conn.close()

def delete_pet(user_id):
    conn = sqlite3.connect(PETS_DB)
    c = conn.cursor()
    c.execute("DELETE FROM pets WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_pet(user_id, satiety=None, level=None, xp=None):
    conn = sqlite3.connect(PETS_DB)
    c = conn.cursor()
    now = datetime.now().isoformat()
    fields = []
    values = []
    if satiety is not None:
        fields.append("satiety = ?")
        values.append(satiety)
    if level is not None:
        fields.append("level = ?")
        values.append(level)
    if xp is not None:
        fields.append("xp = ?")
        values.append(xp)
    fields.append("last_update = ?")
    values.append(now)
    values.append(user_id)
    c.execute(f"UPDATE pets SET {', '.join(fields)} WHERE user_id = ?", tuple(values))
    conn.commit()
    conn.close()

def update_pet_stats(user_id):
    pet = get_pet(user_id)
    if not pet:
        return
    pet_id, name, price, satiety, level, xp, last_update = pet
    last_update = datetime.fromisoformat(last_update)
    now = datetime.now()
    hours_passed = int((now - last_update).total_seconds() // 3600)
    if hours_passed <= 0:
        return
    loss = sum(random.randint(1, 3) for _ in range(hours_passed))
    satiety = max(0, satiety - loss)
    update_pet(user_id, satiety=satiety)
    if satiety <= 0:
        delete_pet(user_id)

# --- Команды ---
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["магазин питомцев", "питомцы"])
def pet_shop(message):
    text = "🐾 <b>Магазин питомцев</b> 🐾\n\n"
    for idx, info in PETS_DATA.items():
        rarity_info = PET_RARITY[info['rarity']]
        text += f"{rarity_info['emoji']} <b>{idx}️⃣ {info['name']}</b> — <code>{format_number(info['price'])} izzzy</code>\n"
        text += f"   └─ Редкость: <i>{rarity_info['name']}</i>\n\n"
    
    text += "\n🟢 Команда для покупки питомца:\n<code>Купить питомца (номер)</code>\nПример: <code>Купить питомца 1</code>"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить питомца"))
def buy_pet(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        # Проверяем, есть ли уже питомец
        if get_pet(user_id):
            bot.send_message(message.chat.id, "❌ У вас уже есть питомец!")
            return

        parts = message.text.split()
        if len(parts) < 3 or not parts[-1].isdigit():
            bot.send_message(message.chat.id, "❌ Укажите номер питомца!")
            return
            
        num = int(parts[-1])
        if num not in PETS_DATA:
            bot.send_message(message.chat.id, "❌ Неверный номер питомца!")
            return

        pet_info = PETS_DATA[num]
        if user_data["balance"] < pet_info["price"]:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            return

        # Списание денег и сохранение
        user_data["balance"] -= pet_info["price"]
        save_casino_data()  # ⬅️ ДОБАВЬТЕ ЭТУ СТРОЧКУ
        
        # Создание питомца
        set_pet(user_id, num, pet_info["name"], pet_info["price"])
        
        rarity_info = PET_RARITY[pet_info['rarity']]
        bot.send_message(
            message.chat.id,
            f"🎉 {rarity_info['emoji']} <b>Поздравляем!</b>\n"
            f"Вы купили <b>{pet_info['name']}</b> за <code>{format_number(pet_info['price'])} izzzy</code>\n"
            f"Редкость: <i>{rarity_info['name']}</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка покупки питомца: {e}")
        bot.send_message(message.chat.id, "⚠️ Ошибка при покупке питомца!")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой питомец", "мое животное", "мой пет"])
def my_pet(message):
    try:
        user_id = message.from_user.id
        update_pet_stats(user_id)
        pet = get_pet(user_id)
        if not pet:
            bot.send_message(message.chat.id, "🐾 У вас нет питомца! Купите его в магазине.")
            return

        pet_id, name, price, satiety, level, xp, last_update = pet
        pet_info = PETS_DATA.get(pet_id, {})
        rarity_info = PET_RARITY.get(pet_info.get('rarity', 1), PET_RARITY[1])
        
        level_emoji = get_level_emoji(level)
        level_title = get_level_title(level)

        mention = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        text = (
            f"{level_emoji} <b>Питомец {mention}</b>\n\n"
            f"{rarity_info['emoji']} <b>{name}</b> | Ур. {level} ({level_title})\n"
            f"💰 Стоимость: <code>{format_number(price)} izzzy</code>\n"
            f"🍪 Сытость: <b>{satiety}%</b>\n"
            f"⭐ Опыт: <b>{xp}/100</b>\n"
            f"🎯 Редкость: <i>{rarity_info['name']}</i>"
        )

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🍪 Накормить", callback_data=f"feed_{user_id}"),
            InlineKeyboardButton("🎮 Игры", callback_data=f"games_{user_id}")
        )
        kb.add(InlineKeyboardButton("💰 Продать питомца", callback_data=f"sell_{user_id}"))

        if pet_info.get("image"):
            bot.send_photo(message.chat.id, pet_info["image"], caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.error(f"Ошибка отображения питомца: {e}")
        bot.send_message(message.chat.id, "⚠️ Ошибка при показе питомца!")

# --- Обработчики кнопок с полной защитой ---
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("feed_"))
def feed_pet(call):
    try:
        action, owner_id = call.data.split("_")
        owner_id = int(owner_id)
        
        # Проверка владельца
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не ваш питомец!", show_alert=True)
            return

        user_data = get_user_data(owner_id)
        pet = get_pet(owner_id)
        if not pet:
            bot.answer_callback_query(call.id, "❌ У вас нет питомца!", show_alert=True)
            return

        pet_id, name, price, satiety, level, xp, _ = pet
        
        # Проверка сытости
        if satiety >= 100:
            bot.answer_callback_query(call.id, "❌ Ваш питомец уже сыт!", show_alert=True)
            return

        cost = random.randint(500, 1500)
        if user_data["balance"] < cost:
            bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {format_number(cost)} izzzy", show_alert=True)
            return

        # Кормление
        user_data["balance"] -= cost
        satiety = 100
        update_pet(owner_id, satiety=satiety)
        
        # Обновление сообщения
        pet_info = PETS_DATA.get(pet_id, {})
        rarity_info = PET_RARITY.get(pet_info.get('rarity', 1), PET_RARITY[1])
        level_emoji = get_level_emoji(level)
        level_title = get_level_title(level)
        
        text = (
            f"{level_emoji} <b>Питомец обновлен!</b>\n\n"
            f"{rarity_info['emoji']} <b>{name}</b> | Ур. {level} ({level_title})\n"
            f"💰 Стоимость: <code>{format_number(price)} izzzy</code>\n"
            f"🍪 Сытость: <b>{satiety}%</b> ✅\n"
            f"⭐ Опыт: <b>{xp}/100</b>\n"
            f"🎯 Редкость: <i>{rarity_info['name']}</i>\n\n"
            f"💸 Потрачено на еду: <code>{format_number(cost)} izzzy</code>"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🍪 Накормить", callback_data=f"feed_{owner_id}"),
            InlineKeyboardButton("🎮 Игры", callback_data=f"games_{owner_id}")
        )
        kb.add(InlineKeyboardButton("💰 Продать питомца", callback_data=f"sell_{owner_id}"))

        if pet_info.get("image"):
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        
        bot.answer_callback_query(call.id, f"🍪 Питомец накормлен! -{format_number(cost)} izzzy")

    except Exception as e:
        logger.error(f"Ошибка кормления питомца: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при кормлении!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("games_"))
def show_games(call):
    try:
        action, owner_id = call.data.split("_")
        owner_id = int(owner_id)
        
        # Проверка владельца
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не ваш питомец!", show_alert=True)
            return

        pet = get_pet(owner_id)
        if not pet:
            bot.answer_callback_query(call.id, "❌ У вас нет питомца!", show_alert=True)
            return

        pet_id, name, price, satiety, level, xp, _ = pet
        
        text = f"🎮 <b>Выберите игру для {name}</b>\n\n"
        
        kb = InlineKeyboardMarkup(row_width=1)
        for game_id, game_info in PET_GAMES.items():
            cost_text = f" - {format_number(game_info['cost'])} izzzy" if game_info['cost'] > 0 else " - Бесплатно"
            kb.add(InlineKeyboardButton(
                f"{game_info['name']}{cost_text}", 
                callback_data=f"play_{owner_id}_{game_id}"
            ))
        
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_{owner_id}"))

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка показа игр: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("play_"))
def play_game(call):
    try:
        parts = call.data.split("_")
        owner_id = int(parts[1])
        game_id = parts[2]
        
        # Проверка владельца
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не ваш питомец!", show_alert=True)
            return

        user_data = get_user_data(owner_id)
        pet = get_pet(owner_id)
        if not pet:
            bot.answer_callback_query(call.id, "❌ У вас нет питомца!", show_alert=True)
            return

        pet_id, name, price, satiety, level, xp, _ = pet
        game_info = PET_GAMES.get(game_id)
        
        if not game_info:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return

        # Проверка стоимости игры
        if user_data["balance"] < game_info["cost"]:
            bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {format_number(game_info['cost'])} izzzy", show_alert=True)
            return

        # Проверка сытости
        if satiety <= 20:
            bot.answer_callback_query(call.id, "❌ Питомец слишком голоден для игр! Сначала покормите его.", show_alert=True)
            return

        # Списание стоимости игры
        if game_info["cost"] > 0:
            user_data["balance"] -= game_info["cost"]

        # Играем и получаем XP
        earned_xp = random.randint(game_info["xp_min"], game_info["xp_max"])
        xp += earned_xp
        
        level_up = False
        new_level = level
        if xp >= 100:
            xp = xp - 100
            new_level = level + 1
            level_up = True

        update_pet(owner_id, xp=xp, level=new_level)

        # Обновление сообщения
        pet_info = PETS_DATA.get(pet_id, {})
        rarity_info = PET_RARITY.get(pet_info.get('rarity', 1), PET_RARITY[1])
        level_emoji = get_level_emoji(new_level)
        level_title = get_level_title(new_level)
        
        text = (
            f"{level_emoji} <b>Результаты игры</b>\n\n"
            f"🎮 Игра: <b>{game_info['name']}</b>\n"
            f"📈 Получено опыта: <b>+{earned_xp} XP</b>\n"
        )
        
        if level_up:
            text += f"🎉 <b>ПОЗДРАВЛЯЕМ! {name} достиг {new_level} уровня!</b>\n\n"
        else:
            text += f"⭐ До следующего уровня: <b>{100 - xp} XP</b>\n\n"
            
        text += (
            f"{rarity_info['emoji']} <b>{name}</b> | Ур. {new_level} ({level_title})\n"
            f"🍪 Сытость: <b>{satiety}%</b>\n"
            f"⭐ Опыт: <b>{xp}/100</b>\n"
        )
        
        if game_info["cost"] > 0:
            text += f"💸 Стоимость игры: <code>{format_number(game_info['cost'])} izzzy</code>"

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🍪 Накормить", callback_data=f"feed_{owner_id}"),
            InlineKeyboardButton("🎮 Игры", callback_data=f"games_{owner_id}")
        )
        kb.add(InlineKeyboardButton("💰 Продать питомца", callback_data=f"sell_{owner_id}"))

        if pet_info.get("image"):
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        
        if level_up:
            bot.answer_callback_query(call.id, f"🎉 Уровень повышен до {new_level}!")
        else:
            bot.answer_callback_query(call.id, f"🎮 +{earned_xp} XP за игру!")

    except Exception as e:
        logger.error(f"Ошибка в игре: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка в игре!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("sell_"))
def sell_pet(call):
    try:
        action, owner_id = call.data.split("_")
        owner_id = int(owner_id)
        
        # Проверка владельца
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не ваш питомец!", show_alert=True)
            return

        user_data = get_user_data(owner_id)
        pet = get_pet(owner_id)
        if not pet:
            bot.answer_callback_query(call.id, "❌ У вас нет питомца!", show_alert=True)
            return

        pet_id, name, price, satiety, level, xp, _ = pet
        
        refund = price // 2
        user_data["balance"] += refund
        delete_pet(owner_id)
        
        # СОХРАНЕНИЕ ДАННЫХ ПОСЛЕ ИЗМЕНЕНИЯ БАЛАНСА
        save_casino_data()  # ⬅️ ВАЖНО: сохраняем изменения

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"💸 <b>Питомец продан!</b>\n\nВы продали <b>{name}</b> и получили <code>{format_number(refund)} izzzy</code>\n💰 Новый баланс: <code>{format_number(user_data['balance'])} izzzy</code>",
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, f"✅ {name} продан за {format_number(refund)} izzzy")

    except Exception as e:
        logger.error(f"Ошибка продажи питомца: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при продаже!", show_alert=True)


# ================== ДАННЫЕ КАЗИНО ==================
if os.path.exists(CASINO_DATA_FILE):
    with open(CASINO_DATA_FILE, "r", encoding="utf-8") as f:
        casino_data = json.load(f)
else:
    casino_data = {}

if os.path.exists(PROMO_CODES_FILE):
    with open(PROMO_CODES_FILE, "r", encoding="utf-8") as f:
        promocodes = json.load(f)
else:
    promocodes = {}

if os.path.exists(WARNS_FILE):
    with open(WARNS_FILE, "r", encoding="utf-8") as f:
        warns_data = json.load(f)
else:
    warns_data = {}

# Конфигурация бота
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
else:
    config = {
        "max_daily_income": MAX_DAILY_INCOME,
        "max_balance": MAX_BALANCE,
        "transfer_daily_limit": TRANSFER_DAILY_LIMIT,
        "transfer_fee": TRANSFER_FEE,
        "bank_interest_rate": 0.001,  # 0.1% в день
        "blackjack_win_multiplier": 2,
        "roulette_win_multiplier": 2,
        "mines_multiplier_increment": 0.5,
        "coin_flip_multiplier": 2,
        "mines_cells": 30,
        "mines_count": 5
    }

# Бэкап данных
casino_data_backup = deepcopy(casino_data)

def save_casino_data():
    with open(CASINO_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(casino_data, f, ensure_ascii=False, indent=2)

def save_promocodes():
    with open(PROMO_CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(promocodes, f, ensure_ascii=False, indent=2)

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def save_warns():
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(warns_data, f, ensure_ascii=False, indent=2)

def format_number(number):
    """Форматирует число с разделителями тысяч"""
    return f"{number:,}".replace(",", ".")

def get_user_data(user_id):
    user_id_str = str(user_id)
    if user_id_str not in casino_data:
        casino_data[user_id_str] = {
            "balance": START_BALANCE,
            "last_bonus": None,
            "stage": None,
            "game": None,
            "tyanka": None,
            "business": None,
            "house": None,
            "car": None,
            "pet": None,
            "activated_promos": [],
            "daily_income": {"date": date.today().isoformat(), "amount": 0},
            "daily_transfers": {"date": date.today().isoformat(), "amount": 0},
            "bank_balance": 0,
            "last_interest_date": date.today().isoformat(),
            "vip": {"level": 0, "expires": None}
        }
    else:
        user_data = casino_data[user_id_str]

        if "business" not in user_data:
            user_data["business"] = None
        if "house" not in user_data:
            user_data["house"] = None
        if "car" not in user_data:
            user_data["car"] = None
        if "tyanka" not in user_data:
            user_data["tyanka"] = None
        if "pet" not in user_data:
            user_data["pet"] = None
        if "activated_promos" not in user_data:
            user_data["activated_promos"] = []
        if "daily_income" not in user_data:
            user_data["daily_income"] = {"date": date.today().isoformat(), "amount": 0}
        if "daily_transfers" not in user_data:
            user_data["daily_transfers"] = {"date": date.today().isoformat(), "amount": 0}
        if "bank_balance" not in user_data:
            user_data["bank_balance"] = 0
        if "last_interest_date" not in user_data:
            user_data["last_interest_date"] = date.today().isoformat()
        if "vip" not in user_data:
            user_data["vip"] = {"level": 0, "expires": None}

        # Сброс дневных лимитов если дата изменилась
        today = date.today().isoformat()
        if user_data["daily_income"]["date"] != today:
            user_data["daily_income"] = {"date": today, "amount": 0}
        if user_data["daily_transfers"]["date"] != today:
            user_data["daily_transfers"] = {"date": today, "amount": 0}

    # Добавляем ID пользователя для удобства
    casino_data[user_id_str]["_user_id"] = user_id

    # Гарантируем возврат словаря (никогда не None)
    return casino_data.get(user_id_str, {})

# ================== ПРОСТЫЕ ФУНКЦИИ БЕЗ CONFIG ==================
def check_income_limits(user_id, amount):
    """Всегда возвращаем полную сумму"""
    return amount

def add_income(user_id, amount, source="other"):
    """Просто добавляем деньги"""
    user_data = get_user_data(user_id)
    user_data["balance"] += amount
    save_casino_data()
    logger.info(f"Начислен доход {amount}$ пользователю {user_id} из источника {source}")
    return amount

def apply_transfer_limits(sender_id, amount):
    """Фиксированная комиссия 10%"""
    fee = int(amount * 0.1)  # 10% комиссия
    net_amount = amount - fee
    logger.info(f"Перевод от {sender_id}: сумма {amount}$, комиссия {fee}$, чистая {net_amount}$")
    return net_amount, fee

import random
import time
import uuid
import sqlite3
from datetime import datetime

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== КАРТЫ ДЛЯ БЛЭКДЖЕКА ==================
suits = ["♠️", "♥️", "♦️", "♣️"]
ranks = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

def new_deck():
    deck = [(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)
    return deck

def hand_value(hand):
    value = sum(ranks[card[0]] for card in hand)
    aces = sum(1 for card in hand if card[0] == "A")
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    return value

def format_hand(hand, hide_second=False):
    if hide_second and len(hand) > 1:
        return f"{hand[0][0]}{hand[0][1]} ❓"
    return " • ".join(f"{r}{s}" for r, s in hand)

# ================== КЛАВИАТУРА ==================
def bj_action_keyboard(user_id, game_id, can_double=True):
    kb = InlineKeyboardMarkup(row_width=1)  # Вертикальное расположение
    
    # Каждую кнопку добавляем отдельно
    kb.add(InlineKeyboardButton("🎯 Взять", callback_data=f"bj_hit_{user_id}_{game_id}"))
    kb.add(InlineKeyboardButton("🛑 Оставить", callback_data=f"bj_stand_{user_id}_{game_id}"))
    kb.add(InlineKeyboardButton("🏳️ Сдаться", callback_data=f"bj_surrender_{user_id}_{game_id}"))
    
    if can_double:
        kb.add(InlineKeyboardButton("💹 Удвоить", callback_data=f"bj_double_{user_id}_{game_id}"))
    
    return kb

# ================== АКТИВНЫЕ ИГРЫ ==================
active_blackjack_games = {}
BLACKJACK_IMAGE_URL = "https://i.supaimg.com/d55f9fad-17e9-4723-8cd8-4258944b667f/fc07259f-695e-4d75-a365-2e76cca30464.png"

# ================== СТАРТ ИГРЫ ==================
def start_blackjack_game(user_data, user_id, bet):
    # Проверки
    if bet < 100:
        return None, "❌ Минимальная ставка 100 izzzy"

    if user_data["balance"] < bet:
        return None, "❌ Недостаточно средств!"

    deck = new_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    game_id = str(uuid.uuid4())[:8]

    active_blackjack_games[game_id] = {
        "user_id": user_id,
        "bet": bet,
        "deck": deck,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "player_value": hand_value(player_hand),
        "dealer_value": hand_value([dealer_hand[0]]),
        "status": "playing",
        "start_time": time.time()
    }

    # СПИСЫВАЕМ СТАВКУ
    user_data["balance"] -= bet
    save_casino_data()

    return game_id, "OK"

# ================== КРАСИВОЕ СООБЩЕНИЕ ==================
def format_blackjack_message(game_id):
    game = active_blackjack_games[game_id]
    uid = game["user_id"]

    try:
        user = bot.get_chat(uid)
        name = user.first_name
    except:
        name = str(uid)
    
    mention = f'<a href="tg://user?id={uid}">{name}</a>'
    
    # Символ масти для заголовка
    suit_symbol = random.choice(["♣️", "♠️", "♥️", "♦️"])
    
    # Статус игры
    status_emoji = {
        "playing": "🎮",
        "blackjack": "🎯",
        "bust": "💥",
        "win": "✅",
        "lose": "❌",
        "push": "🤝",
        "surrender": "🏳️"
    }
    
    status_text = {
        "playing": "Твой ход",
        "blackjack": "BLACKJACK!",
        "bust": "ПЕРЕБОР",
        "win": "Ты победил!",
        "lose": "Ты проиграл",
        "push": "Ничья",
        "surrender": "Сдача"
    }
    
    emoji = status_emoji.get(game["status"], "🎮")
    status = status_text.get(game["status"], "")
    
    # Формируем текст
    text = f"{suit_symbol} <b>{mention}, {status}</b> {emoji}\n"
    text += "·····················\n"
    text += f"💶 Ставка: {format_number(game['bet'])} \n"
    
    # Выигрыш
    if game["status"] == "win":
        win_amount = game['bet'] * 2
        text += f"📊 Выигрыш: {format_number(win_amount)} izzzy\n"
    elif game["status"] == "blackjack":
        win_amount = int(game['bet'] * 2.5)
        text += f"📊 Выигрыш: {format_number(win_amount)} izzzy 🎯\n"
    elif game["status"] == "push":
        text += f"📊 Возврат: {format_number(game['bet'])} izzzy\n"
    elif game["status"] == "surrender":
        text += f"📊 Возврат: {format_number(game['bet']//2)} izzzy\n"
    else:
        text += f"📊 Выигрыш: —\n"
    
    text += "\n"
    
    # Дилер
    if game["status"] == "playing":
        dealer_cards = format_hand(game['dealer_hand'], hide_second=True)
        dealer_score = hand_value([game['dealer_hand'][0]])
        text += f"🤵 <b>Дилер:</b>\n{dealer_cards} | {dealer_score}\n"
    else:
        dealer_cards = format_hand(game['dealer_hand'])
        text += f"🤵 <b>Дилер:</b>\n{dealer_cards} | {game['dealer_value']}\n"
    
    text += "-----------------\n"
    
    # Игрок
    text += f"🧑‍💻 <b>Ты:</b>\n{format_hand(game['player_hand'])} | {game['player_value']}\n"
    
    # Дополнительный текст о результате
    if game["status"] == "win":
        text += f"🎉 У тебя больше очков!"
    elif game["status"] == "lose":
        text += f"💔 У дилера больше очков"
    elif game["status"] == "blackjack":
        text += f"🔥 BLACKJACK! Ты собрал 21!"
    elif game["status"] == "bust":
        text += f"💥 Перебор! Ты набрал больше 21"
    elif game["status"] == "push":
        text += f"🤝 Одинаковое количество очков"
    elif game["status"] == "surrender":
        text += f"🏳️ Ты сдался и забрал половину ставки"

    return text

# ================== CALLBACK ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith("bj_"))
def handle_blackjack_action(call):
    try:
        _, action, uid, gid = call.data.split("_")
        uid = int(uid)

        if call.from_user.id != uid:
            bot.answer_callback_query(call.id, "❌ Не твоя игра", show_alert=True)
            return

        game = active_blackjack_games.get(gid)
        if not game or game["status"] != "playing":
            bot.answer_callback_query(call.id, "❌ Игра окончена")
            return

        user_data = get_user_data(uid)
        can_double = len(game["player_hand"]) == 2 and user_data["balance"] >= game["bet"]

        if action == "hit":
            card = game["deck"].pop()
            game["player_hand"].append(card)
            game["player_value"] = hand_value(game["player_hand"])

            if game["player_value"] > 21:
                game["status"] = "bust"
                complete_blackjack_game(gid)
            elif game["player_value"] == 21:
                game["status"] = "blackjack"
                user_data["balance"] += int(game["bet"] * 2.5)
                save_casino_data()

        elif action == "stand":
            dealer_turn(gid)
            complete_blackjack_game(gid)

        elif action == "surrender":
            game["status"] = "surrender"
            user_data["balance"] += game["bet"] // 2
            save_casino_data()

        elif action == "double":
            if len(game["player_hand"]) != 2:
                bot.answer_callback_query(call.id, "❌ Только на первых картах", show_alert=True)
                return
            if user_data["balance"] < game["bet"]:
                bot.answer_callback_query(call.id, "❌ Недостаточно средств", show_alert=True)
                return

            user_data["balance"] -= game["bet"]
            game["bet"] *= 2

            game["player_hand"].append(game["deck"].pop())
            game["player_value"] = hand_value(game["player_hand"])

            if game["player_value"] > 21:
                game["status"] = "bust"
            else:
                dealer_turn(gid)
                complete_blackjack_game(gid)

        # Обновляем сообщение с ФОТО
        can_double_after = len(game["player_hand"]) == 2 and user_data["balance"] >= game["bet"] and game["status"] == "playing"
        
        bot.edit_message_media(
            media=types.InputMediaPhoto(
                media=BLACKJACK_IMAGE_URL,
                caption=format_blackjack_message(gid),
                parse_mode="HTML"
            ),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=bj_action_keyboard(uid, gid, can_double_after) if game["status"] == "playing" else None
        )
        
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка Blackjack: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== ДИЛЕР ==================
def dealer_turn(game_id):
    game = active_blackjack_games[game_id]
    game["dealer_value"] = hand_value(game["dealer_hand"])
    while game["dealer_value"] < 17:
        game["dealer_hand"].append(game["deck"].pop())
        game["dealer_value"] = hand_value(game["dealer_hand"])

# ================== ФИНАЛ ==================
def complete_blackjack_game(game_id):
    game = active_blackjack_games[game_id]
    user_data = get_user_data(game["user_id"])

    if game["status"] in ["bust", "surrender", "blackjack"]:
        return

    p = game["player_value"]
    d = game["dealer_value"]

    if d > 21 or p > d:
        game["status"] = "win"
        user_data["balance"] += game["bet"] * 2
    elif p < d:
        game["status"] = "lose"
    else:
        game["status"] = "push"
        user_data["balance"] += game["bet"]

    save_casino_data()

# ================== КОМАНДА: ИГРАТЬ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("играть"))
def play_blackjack_command(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)

        parts = message.text.split()

        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "🎰 <b>Игра в Blackjack</b>\n\n"
                "📝 <b>Использование:</b>\n"
                "<code>играть [ставка]</code>\n\n"
                "📊 <b>Примеры:</b>\n"
                "<code>играть 1000</code>\n"
                "<code>играть 5000</code>\n\n"
                "💰 <b>Минимальная ставка:</b> 100 izzzy\n"
                f"💵 <b>Твой баланс:</b> {format_number(user_data['balance'])} izzzy",
                parse_mode="HTML"
            )
            return

        try:
            bet = int(parts[1])
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ <b>Ошибка!</b>\nСтавка должна быть числом!\n\n"
                "📝 <b>Пример:</b> <code>играть 3000</code>",
                parse_mode="HTML"
            )
            return

        if bet < 100:
            bot.send_message(
                message.chat.id,
                "❌ <b>Ошибка!</b>\nМинимальная ставка 100 izzzy",
                parse_mode="HTML"
            )
            return

        game_id, result = start_blackjack_game(user_data, user_id, bet)

        if game_id is None:
            bot.send_message(message.chat.id, result, parse_mode="HTML")
            return

        # Отправляем игру с ФОТО
        text = format_blackjack_message(game_id)
        can_double = user_data["balance"] >= bet
        
        bot.send_photo(
            message.chat.id,
            photo=BLACKJACK_IMAGE_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=bj_action_keyboard(user_id, game_id, can_double)
        )

    except Exception as e:
        logger.error(f"Ошибка в команде 'играть': {e}")
        bot.send_message(
            message.chat.id,
            "❌ <b>Ошибка при запуске игры!</b>\nПопробуйте позже.",
            parse_mode="HTML"
        )



    
    
# ================== ИГРА В РУЛЕТКУ (CASINO ROULETTE) ==================

import json
import os
import random
import time

ROULETTE_BETS_FILE = "roulette_bets.json"
ROULETTE_RESULTS_FILE = "roulette_results.txt"
ROULETTE_SPIN_GIF = "https://media3.giphy.com/media/v1.Y2lkPTZjMDliOTUyZnp2YWpycWV5dHo5cnYwNzRzYndsazdrNHozeTE5cnA1ZndscTJobCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/M2YOM0xF7L83e/giphy.gif"


# ================== JSON РАБОТА ==================

def load_roulette_bets():
    if not os.path.exists(ROULETTE_BETS_FILE):
        return {}
    try:
        with open(ROULETTE_BETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_roulette_bets(data):
    with open(ROULETTE_BETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ================== ПАРСИНГ ==================

def parse_bet_input(text):
    parts = text.split()
    if len(parts) < 2:
        return None

    try:
        bet = int(parts[0])
        if bet <= 0:
            return None
    except:
        return None

    second = parts[1].lower()

    if len(parts) == 2 and second in ['к', 'ч', 'з']:
        return ('color', bet, second)

    if len(parts) == 2 and second.isdigit():
        num = int(second)
        if 0 <= num <= 36:
            return ('single', bet, num)

    if len(parts) == 2 and '-' in second:
        r = second.split('-')
        if len(r) == 2 and r[0].isdigit() and r[1].isdigit():
            start, end = int(r[0]), int(r[1])
            if 0 <= start <= 36 and 0 <= end <= 36 and start <= end:
                return ('range', bet, start, end)

    if len(parts) > 2:
        nums = []
        for p in parts[1:]:
            if not p.isdigit():
                return None
            n = int(p)
            if not 0 <= n <= 36:
                return None
            nums.append(n)
        return ('multi', bet, nums)

    return None


# ================== СТАВКА ==================

@bot.message_handler(func=lambda m: m.text and parse_bet_input(m.text) is not None)
def place_bet(message):
    try:
        user_id = str(message.from_user.id)
        chat_id = str(message.chat.id)
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

        parsed = parse_bet_input(message.text)
        if not parsed:
            return

        bet_type = parsed[0]
        bet_amount = parsed[1]

        user_data = get_user_data(int(user_id))
        roulette_data = load_roulette_bets()

        if chat_id not in roulette_data:
            roulette_data[chat_id] = {}

        if user_id not in roulette_data[chat_id]:
            roulette_data[chat_id][user_id] = []

        # ---- COLOR ----
        if bet_type == 'color':
            color = parsed[2]
            color_display = "RED" if color == 'к' else "BLACK" if color == 'ч' else "GREEN"
            
            if user_data["balance"] < bet_amount:
                bot.reply_to(message, f"Недостаточно средств!", parse_mode="HTML")
                return

            user_data["balance"] -= bet_amount
            roulette_data[chat_id][user_id].append({
                "type": "color",
                "amount": bet_amount,
                "value": color,
                "mention": mention
            })

            save_casino_data()
            save_roulette_bets(roulette_data)

            bot.reply_to(
                message, 
                f"Ставка принята: {mention} {format_number(bet_amount)} izzzy на {color_display}",
                parse_mode="HTML"
            )

        # ---- SINGLE ----
        elif bet_type == 'single':
            number = parsed[2]
            if user_data["balance"] < bet_amount:
                bot.reply_to(message, "Недостаточно средств!", parse_mode="HTML")
                return

            user_data["balance"] -= bet_amount
            roulette_data[chat_id][user_id].append({
                "type": "single",
                "amount": bet_amount,
                "value": [number],
                "mention": mention
            })

            save_casino_data()
            save_roulette_bets(roulette_data)

            bot.reply_to(
                message, 
                f"Ставка принята: {mention} {format_number(bet_amount)}$ на {number}",
                parse_mode="HTML"
            )

        # ---- RANGE ----
        elif bet_type == 'range':
            start, end = parsed[2], parsed[3]
            size = end - start + 1
            total = bet_amount * size

            if user_data["balance"] < total:
                bot.reply_to(message, "Недостаточно средств!", parse_mode="HTML")
                return

            user_data["balance"] -= total
            roulette_data[chat_id][user_id].append({
                "type": "range",
                "amount": bet_amount,
                "start": start,
                "end": end,
                "mention": mention
            })

            save_casino_data()
            save_roulette_bets(roulette_data)

            bot.reply_to(
                message, 
                f"Ставка принята: {mention} {bet_amount} izzzy на {start}-{end}",
                parse_mode="HTML"
            )

        # ---- MULTI ----
        elif bet_type == 'multi':
            numbers = parsed[2]
            total = bet_amount * len(numbers)

            if user_data["balance"] < total:
                bot.reply_to(message, "Недостаточно средств!", parse_mode="HTML")
                return

            user_data["balance"] -= total
            roulette_data[chat_id][user_id].append({
                "type": "single",
                "amount": bet_amount,
                "value": numbers,
                "mention": mention
            })

            save_casino_data()
            save_roulette_bets(roulette_data)

            bot.reply_to(
                message, 
                f"Ставка принята: {mention} {format_number(total)} izzzy на числа",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Ошибка ставки: {e}")
        bot.reply_to(message, "Ошибка при размещении ставки!")


import threading
import uuid
from datetime import datetime

roulette_lock = threading.Lock()

def generate_roulette_session_id():
    """Генерирует уникальный ID для сессии рулетки."""
    return str(uuid.uuid4())[:8]

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'го')
def start_roulette(message):
    try:
        chat_id = str(message.chat.id)
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        # ✅ Создаем session_id в самом начале, чтобы он был доступен везде
        session_id = generate_roulette_session_id()
        
        with roulette_lock:
            # 1. Загружаем ставки
            try:
                with open(ROULETTE_BETS_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:  # Пустой файл
                        roulette_data = {}
                    else:
                        roulette_data = json.loads(content)
            except (FileNotFoundError, json.JSONDecodeError):
                roulette_data = {}
            
            # 2. Проверяем наличие ставок в чате
            if chat_id not in roulette_data or not roulette_data[chat_id]:
                bot.send_message(chat_id, 
                                 f"{mention}, в чате нет активных ставок!",
                                 parse_mode="HTML")
                return
            
            # 3. Сохраняем ставки в локальную переменную
            chat_bets = roulette_data.pop(chat_id, None)
            
            # 4. Перезаписываем файл, удаляя обработанные ставки
            try:
                with open(ROULETTE_BETS_FILE, "w", encoding="utf-8") as f:
                    json.dump(roulette_data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"Не удалось сохранить файл ставок: {e}")
                # Если не удалось сохранить, возвращаем ставки обратно, чтобы не потерять
                if chat_bets:
                    if chat_id not in roulette_data:
                        roulette_data[chat_id] = {}
                    roulette_data[chat_id].update(chat_bets)
                    with open(ROULETTE_BETS_FILE, "w", encoding="utf-8") as f:
                        json.dump(roulette_data, f, ensure_ascii=False, indent=4)
                bot.send_message(chat_id, "❌ Ошибка при обработке ставок. Попробуйте позже.")
                return
        
        # ===== ВНЕ БЛОКИРОВКИ =====
        # 5. Отправляем анимацию без текста
        spin_msg = bot.send_animation(
            chat_id,
            ROULETTE_SPIN_GIF
        )
        
        time.sleep(2)
        
        # 6. Удаляем анимацию
        try:
            bot.delete_message(chat_id, spin_msg.message_id)
        except:
            pass
        
        # 7. Генерируем результат
        if random.random() < 0.027:  # 2.7% шанс на зеро
            result_number = 0
            result_color = 'з'
            color_emoji = "🟢"
        else:
            result_number = random.randint(1, 36)
            result_color = 'ч' if result_number % 2 == 0 else 'к'
            color_emoji = "⚫" if result_color == 'ч' else "🔴"
        
        # 8. Формируем результат
        result_lines = []
        result_lines.append(f"Рулетка: {result_number}{color_emoji}")
        
        # 9. Обрабатываем ставки
        for player_id, bets in chat_bets.items():
            try:
                player_data = get_user_data(int(player_id))
                for bet in bets:
                    # Используем mention из ставки (там уже есть кликабельная ссылка)
                    player_mention = bet.get('mention', f'<a href="tg://user?id={player_id}">Игрок</a>')
                    
                    # Определяем тип ставки и формируем строку
                    if bet["type"] == "color":
                        color_text = "RED" if bet["value"] == 'к' else "BLACK" if bet["value"] == 'ч' else "GREEN"
                        bet_line = f"{player_mention} {format_number(bet['amount'])} izzzy на {color_text}"
                    elif bet["type"] == "single":
                        if len(bet["value"]) == 1:
                            bet_line = f"{player_mention} {format_number(bet['amount'])} izzzy на {bet['value'][0]}"
                        else:
                            # Для нескольких чисел
                            numbers_str = ', '.join(str(n) for n in bet['value'])
                            bet_line = f"{player_mention} {format_number(bet['amount'])} izzzy на {numbers_str}"
                    elif bet["type"] == "range":
                        bet_line = f"{player_mention} {format_number(bet['amount'])} izzzy на {bet['start']}-{bet['end']}"
                    else:
                        bet_line = f"{player_mention} {format_number(bet['amount'])} izzzy"
                    
                    # Проверяем выигрыш
                    won = False
                    win_amount = 0
                    
                    if bet["type"] == "color":
                        if bet["value"] == result_color:
                            won = True
                            win_amount = bet["amount"] * (15 if result_color == 'з' else 2)
                    elif bet["type"] == "single":
                        if result_number in bet["value"]:
                            won = True
                            win_amount = bet["amount"] * 36 if len(bet["value"]) == 1 else bet["amount"] * 2
                    elif bet["type"] == "range":
                        if bet["start"] <= result_number <= bet["end"]:
                            won = True
                            win_amount = bet["amount"] * (bet["end"] - bet["start"] + 1)
                    
                    if won:
                        player_data["balance"] += win_amount
                        bet_line += " | WIN"
                    
                    result_lines.append(bet_line)
                
                save_casino_data()
                
            except Exception as e:
                logger.error(f"Ошибка обработки ставки игрока {player_id}: {e}")
        
        # 10. Отправляем результат
        result_text = "\n".join(result_lines)
        if len(result_text) > 4000:
            result_text = result_text[:4000] + "..."
        
        bot.send_message(chat_id, result_text, parse_mode="HTML")
        
        # 11. Логируем результат ✅
        try:
            with open(ROULETTE_RESULTS_FILE, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                total_bets = sum(len(bets) for bets in chat_bets.values())
                f.write(f"{timestamp}|{result_number}|{result_color}|{session_id}|{total_bets}|0\n")
                logger.info(f"✅ Результат рулетки записан в лог: {result_number} {result_color}, сессия {session_id}")
        except Exception as e:
            logger.error(f"❌ Не удалось записать результат рулетки в лог: {e}")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка рулетки: {e}", exc_info=True)
        
        # ✅ Проверяем, существует ли session_id (на случай ошибки ДО его создания)
        error_session_id = session_id if 'session_id' in locals() else "unknown"
        
        bot.send_message(message.chat.id, 
                        f"❌ Критическая ошибка при запуске рулетки!\n"
                        f"Сообщите администратору код: <code>{error_session_id}</code>\n"
                        f"Ошибка: {str(e)}",
                        parse_mode="HTML")

# ================== КОМАНДА ЛОГИ РУЛЕТКИ ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["лог", "логи"])
def show_roulette_logs(message):
    """Показать последние 10 результатов рулетки"""
    try:
        if not os.path.exists(ROULETTE_RESULTS_FILE):
            bot.reply_to(message, "❗ Логи рулетки пусты.")
            return

        with open(ROULETTE_RESULTS_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()

        recent_logs = logs[-10:] if len(logs) >= 10 else logs

        if not recent_logs:
            bot.reply_to(message, "❗ Логи рулетки пусты.")
            return

        recent_logs.reverse()
        text = ""

        for log in recent_logs:
            log = log.strip()
            if "|" in log:
                parts = log.split("|")
                if len(parts) >= 6:
                    number = parts[1]
                    color = parts[2]
                    
                    if color == 'з':
                        emoji = "🟢"
                    elif color == 'к':
                        emoji = "🔴"
                    else:  # 'ч'
                        emoji = "⚫"
                    
                    text += f"{number}{emoji}\n"

        # Отправляем ответом на сообщение пользователя
        bot.reply_to(message, text.strip(), parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка показа логов рулетки: {e}")
        bot.reply_to(message, "❌ Ошибка при получении логов!")

print("✅ Новая улучшенная система рулетки загружена!")
        


        
# ================== ФУТБОЛ / БАСКЕТБОЛ / ТИР (50/50) БЕЗ АНИМАЦИИ ==================

def sport_game_simple(message, game_type, bet):
    """Упрощенная версия игры без анимации с честными 50/50"""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

    # Проверки
    if bet <= 0:
        bot.reply_to(message, "❌ Ставка должна быть больше 0!")
        return

    if user_data["balance"] < bet:
        bot.reply_to(message, "❌ Недостаточно средств!")
        return

    games = {
        "футбол": {
            "emoji": "⚽",
            "name": "футбол",
            "action1": "Целимся в ворота...",
            "action2": "Делаем удар по воротам..."
        },
        "баскетбол": {
            "emoji": "🏀",
            "name": "баскетбол",
            "action1": "Целимся в кольцо...",
            "action2": "Делаем бросок..."
        },
        "тир": {
            "emoji": "🎯",
            "name": "тир",
            "action1": "Целимся в мишень...",
            "action2": "Кидаем дротик..."
        }
    }

    if game_type not in games:
        return

    game_info = games[game_type]
    
    # Списываем ставку
    user_data["balance"] -= bet
    save_casino_data()

    # ЧЕСТНЫЕ 50/50 - используем random.random() для более точного распределения
    win_chance = random.random()  # от 0.0 до 1.0
    win = win_chance < 0.60  # ровно 50% шанс на выигрыш
    
    # Для отладки можно добавить логирование
    logger.info(f"🎮 Игра {game_type}: ставка {bet}, шанс {win_chance:.3f}, результат {'ВЫИГРЫШ' if win else 'ПРОИГРЫШ'}")
    
    # Первое сообщение
    msg1 = bot.reply_to(
        message,
        f"{game_info['emoji']} {game_info['action1']}",
        parse_mode="HTML"
    )
    time.sleep(1)
    
    # Второе сообщение (отвечает на первое)
    msg2 = bot.reply_to(
        msg1,
        f"{game_info['emoji']} {game_info['action2']}",
        parse_mode="HTML"
    )
    time.sleep(1)
    
    # Третье сообщение с результатом (отвечает на второе)
    if win:
        win_amount = bet * 2
        user_data["balance"] += win_amount
        save_casino_data()
        
        msg3 = bot.reply_to(
            msg2,
            f"✅ {mention}, ты попал по цели, выигрыш составил: {format_number(win_amount)} izzzy",
            parse_mode="HTML"
        )
    else:
        msg3 = bot.reply_to(
            msg2,
            f"❌ {mention}, ты промахнулся, проигрыш составил: {format_number(bet)} izzzy",
            parse_mode="HTML"
        )
    
    # Ждем 2 секунды и удаляем все сообщения
    time.sleep(2)
    try:
        bot.delete_message(message.chat.id, msg1.message_id)
        bot.delete_message(message.chat.id, msg2.message_id)
        bot.delete_message(message.chat.id, msg3.message_id)
        # Также удаляем оригинальное сообщение с командой если это не в ЛС
        if message.chat.type != "private":
            bot.delete_message(message.chat.id, message.message_id)
    except:
        pass  # Если не удалось удалить - не страшно


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("футбол"))
def football_game(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "🎮 <b>Футбол</b>\n\nПример: <code>футбол 500</code>\n\n⚽ Ударь по воротам и выигрывай x2!\n🎯 Шанс выигрыша: 50%", parse_mode="HTML")
            return

        bet = int(parts[1])
        sport_game_simple(message, "футбол", bet)

    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом!\nПример: <code>футбол 1000</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка в футболе: {e}")
        bot.reply_to(message, "❌ Произошла ошибка в игре. Попробуйте еще раз.")


@bot.message_handler(func=lambda m: m.text and (
    m.text.lower().startswith("баскетбол") or
    m.text.lower().startswith("бс") or
    m.text.lower().startswith("баскет")
))
def basketball_game(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "🏀 <b>Баскетбол</b>\n\nПример: <code>баскетбол 500</code>\n\n🏀 Забрось мяч в кольцо и выигрывай x2!\n🎯 Шанс выигрыша: 50%", parse_mode="HTML")
            return

        bet = int(parts[1])
        sport_game_simple(message, "баскетбол", bet)

    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом!\nПример: <code>баскетбол 1000</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка в баскетболе: {e}")
        bot.reply_to(message, "❌ Произошла ошибка в игре. Попробуйте еще раз.")


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("тир"))
def shooting_game(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "🎯 <b>Тир</b>\n\nПример: <code>тир 500</code>\n\n🎯 Попади в цель и выигрывай x2!\n🎯 Шанс выигрыша: 50%", parse_mode="HTML")
            return

        bet = int(parts[1])
        sport_game_simple(message, "тир", bet)

    except ValueError:
        bot.reply_to(message, "❌ Сумма должна быть числом!\nПример: <code>тир 1000</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка в тире: {e}")
        bot.reply_to(message, "❌ Произошла ошибка в игре. Попробуйте еще раз.")


print("✅ Игры футбол/баскетбол/тир с честными 50/50 загружены! ⚽🏀🎯")



# ================== 🐿️ ИГРА "НАЙДИ БЕЛКУ" ==================

import random
import uuid
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Словарь для хранения активных игр
active_squirrel_games = {}

def check_squirrel_owner(call, user_id):
    """Проверка владельца кнопки"""
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
        return False
    return True

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("белка "))
def squirrel_game(message):
    """Команда для начала игры: белка [ставка]"""
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        # Парсим ставку
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, 
                        f"{mention}, укажи ставку!\n\n"
                        f"Пример: <code>белка 1000</code>",
                        parse_mode="HTML")
            return
        
        try:
            bet = int(parts[1])
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше 0!")
                return
        except ValueError:
            bot.reply_to(message, "❌ Ставка должна быть числом!")
            return
        
        # Проверяем баланс
        user_data = get_user_data(user_id)
        if user_data["balance"] < bet:
            bot.reply_to(message, 
                        f"❌ {mention}, недостаточно средств!\n\n"
                        f"💰 Нужно: <code>{format_number(bet)} izzzy</code>\n"
                        f"💳 У тебя: <code>{format_number(user_data['balance'])} izzzy</code>",
                        parse_mode="HTML")
            return
        
        # Списываем ставку
        user_data["balance"] -= bet
        save_casino_data()
        
        # Генерируем ID игры
        game_id = str(uuid.uuid4())[:8]
        
        # Рандомно выбираем клетку с белкой (0 или 1)
        squirrel_cell = random.randint(0, 1)
        
        # Сохраняем игру
        active_squirrel_games[game_id] = {
            "user_id": user_id,
            "bet": bet,
            "squirrel_cell": squirrel_cell,
            "active": True,
            "message_id": None,
            "chat_id": message.chat.id
        }
        
        # Создаем клавиатуру (кнопки вертикально)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("❓ Клетка 1", callback_data=f"squirrel_0_{game_id}_{user_id}"))
        kb.add(InlineKeyboardButton("❓ Клетка 2", callback_data=f"squirrel_1_{game_id}_{user_id}"))
        
        # Отправляем сообщение
        game_text = f"{mention}, <b>найди белку 🐿️</b>\n\nВыбери клетку:"
        msg = bot.reply_to(message, game_text, parse_mode="HTML", reply_markup=kb)
        
        # Сохраняем ID сообщения
        active_squirrel_games[game_id]["message_id"] = msg.message_id
        
        # Удаляем команду пользователя (для чистоты чата)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Ошибка в игре белка: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при создании игры!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("squirrel_"))
def squirrel_callback(call):
    """Обработчик нажатия на кнопки"""
    try:
        # Разбираем callback_data: squirrel_клетка_gameid_userid
        parts = call.data.split("_")
        cell = int(parts[1])  # 0 или 1
        game_id = parts[2]
        owner_id = int(parts[3])
        
        # Проверяем владельца
        if not check_squirrel_owner(call, owner_id):
            return
        
        # Получаем игру
        game = active_squirrel_games.get(game_id)
        if not game:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return
        
        # Проверяем, активна ли игра
        if not game["active"]:
            bot.answer_callback_query(call.id, "❌ Игра уже завершена!", show_alert=True)
            return
        
        # Помечаем игру как неактивную (чтобы второй раз не нажали)
        game["active"] = False
        
        # Получаем данные
        user_id = owner_id
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        bet = game["bet"]
        squirrel_cell = game["squirrel_cell"]
        
        # Создаем клавиатуру с результатом (без возможности нажатия)
        result_kb = InlineKeyboardMarkup()
        
        if cell == squirrel_cell:
            # ПОБЕДА - игрок нашел белку
            win_amount = bet * 2.5
            user_data = get_user_data(user_id)
            user_data["balance"] += win_amount
            save_casino_data()
            
            # Показываем, где была белка
            if squirrel_cell == 0:
                result_kb.add(InlineKeyboardButton("🐿️ Белка тут!", callback_data="squirrel_done"))
                result_kb.add(InlineKeyboardButton("❌ Пусто", callback_data="squirrel_done"))
            else:
                result_kb.add(InlineKeyboardButton("❌ Пусто", callback_data="squirrel_done"))
                result_kb.add(InlineKeyboardButton("🐿️ Белка тут!", callback_data="squirrel_done"))
            
            # Текст победы
            result_text = (f"{mention}, <b>ты нашёл белку! 🐿️</b>\n\n"
                          f"💰 Твоя ставка <code>{format_number(bet)} izzzy</code> увеличилась в 2.5х\n"
                          f"🎉 Ты получил <code>{format_number(win_amount)} izzzy</code>")
            
        else:
            # ПРОИГРЫШ - игрок не нашел белку
            # Показываем, где была белка
            if squirrel_cell == 0:
                result_kb.add(InlineKeyboardButton("🐿️ Белка была тут!", callback_data="squirrel_done"))
                result_kb.add(InlineKeyboardButton("❌ Пусто", callback_data="squirrel_done"))
            else:
                result_kb.add(InlineKeyboardButton("❌ Пусто", callback_data="squirrel_done"))
                result_kb.add(InlineKeyboardButton("🐿️ Белка была тут!", callback_data="squirrel_done"))
            
            # Текст проигрыша
            result_text = (f"{mention}, <b>к сожалению, белка была не тут 😔</b>\n\n"
                          f"💸 Ты потерял ставку <code>{format_number(bet)} izzzy</code>")
        
        # Редактируем сообщение с результатом
        bot.edit_message_text(
            result_text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML",
            reply_markup=result_kb
        )
        
        # Удаляем игру из активных через 5 минут (чтобы не засорять память)
        def delete_game():
            time.sleep(300)
            if game_id in active_squirrel_games:
                del active_squirrel_games[game_id]
        
        threading.Thread(target=delete_game, daemon=True).start()
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике белки: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка!", show_alert=True)

# Заглушка для неактивных кнопок (чтобы не было ошибок)
@bot.callback_query_handler(func=lambda c: c.data == "squirrel_done")
def squirrel_done_callback(call):
    bot.answer_callback_query(call.id, "🎮 Игра уже завершена")

# ================== СЛОТЫ (ИСПРАВЛЕННАЯ ВЕРСИЯ) ==================

SLOT_SYMBOLS = ["🍒", "⭐", "🍋", "🍊", "💎", "🍀", "❌", "❌", "❌", "❌"]  # Добавлены проигрышные символы
SLOT_MULTIPLIERS = {
    "💎💎💎": 10.0,
    "🍒🍒🍒": 5.0,
    "⭐⭐⭐": 3.0,
    "🍋🍋🍋": 2.0,
    "🍊🍊🍊": 2.0,
    "🍀🍀🍀": 2.0
}

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("слот"))
def slot_game(message):
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используй: <code>слот [ставка]</code>", parse_mode="HTML")
            return
        
        try:
            bet = int(parts[1])
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше 0")
                return
        except ValueError:
            bot.reply_to(message, "❌ Ставка должна быть числом")
            return
        
        user_data = get_user_data(user_id)
        if user_data["balance"] < bet:
            bot.reply_to(message, f"❌ Недостаточно средств\n💰 Баланс: {format_number(user_data['balance'])} izzzy")
            return
        
        user_data["balance"] -= bet
        save_casino_data()
        
        # Генерируем слоты с учетом вероятности проигрыша 45%
        if random.random() < 0.30:  # 45% шанс проигрыша
            # Генерируем гарантированный проигрыш (нет выигрышных комбинаций)
            while True:
                slots = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
                slot_str = "".join(slots)
                
                # Проверяем, что это не выигрышная комбинация
                is_winning = False
                if slot_str in SLOT_MULTIPLIERS:
                    is_winning = True
                else:
                    for symbol in SLOT_SYMBOLS:
                        if slot_str.count(symbol) == 2 and symbol not in ["❌"]:
                            is_winning = True
                            break
                
                if not is_winning:
                    break
        else:
            # 55% шанс на возможный выигрыш
            slots = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
            slot_str = "".join(slots)
        
        win_multiplier = 0
        
        # Проверяем выигрышные комбинации
        if slot_str in SLOT_MULTIPLIERS:
            win_multiplier = SLOT_MULTIPLIERS[slot_str]
        else:
            for symbol in SLOT_SYMBOLS:
                if slot_str.count(symbol) == 2 and symbol not in ["❌"]:
                    win_multiplier = 1.5
                    break
        
        if win_multiplier > 0:
            win_amount = int(bet * win_multiplier)
            user_data["balance"] += win_amount
            result_text = f"✅ Выигрыш | +{format_number(win_amount)} izzzy"
        else:
            win_amount = 0
            result_text = f"❌ Проигрыш | -{format_number(bet)} izzzy"
        
        save_casino_data()
        
        response = (
            f"🎰 <b>Слоты {mention}</b>\n\n"
            f"🎮 Результат: {' '.join(slots)}\n"
            f"📊 {result_text}\n"
            f"💰 Баланс: {format_number(user_data['balance'])} izzzy"
        )
        
        bot.reply_to(message, response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в слотах: {e}")
        bot.reply_to(message, "❌ Ошибка в игре")



# ================== ИГРА В КУБИК (1 НА 1) ==================
DICE_DB = "dice_games.db"

# Инициализация базы данных для кубика
def init_dice_db():
    conn = sqlite3.connect(DICE_DB)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS dice_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            bet_amount INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    conn.commit()
    conn.close()

init_dice_db()

def create_dice_request(from_user_id, to_user_id, bet_amount):
    """Создает запрос на игру в кубик"""
    # Проверяем, есть ли уже активный запрос
    conn = sqlite3.connect(DICE_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT 1 FROM dice_requests 
        WHERE from_user_id = ? AND to_user_id = ? AND status = 'pending'
    """, (from_user_id, to_user_id))
    
    if c.fetchone():
        conn.close()
        return False, "⏳ Запрос на игру уже отправлен!"
    
    # Создаем запрос (действует 5 минут)
    now = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(minutes=5)).isoformat()
    
    c.execute("""
        INSERT INTO dice_requests 
        (from_user_id, to_user_id, bet_amount, created_at, expires_at, status) 
        VALUES (?, ?, ?, ?, ?, 'pending')
    """, (from_user_id, to_user_id, bet_amount, now, expires_at))
    
    conn.commit()
    conn.close()
    return True, "🎲 Запрос на игру отправлен!"

def cleanup_expired_dice_requests():
    """Очищает просроченные запросы на игру"""
    conn = sqlite3.connect(DICE_DB)
    c = conn.cursor()
    
    expired_time = datetime.now().isoformat()
    c.execute("DELETE FROM dice_requests WHERE expires_at < ? AND status = 'pending'", (expired_time,))
    
    conn.commit()
    conn.close()

def accept_dice_request(from_user_id, to_user_id):
    """Принимает запрос на игру"""
    conn = sqlite3.connect(DICE_DB)
    c = conn.cursor()
    
    # Проверяем существование запроса
    c.execute("""
        SELECT bet_amount FROM dice_requests 
        WHERE from_user_id = ? AND to_user_id = ? AND status = 'pending'
    """, (from_user_id, to_user_id))
    
    request = c.fetchone()
    if not request:
        conn.close()
        return False, "❌ Запрос на игру не найден или истек!"
    
    bet_amount = request[0]
    
    # Списываем деньги у обоих игроков
    user1_data = get_user_data(from_user_id)
    user2_data = get_user_data(to_user_id)
    
    if user1_data["balance"] < bet_amount or user2_data["balance"] < bet_amount:
        conn.close()
        return False, "❌ У одного из игроков недостаточно средств!"
    
    user1_data["balance"] -= bet_amount
    user2_data["balance"] -= bet_amount
    save_casino_data()
    
    # Обновляем статус запроса
    c.execute("UPDATE dice_requests SET status = 'accepted' WHERE from_user_id = ? AND to_user_id = ?", 
              (from_user_id, to_user_id))
    
    conn.commit()
    conn.close()
    return True, bet_amount

def reject_dice_request(from_user_id, to_user_id):
    """Отклоняет запрос на игру"""
    conn = sqlite3.connect(DICE_DB)
    c = conn.cursor()
    
    c.execute("UPDATE dice_requests SET status = 'rejected' WHERE from_user_id = ? AND to_user_id = ?", 
              (from_user_id, to_user_id))
    
    conn.commit()
    conn.close()
    return True

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("кубик"))
def dice_game(message):
    """Игра в кубик 1 на 1"""
    try:
        # Очищаем старые запросы
        cleanup_expired_dice_requests()
        
        user_id = message.from_user.id
        from_user_name = message.from_user.first_name
        from_mention = f'<a href="tg://user?id={user_id}">{from_user_name}</a>'
        
        # Определяем целевого пользователя
        target_user = None
        target_user_id = None
        
        if not message.reply_to_message:
            bot.reply_to(
                message,
                f"🎲 <b>Игра в кубик</b>\n\n"
                f"{from_mention}, нужно ответить на сообщение пользователя!\n\n"
                f"<b>Пример:</b>\n"
                f"Ответь на сообщение и напиши: <code>кубик 1000</code>",
                parse_mode="HTML"
            )
            return
        
        target_user = message.reply_to_message.from_user
        target_user_id = target_user.id
        target_user_name = target_user.first_name
        to_mention = f'<a href="tg://user?id={target_user_id}">{target_user_name}</a>'
        
        # Проверки
        if target_user_id == user_id:
            bot.reply_to(message, "❌ Нельзя играть самому с собой!")
            return
        
        if target_user.is_bot:
            bot.reply_to(message, "❌ Нельзя играть с ботом!")
            return
        
        # Парсим ставку
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(
                message,
                f"❌ {from_mention}, укажи ставку!\n\n"
                f"Пример: <code>кубик 1000</code>",
                parse_mode="HTML"
            )
            return
        
        try:
            bet_amount = int(parts[1])
            if bet_amount <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше 0!")
                return
        except ValueError:
            bot.reply_to(message, "❌ Ставка должна быть числом!")
            return
        
        # Проверяем баланс того, кто предлагает
        user_data = get_user_data(user_id)
        if user_data["balance"] < bet_amount:
            bot.reply_to(message, "❌ У тебя нет столько средств.")
            return
        
        # Проверяем баланс того, кому предлагают
        target_data = get_user_data(target_user_id)
        if target_data["balance"] < bet_amount:
            bot.reply_to(
                message,
                f"❌ {from_mention}, у твоего соперника недостаточно средств.",
                parse_mode="HTML"
            )
            return
        
        # Создаем запрос на игру
        success, result_msg = create_dice_request(user_id, target_user_id, bet_amount)
        
        if not success:
            bot.reply_to(message, result_msg)
            return
        
        # Отправляем предложение
        text = (
            f"{to_mention}, внимание!\n\n"
            f"🎲 Пользователь {from_mention} предложил сыграть тебе с ним в кубик.\n\n"
            f"💰 Ставка: <b>{format_number(bet_amount)} izzzy</b>\n"
            f"⏰ Действует: 5 минут"
        )
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Начать", callback_data=f"dice_accept_{user_id}_{target_user_id}"),
            InlineKeyboardButton("Отказать", callback_data=f"dice_reject_{user_id}_{target_user_id}")
        )
        
        msg = bot.reply_to(message, text, parse_mode="HTML", reply_markup=kb)
        
        # Сохраняем ID сообщения для возможного обновления
        return True
        
    except Exception as e:
        logger.error(f"Ошибка в игре кубик: {e}")
        bot.reply_to(message, "❌ Ошибка при создании игры!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("dice_accept_"))
def dice_accept_callback(call):
    """Обработка принятия игры в кубик"""
    try:
        parts = call.data.split("_")
        from_user_id = int(parts[2])
        to_user_id = int(parts[3])
        
        # Проверяем, что нажимает тот, кому предложили
        if call.from_user.id != to_user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Принимаем игру
        success, result = accept_dice_request(from_user_id, to_user_id)
        
        if not success:
            bot.answer_callback_query(call.id, f"❌ {result}", show_alert=True)
            return
        
        bet_amount = result
        
        # Получаем информацию об игроках
        from_user = bot.get_chat(from_user_id)
        to_user = bot.get_chat(to_user_id)
        
        from_mention = f'<a href="tg://user?id={from_user_id}">{from_user.first_name}</a>'
        to_mention = f'<a href="tg://user?id={to_user_id}">{to_user.first_name}</a>'
        
        # Начинаем игру
        bot.edit_message_text(
            f"🎲 Игра в кубик начата!\n\n"
            f"💰 Ставка: <b>{format_number(bet_amount)} izzzy</b>\n"
            f"👥 Игроки:\n"
            f"1. {from_mention}\n"
            f"2. {to_mention}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, "✅ Игра начата!")
        
        # Запускаем игру в кубик
        threading.Thread(
            target=play_dice_game,
            args=(from_user_id, to_user_id, bet_amount, call.message.chat.id, call.message.message_id)
        ).start()
        
    except Exception as e:
        logger.error(f"Ошибка принятия кубика: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при старте игры!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dice_reject_"))
def dice_reject_callback(call):
    """Обработка отказа от игры в кубик"""
    try:
        parts = call.data.split("_")
        from_user_id = int(parts[2])
        to_user_id = int(parts[3])
        
        # Проверяем, что нажимает один из участников
        if call.from_user.id not in [from_user_id, to_user_id]:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Отклоняем игру
        reject_dice_request(from_user_id, to_user_id)
        
        # Редактируем сообщение
        bot.edit_message_text(
            "🎲 Игра в кубик отменена",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, "❌ Игра отменена")
        
    except Exception as e:
        logger.error(f"Ошибка отказа от кубика: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при отмене игры!", show_alert=True)

def play_dice_game(player1_id, player2_id, bet_amount, chat_id, message_id):
    """Процесс игры в кубик"""
    try:
        # Определяем случайно, кто бросает первым
        players = [player1_id, player2_id]
        random.shuffle(players)
        first_player = players[0]
        second_player = players[1]
        
        # Получаем информацию об игроках
        player1 = bot.get_chat(player1_id)
        player2 = bot.get_chat(player2_id)
        
        first_mention = f'<a href="tg://user?id={first_player}">{player1.first_name if first_player == player1_id else player2.first_name}</a>'
        second_mention = f'<a href="tg://user?id={second_player}">{player2.first_name if second_player == player2_id else player1.first_name}</a>'
        
        time.sleep(1)
        
        # Первый игрок бросает кубик
        bot.send_message(
            chat_id,
            f"🎲 Сейчас ход {first_mention}",
            parse_mode="HTML"
        )
        
        time.sleep(1)
        
        # Отправляем эмодзи кубика
        dice_msg = bot.send_message(chat_id, "🎲")
        
        time.sleep(2)
        
        # Определяем результат первого игрока
        first_result = random.randint(1, 6)
        
        # Редактируем сообщение с результатом
        bot.edit_message_text(
            f"🎲 {first_mention} выбросил(а): <b>{first_result}</b>",
            chat_id,
            dice_msg.message_id,
            parse_mode="HTML"
        )
        
        time.sleep(1)
        
        # Второй игрок бросает кубик
        bot.send_message(
            chat_id,
            f"🎲 Теперь кидает кубик {second_mention}",
            parse_mode="HTML"
        )
        
        time.sleep(1)
        
        # Отправляем эмодзи кубика
        dice_msg2 = bot.send_message(chat_id, "🎲")
        
        time.sleep(2)
        
        # Определяем результат второго игрока
        second_result = random.randint(1, 6)
        
        # Редактируем сообщение с результатом
        bot.edit_message_text(
            f"🎲 {second_mention} выбросил(а): <b>{second_result}</b>",
            chat_id,
            dice_msg2.message_id,
            parse_mode="HTML"
        )
        
        time.sleep(1)
        
        # Определяем победителя
        if first_result > second_result:
            winner_id = first_player
            loser_id = second_player
            winner_mention = first_mention
            loser_mention = second_mention
            winner_name = player1.first_name if first_player == player1_id else player2.first_name
        elif second_result > first_result:
            winner_id = second_player
            loser_id = first_player
            winner_mention = second_mention
            loser_mention = first_mention
            winner_name = player2.first_name if second_player == player2_id else player1.first_name
        else:
            # Ничья - возвращаем деньги
            winner_id = None
        
        # Отправляем результат
        result_text = (
            f"🔴 <b>Результат игры кубик:</b>\n\n"
            f"1. {first_mention} | Выпало: <b>{first_result}</b> 🎲\n"
            f"2. {second_mention} | Выпало: <b>{second_result}</b> 🎲\n\n"
        )
        
        if winner_id:
            win_amount = bet_amount * 2
            winner_data = get_user_data(winner_id)
            winner_data["balance"] += win_amount
            save_casino_data()
            
            result_text += (
                f"🏆 <b>Выиграл {winner_mention}</b>\n"
                f"💰 Получил на баланс: <b>{format_number(win_amount)} izzzy</b>"
            )
        else:
            # Ничья - возвращаем деньги обоим
            player1_data = get_user_data(player1_id)
            player2_data = get_user_data(player2_id)
            
            player1_data["balance"] += bet_amount
            player2_data["balance"] += bet_amount
            save_casino_data()
            
            result_text += "🤝 <b>Ничья! Деньги возвращены обоим игрокам.</b>"
        
        bot.send_message(
            chat_id,
            result_text,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в процессе игры кубик: {e}")

def get_user_name(user_id):
    """Получает имя пользователя"""
    try:
        user_data = get_user_data(user_id)
        return user_data.get("name", f"Игрок {user_id}")
    except:
        return f"Игрок {user_id}"

print("✅ Игры: футбол, баскетбол, тир и кубик загружены и готовы к работе! ⚽🏀🎯🎲")


# ================== MINES 5x5 СТАНДАРТНАЯ ВЕРСИЯ ==================

# Глобальные переменные для конфигурации мин (изменяются через админ-команды)
CURRENT_MINES_COUNT = 6  # Стандартное количество мин
CURRENT_MULTIPLIER = 0.25  # Стандартный множитель за клетку

def start_mines_game(user_id, bet):
    """Начинает игру с текущими настройками"""
    u = get_user_data(user_id)
    if u["balance"] < bet:
        return False

    u["balance"] -= bet  
    u.update({  
        "game": "mines",  
        "stage": "mines",  
        "mines_owner": user_id,  
        "mines_bet": bet,  
        "mines_count": CURRENT_MINES_COUNT,
        "mines_positions": random.sample(range(25), CURRENT_MINES_COUNT),  
        "mines_open": [],  
        "mines_multiplier": 1.0,  
        "mines_started": False,
    })  
    save_casino_data()  
    return True

def mines_keyboard(user_id, reveal_all=False, hide_buttons=False):
    """Создает клавиатуру для игры в мины"""
    u = get_user_data(user_id)
    kb = InlineKeyboardMarkup()

    btns = []  
    for i in range(25):  
        if reveal_all:  
            # Показываем мины 💣 или безопасные клетки 💎
            if i in u["mines_positions"]:  
                text = "  💣  "
            else:
                text = "         "
        else:  
            # Показываем открытые клетки или неизвестные
            if i in u["mines_open"]:  
                text = "        "  # Безопасная клетка
            else:  
                text = "  ❓  "  # Неоткрытая клетка

        # Создаем кнопку с callback_data для владельца игры
        btns.append(  
            InlineKeyboardButton(  
                text,  
                callback_data=f"mines_{i}_{user_id}" if not hide_buttons else "no_action"
            )  
        )  

    # Собираем сетку 5x5
    for i in range(0, 25, 5):  
        kb.row(*btns[i:i + 5])  

    # Кнопки действий (только если не скрыты)
    if not hide_buttons:
        if not u["mines_started"]:  
            # Кнопка отмены в начале игры
            kb.row(  
                InlineKeyboardButton(" Отменить игру", callback_data=f"mines_cancel_{user_id}")  
            )  
        else:  
            # Кнопка забрать выигрыш во время игры
            current_win = int(u["mines_bet"] * u["mines_multiplier"])
            kb.row(  
                InlineKeyboardButton(f"💸 Забрать выигрыш", 
                                    callback_data=f"mines_cash_{user_id}")  
            )  

    return kb

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("мины "))
def mines_command(message):
    """Обработчик команды мины"""
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        bot.reply_to(message, "❌ Использование: мины [ставка]\nПример: мины 1000")
        return

    try:
        bet = int(parts[1])

        if bet < 50:
            bot.reply_to(message, "❌ Минимальная ставка: 50 izzzy")
            return

        user = get_user_data(user_id)

        if bet > user["balance"]:
            bot.reply_to(message, "❌ Недостаточно средств!")
            return

        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

        # Начинаем игру с текущими настройками
        success = start_mines_game(user_id, bet)
        
        if not success:
            bot.reply_to(message, "❌ Ошибка начала игры")
            return
        
        text = (
            f"{mention}, игра началась!\n"
            f"💰 Текущий выигрыш: <b>{format_number(bet)} izzzy</b>"
        )
        
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=mines_keyboard(user_id)
        )

    except ValueError:
        bot.reply_to(message, "❌ Ставка должна быть числом!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("mines_"))
def mines_handler(call):
    """Основной обработчик игры в мины"""
    try:
        parts = call.data.split("_")
        action = parts[1]
        owner_id = int(parts[2])
        user_id = call.from_user.id

        # ЗАЩИТА: проверяем, что нажимает владелец игры
        if user_id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
            return

        u = get_user_data(user_id)
        
        # Проверяем, что игра активна
        if u.get("stage") != "mines":
            bot.answer_callback_query(call.id, "❌ Игра уже завершена!")
            return

        # ❌ ОТМЕНА ИГРЫ (в начале)
        if action == "cancel" and not u["mines_started"]:
            u["balance"] += u["mines_bet"]
            u["stage"] = "finished"
            save_casino_data()

            mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
            bot.edit_message_text(
                f"{mention}, игра отменена. Деньги возвращены на баланс.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            bot.answer_callback_query(call.id, "✅ Отменено")
            return

        # 💸 ЗАБРАТЬ ВЫИГРЫШ
        if action == "cash" and u["mines_started"]:
            win = int(u["mines_bet"] * u["mines_multiplier"])
            
            u["balance"] += win
            u["stage"] = "finished"
            save_casino_data()

            mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
            
            # Показываем все мины
            text = (
                f"🎉 {mention}\n"
                f"💰 Выигрыш: <b>{format_number(win)} izzzy</b>\n"
                f"📈 Итоговый множитель: <b>x{u['mines_multiplier']:.2f}</b>"
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=mines_keyboard(user_id, reveal_all=True, hide_buttons=True)
            )
            bot.answer_callback_query(call.id, f"Вацочек не чуствует эту игру")
            return

        # 🧩 ОТКРЫТИЕ КЛЕТКИ (число)
        try:
            cell = int(action)
            
            # Проверяем валидность клетки
            if cell < 0 or cell > 24:
                bot.answer_callback_query(call.id, "❌ Неверная клетка!")
                return
            
            # Проверяем, не открыта ли уже клетка
            if cell in u["mines_open"]:
                bot.answer_callback_query(call.id)
                return
            
            # Открываем клетку
            u["mines_open"].append(cell)
            u["mines_started"] = True

            # 💥 ПОДРЫВ НА МИНЕ
            if cell in u["mines_positions"]:
                u["stage"] = "finished"
                save_casino_data()

                mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
                
                text = (
                    f"💥 {mention}\n"
                    f"❌ Проигрыш: <b>{format_number(u['mines_bet'])} izzzy</b>"
                )
                
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=mines_keyboard(user_id, reveal_all=True, hide_buttons=True)
                )
                bot.answer_callback_query(call.id, "💥 Мина!")
                return

            # ✅ БЕЗОПАСНАЯ КЛЕТКА
            # Увеличиваем множитель
            u["mines_multiplier"] += CURRENT_MULTIPLIER
            save_casino_data()

            # Обновляем клавиатуру
            current_win = int(u["mines_bet"] * u["mines_multiplier"])
            
            text = (
                f"💎 Безопасно!\n"
                f"💰 Текущий выигрыш: <b>{format_number(current_win)} izzzy</b>"
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=mines_keyboard(user_id)
            )
            
            bot.answer_callback_query(call.id, f"Продолжай вацок")
            
        except ValueError:
            # Если action не число, это не клетка
            bot.answer_callback_query(call.id)
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике мин: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== АДМИН-КОМАНДЫ ДЛЯ НАСТРОЙКИ МИН ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить множитель"))
def admin_change_multiplier(message):
    """Команда для изменения множителя (только для админов)"""
    global CURRENT_MULTIPLIER
    
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь админом
    if user_id not in ADMIN_IDS:
        # Админ команда - просто игнорируем (бот молчит)
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, 
                        "❌ Использование: изменить множитель [новый множитель]\n"
                        "Пример: изменить множитель 0.10",
                        parse_mode="HTML")
            return
        
        new_multiplier = float(parts[2])
        
        if new_multiplier <= 0:
            bot.reply_to(message, "❌ Множитель должен быть больше 0!")
            return
        
        if new_multiplier > 10:
            bot.reply_to(message, "❌ Множитель не может быть больше 10!")
            return
        
        old_multiplier = CURRENT_MULTIPLIER
        CURRENT_MULTIPLIER = new_multiplier
        
        bot.reply_to(message, 
                    f"✅ Множитель в игре Mines изменен!\n\n"
                    f"• Старый множитель: <b>x{old_multiplier:.2f}</b>\n"
                    f"• Новый множитель: <b>x{new_multiplier:.2f}</b>",
                    parse_mode="HTML")
        
        logger.info(f"Админ {message.from_user.id} изменил множитель Mines с {old_multiplier} на {new_multiplier}")
        
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат! Используйте число (например: 0.10)")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка изменения множителя: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить мины"))
def admin_change_mines_count(message):
    """Команда для изменения количества мин (только для админов)"""
    global CURRENT_MINES_COUNT
    
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь админом
    if user_id not in ADMIN_IDS:
        # Админ команда - просто игнорируем (бот молчит)
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, 
                        "❌ Использование: изменить мины [количество]\n"
                        "Пример: изменить мины 8\n\n"
                        "Минимальное количество: 1\n"
                        "Максимальное количество: 24",
                        parse_mode="HTML")
            return
        
        new_count = int(parts[2])
        
        if new_count < 1:
            bot.reply_to(message, "❌ Количество мин должно быть не меньше 1!")
            return
        
        if new_count > 24:
            bot.reply_to(message, "❌ Количество мин не может быть больше 24!")
            return
        
        old_count = CURRENT_MINES_COUNT
        CURRENT_MINES_COUNT = new_count
        
        bot.reply_to(message, 
                    f"✅ Количество мин в игре Mines изменено!\n\n"
                    f"• Было: <b>{old_count}</b> мин\n"
                    f"• Стало: <b>{new_count}</b> мин",
                    parse_mode="HTML")
        
        logger.info(f"Админ {message.from_user.id} изменил количество мин с {old_count} на {new_count}")
        
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат! Используйте целое число")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка изменения количества мин: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "жудсдвжжа")
def admin_show_mine_settings(message):
    """Показывает текущие настройки Mines (только для админов)"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь админом
    if user_id not in ADMIN_IDS:
        # Админ команда - просто игнорируем (бот молчит)
        return
    
    bot.reply_to(message,
                f"⚙️ <b>Текущие настройки Mines:</b>\n\n"
                f"• Количество мин: <b>{CURRENT_MINES_COUNT}</b>\n"
                f"• Множитель за клетку: <b>x{CURRENT_MULTIPLIER:.2f}</b>\n"
                f"• Всего клеток: <b>25</b>\n\n"
                f"<i>Команды для изменения:</i>\n"
                f"• <code>изменить мины [количество]</code>\n"
                f"• <code>изменить множитель [значение]</code>",
                parse_mode="HTML")

print("✅ Mines 5x5 загружен с настройками:")
print(f"   • Мин: {CURRENT_MINES_COUNT}")
print(f"   • Множитель за клетку: x{CURRENT_MULTIPLIER}")
print("✅ Админ-команды для изменения настроек добавлены")

# ================== 🏎️ НОВАЯ ИГРА "РАЗГОН" (Drag Race) ==================
# Команда: разгон [ставка]
# Шанс на победу: 60%, на проигрыш: 40%

# Ссылка на гифку (прямая ссылка на файл, а не на страницу giphy)
DRAG_RACE_GIF = "https://media4.giphy.com/media/qUSujD5nvtwvdnEbwi/giphy.gif?cid=790b7611k23r4k23r4k23r4k23r4k23r4k23r4k23r4k23r4&ep=v1_gifs_search&rid=giphy.gif&ct=g"

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("разгон"))
def drag_race_game(message):
    """
    Игра 'Разгон' с гифкой и результатом через 1 секунду.
    """
    try:
        user_id = message.from_user.id
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        chat_id = message.chat.id

        # 1. Парсим ставку
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используй: <code>разгон [ставка]</code>\nПример: <code>разгон 3000</code>", parse_mode="HTML")
            return

        try:
            bet = int(parts[1])
            if bet <= 0:
                bot.reply_to(message, "❌ Ставка должна быть больше 0!")
                return
        except ValueError:
            bot.reply_to(message, "❌ Ставка должна быть числом!")
            return

        # 2. Проверяем баланс
        user_data = get_user_data(user_id)
        if user_data["balance"] < bet:
            bot.reply_to(message, "🏧 У тебя не хватает средств.", parse_mode="HTML")
            return

        # 3. Списываем ставку
        user_data["balance"] -= bet
        save_casino_data()

        # 4. Отправляем гифку (без текста)
        gif_msg = bot.send_animation(chat_id, DRAG_RACE_GIF)

        # 5. Ждем 1 секунду
        time.sleep(1)

        # 6. Удаляем гифку
        try:
            bot.delete_message(chat_id, gif_msg.message_id)
        except Exception as e:
            logger.error(f"Не удалось удалить гифку разгона: {e}")

        # 7. Генерируем результат (60% победа, 40% проигрыш)
        speed = random.randint(90, 320)  # Рандомная скорость
        is_win = random.random() < 0.5  # 60% шанс на победу

        # 8. Формируем текст результата
        if is_win:
            win_amount = bet * 2  # Ставка удвоилась
            user_data["balance"] += win_amount
            save_casino_data()
            result_text = (
                f"🏎️ {mention}, ты выиграл!\n"
                f"🚀 Скорость разгона: {speed} км/ч\n"
                f"💴 Ставка удвоилась, ты получил: {format_number(win_amount)} izzzy"
            )
        else:
            result_text = (
                f"🏎️ {mention}, ты проиграл.\n"
                f"🚀 Скорость разгона: {speed} км/ч\n"
                f"💴 Твоя ставка {format_number(bet)} izzzy сгорела."
            )

        # 9. Отправляем результат
        bot.send_message(chat_id, result_text, parse_mode="HTML")

        logger.info(f"Игра 'Разгон': {user_id} | Ставка: {bet} | Результат: {'win' if is_win else 'lose'} | Скорость: {speed}")

    except Exception as e:
        logger.error(f"Ошибка в игре 'Разгон': {e}")
        bot.reply_to(message, "❌ Произошла ошибка во время игры. Попробуйте позже.")

print("✅ Игра 'Разгон' (Drag Race) успешно добавлена!")
    
# ================== ПОЛНОСТЬЮ ПЕРЕРАБОТАННАЯ КОМАНДА "ПОМОЩЬ" / "/help" ==================
# 3 СТРАНИЦЫ ПО 2x2 КНОПКИ, ЗАЩИТА ОТ ЧУЖИХ КНОПОК
# ВО ВСЕХ РАЗДЕЛАХ ОПИСАНИЯ КОМАНД, КРОМЕ ИГР - ТАМ ТОЛЬКО КОМАНДЫ
# ДОБАВЛЕН РАЗДЕЛ "РП КОМАНДЫ"

# ---------- НАСТРОЙКА СТРАНИЦ ПОМОЩИ ----------
HELP_PAGES = {
    1: [  # Страница 1: 4 раздела
        ("📋 Команды", "help_cmds"),
        ("🕹️ Игры", "help_games"),
        ("💎 VIP", "help_vip"),
        ("👸 Тянки", "help_tyanki")
    ],
    2: [  # Страница 2: 4 раздела
        ("🐾 Питомцы", "help_pets"),
        ("💍 Система брака", "help_marriage"),
        ("⚡ Ивенты", "help_events"),
        ("💰 Донат", "help_donate")
    ],
    3: [  # Страница 3: 2 раздела (можно добавить еще, если нужно)
        ("🎭 РП команды", "help_rp"),
        # ("🔮 Будущий раздел", "help_future") # Место для нового раздела
    ]
}

# ---------- ФУНКЦИЯ ПРОВЕРКИ ВЛАДЕЛЬЦА КНОПКИ ----------
def check_help_owner(call, user_id):
    """Проверяет, что кнопку нажимает её владелец"""
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return False
    return True

# ---------- КОМАНДА /help И ПОМОЩЬ ----------
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["помощь", "/help@meow_gamechat_bot", "/help"])
def cmd_help(message):
    user_id = message.from_user.id

    # Упрощенный текст без ника и ID
    text = "🍉 <b>Панель помощи в боте</b>\n\nВыбери раздел:"

    # Страница 1: 4 раздела + кнопка Вперёд (без эмодзи)
    kb = InlineKeyboardMarkup(row_width=2)
    
    # Добавляем кнопки разделов по 2 в ряд
    for i in range(0, len(HELP_PAGES[1]), 2):
        row = []
        # Первая кнопка в ряду
        btn_text, callback = HELP_PAGES[1][i]
        row.append(InlineKeyboardButton(btn_text, callback_data=f"{callback}_{user_id}"))
        # Вторая кнопка в ряду (если есть)
        if i + 1 < len(HELP_PAGES[1]):
            btn_text2, callback2 = HELP_PAGES[1][i + 1]
            row.append(InlineKeyboardButton(btn_text2, callback_data=f"{callback2}_{user_id}"))
        kb.row(*row)
    
    # Кнопка Вперёд без эмодзи
    kb.add(InlineKeyboardButton("Вперёд", callback_data=f"help_next_{user_id}"))

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb,
        parse_mode="HTML"
    )

# ---------- ОБРАБОТЧИК КНОПКИ ВПЕРЁД (НА СТРАНИЦУ 2) ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("help_next_") and not c.data.startswith("help_next_2_"))
def help_next_page(call):
    try:
        user_id = int(call.data.rsplit("_", 1)[1])

        if not check_help_owner(call, user_id):
            return

        text = "🍉 <b>Панель помощи в боте - СТРАНИЦА 2/3</b>\n\nВыбери раздел:"

        kb = InlineKeyboardMarkup(row_width=2)

        for i in range(0, len(HELP_PAGES[2]), 2):
            row = []

            btn_text, callback = HELP_PAGES[2][i]
            row.append(
                InlineKeyboardButton(btn_text, callback_data=f"{callback}_{user_id}")
            )

            if i + 1 < len(HELP_PAGES[2]):
                btn_text2, callback2 = HELP_PAGES[2][i + 1]
                row.append(
                    InlineKeyboardButton(btn_text2, callback_data=f"{callback2}_{user_id}")
                )

            kb.row(*row)

        kb.add(
            InlineKeyboardButton("Назад", callback_data=f"help_back_{user_id}"),
            InlineKeyboardButton("Вперёд", callback_data=f"help_next_2_{user_id}")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка help_next_page: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ---------- ОБРАБОТЧИК КНОПКИ ВПЕРЁД (НА СТРАНИЦУ 3) ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("help_next_2_"))
def help_next_page_2(call):
    try:
        user_id = int(call.data.rsplit("_", 1)[1])

        if not check_help_owner(call, user_id):
            return

        text = "🍉 <b>Панель помощи в боте - СТРАНИЦА 3/3</b>\n\nВыбери раздел:"

        kb = InlineKeyboardMarkup(row_width=2)

        for i in range(0, len(HELP_PAGES[3]), 2):
            row = []

            btn_text, callback = HELP_PAGES[3][i]
            row.append(
                InlineKeyboardButton(btn_text, callback_data=f"{callback}_{user_id}")
            )

            if i + 1 < len(HELP_PAGES[3]):
                btn_text2, callback2 = HELP_PAGES[3][i + 1]
                row.append(
                    InlineKeyboardButton(btn_text2, callback_data=f"{callback2}_{user_id}")
                )

            kb.row(*row)

        kb.add(
            InlineKeyboardButton("Назад", callback_data=f"help_back_2_{user_id}")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка help_next_page_2: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ---------- ОБРАБОТЧИК КНОПКИ НАЗАД (С 3 НА 2) ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("help_back_2_"))
def help_back_page_2(call):
    try:
        user_id = int(call.data.rsplit("_", 1)[1])

        if not check_help_owner(call, user_id):
            return

        text = "🍉 <b>Панель помощи в боте - СТРАНИЦА 2/3</b>\n\nВыбери раздел:"

        kb = InlineKeyboardMarkup(row_width=2)

        for i in range(0, len(HELP_PAGES[2]), 2):
            row = []

            btn_text, callback = HELP_PAGES[2][i]
            row.append(
                InlineKeyboardButton(btn_text, callback_data=f"{callback}_{user_id}")
            )

            if i + 1 < len(HELP_PAGES[2]):
                btn_text2, callback2 = HELP_PAGES[2][i + 1]
                row.append(
                    InlineKeyboardButton(btn_text2, callback_data=f"{callback2}_{user_id}")
                )

            kb.row(*row)

        kb.add(
            InlineKeyboardButton("Назад", callback_data=f"help_back_{user_id}"),
            InlineKeyboardButton("Вперёд", callback_data=f"help_next_2_{user_id}")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка help_back_page_2: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ---------- ОБРАБОТЧИК КНОПКИ НАЗАД (СО СТРАНИЦЫ 2 НА СТРАНИЦУ 1) ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("help_back_"))
def help_back_page(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        if not check_help_owner(call, user_id):
            return
        
        text = "🍉 <b>Панель помощи в боте</b>\n\nВыбери раздел:"
        
        kb = InlineKeyboardMarkup(row_width=2)
        
        # Добавляем кнопки разделов по 2 в ряд
        for i in range(0, len(HELP_PAGES[1]), 2):
            row = []
            # Первая кнопка в ряду
            btn_text, callback = HELP_PAGES[1][i]
            row.append(InlineKeyboardButton(btn_text, callback_data=f"{callback}_{user_id}"))
            # Вторая кнопка в ряду (если есть)
            if i + 1 < len(HELP_PAGES[1]):
                btn_text2, callback2 = HELP_PAGES[1][i + 1]
                row.append(InlineKeyboardButton(btn_text2, callback_data=f"{callback2}_{user_id}"))
            kb.row(*row)
        
        # Кнопка Вперёд (без эмодзи)
        kb.add(InlineKeyboardButton("Вперёд", callback_data=f"help_next_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка help_back_page: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ---------- ОБРАБОТЧИК РАЗДЕЛОВ ПОМОЩИ ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith((
    "help_cmds_", "help_games_", "help_vip_", "help_tyanki_",
    "help_pets_", "help_marriage_", "help_events_", "help_donate_",
    "help_rp_"
)))
def help_section_handler(call):
    try:
        # Берём user_id после последнего "_"
        user_id = int(call.data.rsplit("_", 1)[1])

        if not check_help_owner(call, user_id):
            return

        # Получаем section между "help_" и "_user_id"
        section = call.data[len("help_"):].rsplit("_", 1)[0]

        if section == "cmds":
            content = HELP_CONTENT["cmds"]
        elif section == "games":
            content = HELP_CONTENT["games"]
        elif section == "vip":
            content = HELP_CONTENT["vip"]
        elif section == "tyanki":
            content = HELP_CONTENT["tyanki"]
        elif section == "pets":
            content = HELP_CONTENT["pets"]
        elif section == "marriage":
            content = HELP_CONTENT["marriage"]
        elif section == "events":
            content = HELP_CONTENT["events"]
        elif section == "donate":
            content = HELP_CONTENT["donate"].format(user_id=user_id)
        elif section == "rp":
            content = HELP_CONTENT["rp"]
        else:
            content = "❌ Раздел не найден"

        kb = InlineKeyboardMarkup()

        # Определяем страницу возврата
        if section in ["cmds", "games", "vip", "tyanki"]:
            kb.add(InlineKeyboardButton("Назад", callback_data=f"help_back_{user_id}"))
        else:
            kb.add(InlineKeyboardButton("Назад", callback_data=f"help_back_2_{user_id}"))

        bot.edit_message_text(
            content,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка help_section_handler: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ---------- ТЕКСТЫ ДЛЯ РАЗДЕЛОВ ----------
# ВО ВСЕХ РАЗДЕЛАХ ЕСТЬ ОПИСАНИЯ КОМАНД, КРОМЕ "ИГРЫ" - ТАМ ТОЛЬКО КОМАНДЫ
HELP_CONTENT = {
    # ----- КОМАНДЫ (СТРАНИЦА 1) - С ОПИСАНИЯМИ -----
    "cmds": """
📋 <b>Основные команды</b>
━━━━━━━━━━━━━━━━━━━

[💰] <b>баланс</b> / <b>б</b> — твой текущий баланс
[👥] <b>мой кабинет</b> — реферальная информация
[🏆] <b>топ</b> — топ-50 игроков по балансу
[🍉] <b>мой профиль</b> — профиль с краткой информацией
[🎁] <b>бонус</b> — ежедневный бонус (1000-15000 izzzy)
[🌰] <b>мои звезды</b> — узнать сколько заработано звезд
[📄] <b>мой налог</b> — статистика списанных сумм налоговой
[💸] <b>п [сумма]</b> — перевод денег (ответом)
[🎫] <b>промо [название]</b> — активировать промокод
[⭐] <b>задонатить [сумма]</b> — пополнить через Telegram Stars

<b>🏦MEOW BANK:</b>
[🏛] <b>открыть счёт</b> — создать банковский счет (1.2% годовых)
[📊] <b>мой счёт</b> — информация о банковском счете
[📥] <b>пополнить счёт [сумма]</b> — внести деньги на счет
[📤] <b>удалить счёт</b> — закрыть банковский счет

<b>⚙️ ПРОЧЕЕ:</b>
[🎭] <b>рп</b> — список RP-команд
[👝] <b>магазин кейсов</b> — узнать список кейсов и их цены
[👝] <b>купить кейс [номер]</b> — купить кейс за звёзды
[👝] <b>мои кейсы</b> — ваш купленный кейс
[👝] <b>открыть кейс</b> — открыть свой кейс если он есть
[🍀] <b>купить подарок</b> — купить подарок себе от имени бота
""",

    # ----- ИГРЫ (СТРАНИЦА 1) - ТОЛЬКО КОМАНДЫ, БЕЗ ОПИСАНИЙ -----
    "games": """
 <b>🕹️ Игры 🕹️</b>
━━━━━━━━━━━━━━━━━━━

[🃏] <b>играть [ставка]</b>
[🎰] <b>слот [ставка]</b>
[♦️] <b>джокер [ставка]</b>
[🍬] <b>конфетка [ставка]</b>
[🍹] <b>бомба [ставка]</b>
[☁️] <b>лестница [ставка]</b>
[🐿️] <b>белка [ставка]</b>
[🏎️] <b>разгон [ставка]</b>
[💣] <b>мины [ставка]</b>
[🔴] <b>[ставка] к/ч | Ставка на красное или чёрное</b>
[🔢] <b>[ставка] 1-36 | Ставки на числа и диапозон</b>
[⚽] <b>футбол [ставка]</b>
[🏀] <b>баскетбол [ставка]</b>
[🎯] <b>тир [ставка]</b>
[🪙] <b>рб [ставка] [орёл/решка]</b>
[🎲] <b>кубик [ставка]</b>
[⭕] <b>кнб [ставка]</b>
[🐝] <b>улей [ставка]</b>

""",

    # ----- VIP (СТРАНИЦА 1) - С ОПИСАНИЯМИ -----
    "vip": """
💎 <b>VIP Система</b>
━━━━━━━━━━━━━━━━━━━

<b>🥉 VIP 1 - Bronze</b>
[💳] <b>вип</b> / <b>vip</b> — открыть магазин VIP
[💰] <b>250,000 izzzy</b> — стоимость
[📈] +5% бонус к доходу
[⏱] 1,000 izzzy / 3 часа

<b>🥈 VIP 2 - Silver</b>
[💰] <b>500,000 izzzy</b> — стоимость
[📈] +10% бонус к доходу
[⏱] 2,500 izzzy / 3 часа

<b>🥇 VIP 3 - Gold</b>
[💰] <b>750,000 izzzy</b> — стоимость
[📈] +15% бонус к доходу
[⏱] 5,000 izzzy / 3 часа

<b>💎 VIP 4 - Platinum</b>
[💰] <b>1,000,000 izzzy</b> — стоимость
[📈] +20% бонус к доходу
[⏱] 8,000 izzzy / 3 часа

<b>🔹 VIP 5 - Diamond</b>
[💰] <b>1,250,000 izzzy</b> — стоимость
[📈] +25% бонус к доходу
[⏱] 11,000 izzzy / 3 часа

<b>👑 VIP 6 - Master</b>
[💰] <b>1,500,000 izzzy</b> — стоимость
[📈] +30% бонус к доходу
[⏱] 14,000 izzzy / 3 часа

<b>🔥 VIP 7 - Legend</b>
[💰] <b>1,750,000 izzzy</b> — стоимость
[📈] +40% бонус к доходу
[⏱] 20,000 izzzy / 3 часа

""",

    # ----- ТЯНКИ (СТРАНИЦА 1) - С ОПИСАНИЯМИ -----
    "tyanki": """
🏧 <b>Тянки</b>
━━━━━━━━━━━━━━━━━━━

<b>🛍 КОМАНДЫ:</b>
[🏪] <b>магазин тянок</b> — посмотреть всех тянок
[💝] <b>купить тянку [имя]</b> — купить тянку
[👩] <b>моя тянка</b> — информация о тянке

""",

    # ----- ПИТОМЦЫ (СТРАНИЦА 2) - С ОПИСАНИЯМИ -----
    "pets": """
🐾 <b>ПИТОМЦЫ</b>
━━━━━━━━━━━━━━━━━━━

<b>🛍 КОМАНДЫ:</b>
[🏪] <b>магазин питомцев</b> — посмотреть всех питомцев
[🐕] <b>купить питомца [номер]</b> — купить питомца
[🐈] <b>мой питомец</b> — информация о питомце

""",

    # ----- БРАК (СТРАНИЦА 2) - С ОПИСАНИЯМИ -----
    "marriage": """
💍 <b>Система брака</b>
━━━━━━━━━━━━━━━━━━━

<b>💌 КОМАНДЫ:</b>
[💞] <b>+брак</b> — предложить брак (ответом)
[💒] <b>мой брак</b> — информация о текущем браке
[📜] <b>браки</b> — список всех активных браков

""",

    # ----- ИВЕНТЫ (СТРАНИЦА 2) - С ОПИСАНИЯМИ -----
    "events": """
🏧 <b>Ивенты</b>
━━━━━━━━━━━━━━━━━━━

<b>⛏ ШАХТА:</b>
[⛏] <b>моя шахта</b> — главное меню шахты
[🔨] <b>копать</b> — добывать руду

<b>🎏 РЫБАЛКА:</b>
[🎣] <b>рыбачить</b> — Начать рыбалку
[🐟] <b>моя рыбалка</b> — Статистика рыбалок

<b>🌱 САДОВНИК:</b>
[🌱] <b>мои растения</b> — Меню садовника
[🪴] <b>посадить растение</b> — Посадить новый саженец
[🛒] <b>купить сажанец [номер]</b> — Купить саженец из магазина

""",

    # ----- ДОНАТ (СТРАНИЦА 2) - С ОПИСАНИЯМИ -----
    "donate": """
💰 <b>Донат и поддержка</b>
━━━━━━━━━━━━━━━━━━━

<b>⭐ ПОПОЛНЕНИЕ:</b>
[💸] <b>задонатить [сумма]</b> — пополнить баланс через Telegram Stars
└ Курс: 1⭐ = 10,000 izzzy

<b>🛠 ПОДДЕРЖКА:</b>
[👨‍💻] <b>Разработчик:</b> Пармиджано
[💬] <b>Чат бота:</b> @meowchatgame
[📢] <b>Канал:</b> @meow_newsbot

""",

    # ----- РП КОМАНДЫ (СТРАНИЦА 3) - ТОЛЬКО КОМАНДЫ -----
    "rp": """
<b>🎭 РП КОМАНДЫ</b>
━━━━━━━━━━━━━━━━━━━

[🤗] <b>обнять</b>
[😘] <b>поцеловать</b>
[✨] <b>погладить</b>
[🪶] <b>пощекотать</b>
[🎁] <b>подарить</b>
[👊] <b>ударить</b>
[🖐️] <b>шлёпнуть</b>
[🥊] <b>избить</b>
[🥷] <b>украсть</b>
[🍆] <b>выебать</b>
[🔥] <b>трахнуть</b>
[👅] <b>отсосать</b>
[💦] <b>отлизать</b>
[🚬] <b>закурить</b>

💬 <i>Работают только ответом на сообщение</i>
"""
}

# ---------- ВОЗВРАТ В ГЛАВНОЕ МЕНЮ (ОПЦИОНАЛЬНО) ----------
@bot.callback_query_handler(func=lambda c: c.data == "back_to_help_main")
def back_to_help_main(call):
    try:
        user_id = call.from_user.id
        
        text = "🍉 <b>Панель помощи в боте</b>\n\nВыбери раздел:"
        
        kb = InlineKeyboardMarkup(row_width=2)
        
        # Добавляем кнопки разделов по 2 в ряд
        for i in range(0, len(HELP_PAGES[1]), 2):
            row = []
            # Первая кнопка в ряду
            btn_text, callback = HELP_PAGES[1][i]
            row.append(InlineKeyboardButton(btn_text, callback_data=f"{callback}_{user_id}"))
            # Вторая кнопка в ряду (если есть)
            if i + 1 < len(HELP_PAGES[1]):
                btn_text2, callback2 = HELP_PAGES[1][i + 1]
                row.append(InlineKeyboardButton(btn_text2, callback_data=f"{callback2}_{user_id}"))
            kb.row(*row)
        
        # Кнопка Вперёд (без эмодзи)
        kb.add(InlineKeyboardButton("Вперёд", callback_data=f"help_next_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка back_to_help_main: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


# ================== ОБРАБОТКА КНОПКИ ОТМЕНЫ ==================
@bot.callback_query_handler(func=lambda call: call.data == "mines_cancel")
def callback_mines_cancel(call):
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["stage"] != "mines_playing" or not user_data.get("mines_bet"):
        bot.answer_callback_query(call.id, "❌ Игра уже завершена!")
        return
    
    bet = user_data["mines_bet"]
    
    # Возвращаем деньги на баланс
    user_data["balance"] += bet
    user_data["stage"] = "finished"
    save_casino_data()
    
    # Получаем информацию о пользователе для упоминания
    user = bot.get_chat(user_id)
    mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
    
    # Отправляем сообщение об отмене
    cancel_message = f"{mention}, ты отменил игру - <b>деньги возвращаются на твой баланс</b>"
    bot.send_message(call.message.chat.id, cancel_message, parse_mode="HTML")
    
    # Удаляем сообщение с игрой
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    bot.answer_callback_query(call.id, "✅ Игра отменена!")

# ================== ОБРАБОТКА МИН (ОБНОВЛЕННАЯ) ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith('mines_'))
def callback_mines(call):
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["stage"] != "mines_playing":
        bot.answer_callback_query(call.id, "❌ Игра уже завершена!")
        return
        
    if call.data == "mines_cashout":
        win_amount = int(user_data["mines_bet"] * user_data["mines_multiplier"])
        actual_win = add_income(user_id, win_amount, "mines")
        
        if actual_win > 0:
            text = f"💰 Вы забрали {format_number(actual_win)}$! Множитель: {user_data['mines_multiplier']}x"
        else:
            text = f"💰 Вы забрали выигрыш, но достигнут дневной лимит дохода!"
            
        user_data["stage"] = "finished"
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text
        )
        save_casino_data()
        bot.answer_callback_query(call.id)
        return
        
    if call.data == "mines_cancel":
        # Обработка уже реализована выше в отдельном обработчике
        return
        
    cell_index = int(call.data.split('_')[1])
    mines = user_data["mines_positions"]
    revealed = user_data.get("mines_revealed", [])
    
    if cell_index in revealed:
        bot.answer_callback_query(call.id, "❌ Эта клетка уже открыта!")
        return
        
    revealed.append(cell_index)
    user_data["mines_revealed"] = revealed
    
    if cell_index in mines:
        # Игрок наступил на мину
        user_data["stage"] = "finished"
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"💥 А все - деньги твои тютю, начни заново: мины (ставка) {format_number(user_data['mines_bet'])}"
        )
    else:
        # Игрок выбрал безопасную клетку
        user_data["mines_multiplier"] += config["mines_multiplier_increment"]
        safe_cells = config["mines_cells"] - config["mines_count"]
        revealed_safe = len([c for c in revealed if c not in mines])
        
        if revealed_safe >= safe_cells:
            # Все безопасные клетки открыты
            win_amount = int(user_data["mines_bet"] * user_data["mines_multiplier"])
            actual_win = add_income(user_id, win_amount, "mines")
            
            if actual_win > 0:
                text = f"🎉 Вы открыли все безопасные клетки! Выигрыш: {format_number(actual_win)}$"
            else:
                text = f"🎉 Вы открыли все безопасные клетки, но достигнут дневной лимит дохода!"
                
            user_data["stage"] = "finished"
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text
            )
        else:
            # Продолжаем игру
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"💣 Текущий множитель: {user_data['mines_multiplier']}x\nВыберите клетку:",
                reply_markup=mines_keyboard(user_id)
            )
            
    save_casino_data()
    bot.answer_callback_query(call.id)

# ================== ОРЕЛ И РЕШКА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("рб"))
def start_coin_flip(message):
    """Игра Орёл и Решка с анимацией"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Использование: рб [ставка] [орёл/решка]")
            return

        bet = int(parts[1])
        choice = parts[2].lower().replace("ё", "е")  # ✅ поддержка "орел" и "орёл"

        if choice not in ["орел", "решка"]:
            bot.reply_to(message, "❌ Нужно указать 'орёл' или 'решка'.")
            return

        user_id = message.from_user.id
        user_data = get_user_data(user_id)

        if user_data["balance"] < bet:
            bot.reply_to(message, "❌ Недостаточно средств!")
            return

        # Снимаем ставку
        user_data["balance"] -= bet
        save_casino_data()

        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

        # Отправляем начальное сообщение с анимацией
        msg = bot.send_message(
            message.chat.id,
            f"💶 <b>Подкидываю монетку...</b>",
            parse_mode="HTML"
        )

        # Ждем 2 секунды (2000 миллисекунд)
        time.sleep(1)

        # Определяем результат
        result = random.choice(["орел", "решка"])
        win = (choice == result)
        prize = bet * 2 if win else 0

        if win:
            user_data["balance"] += prize
            save_casino_data()
            result_text = f"🎉 {mention}, ты выиграл(а) <b>{format_number(prize)} izzzy</b>!\n\n<b>Ставка:</b> {choice.capitalize()}\n<b>Выпало:</b> {result.capitalize()}"
        else:
            result_text = f"😢 {mention}, ты проиграл(а) <b>{format_number(bet)} izzzy</b>\n\n<b>Ставка:</b> {choice.capitalize()}\n<b>Выпало:</b> {result.capitalize()}"

        # Меняем сообщение на результат
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=result_text,
            parse_mode="HTML"
        )

    except ValueError:
        bot.reply_to(message, "❌ Ставка должна быть числом!")
    except Exception as e:
        logger.error(f"Ошибка в игре Орёл и Решка: {e}")
        bot.reply_to(message, "❌ Ошибка при игре в Орёл и Решка")



# ----------- ОБРАБОТЧИК ТЕКСТОВОЙ КОМАНДЫ «задонатить ...» -----------
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("задонатить"))
def donate_custom(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Укажи сумму. Пример: <code>задонатить 20000</code>", parse_mode="HTML")
            return

        amount = int(parts[1])
        if amount < 2000:
            bot.reply_to(message, "❌ Минимум 2000💸 (1⭐).", parse_mode="HTML")
            return

        # Рассчитываем звёзды по курсу (1⭐ = 2000💸)
        stars = max(1, amount // 7000)
        user_id = message.from_user.id
        payment_id = create_star_payment(user_id, stars, amount)

        title = "Покупка игровой валюты"
        description = f"Пополнение счёта на {amount:,}💸"
        currency = "XTR"  # Telegram Stars

        price = types.LabeledPrice(label=f"{amount:,}💸", amount=stars)
        bot.send_invoice(
            chat_id=message.chat.id,
            title=title,
            description=description,
            invoice_payload=payment_id,
            provider_token="",  # Telegram Stars
            currency=currency,
            prices=[price],
            start_parameter="stars-donate"
        )
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат. Пример: <code>задонатить 10000</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {e}")

# ----------- ПОДТВЕРЖДЕНИЕ ПЛАТЕЖА -----------
@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(pre_q):
    bot.answer_pre_checkout_query(pre_q.id, ok=True)

# ----------- ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ -----------
@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    pay = message.successful_payment
    pid = pay.invoice_payload
    info = get_star_payment(pid)
    if not info:
        bot.send_message(message.chat.id, "⚠️ Не найден платёж в базе.")
        return

    user_id, stars, amount, status = info
    if status == "completed":
        bot.send_message(message.chat.id, "✅ Этот платёж уже был подтверждён.")
        return

    # Завершаем платёж
    complete_star_payment(pid)

    # Добавляем валюту игроку
    user_data = get_user_data(user_id)
    user_data["balance"] += amount
    save_casino_data()

    bot.send_message(
        message.chat.id,
        f"🎉 Оплата {stars}⭐ получена!\n"
        f"💰 На баланс зачислено <b>{amount:,} izzzy</b>\n"
        f"Спасибо за поддержку ❤️",
        parse_mode="HTML"
    )

# ----------- КНОПКА «НАЗАД» -----------
@bot.callback_query_handler(func=lambda c: c.data == "donate_back")
def donate_back(call):
    show_donate_menu(call.message)

# ================== ТЯНКИ ==================
def update_tyanka_stats(user_data):
    if not user_data.get("tyanka"):
        return
    
    tyanka = user_data["tyanka"]
    if "last_update" not in tyanka:
        tyanka["last_update"] = datetime.now().isoformat()
        return
    
    last_update = datetime.fromisoformat(tyanka["last_update"])
    now = datetime.now()
    hours_passed = (now - last_update).total_seconds() / 3600
    
    if hours_passed < 1:
        return
    
    # Уменьшаем сытость и начисляем прибыль
    satiety_lost = min(int(hours_passed * 2), tyanka["satiety"])
    hours_effective = min(hours_passed, tyanka["satiety"] / 2)
    
    if satiety_lost > 0:
        tyanka["satiety"] -= satiety_lost
        profit = int(hours_effective * TYANKA_DATA[tyanka["name"]]["profit_per_hour"])
        
        # Применяем лимиты дохода
        actual_profit = check_income_limits(user_data["_user_id"], profit)
        if actual_profit > 0:
            tyanka["profit_accumulated"] += actual_profit
    
    tyanka["last_update"] = now.isoformat()
    save_casino_data()

# ================== БИЗНЕС ==================
def update_business_stats(user_data):
    if not user_data.get("business"):
        return
    
    business = user_data["business"]
    if "last_update" not in business:
        business["last_update"] = datetime.now().isoformat()
        return
    
    last_update = datetime.fromisoformat(business["last_update"])
    now = datetime.now()
    hours_passed = (now - last_update).total_seconds() / 3600
    
    if hours_passed < 1:
        return
    
    # Уменьшаем материалы и начисляем прибыль
    materials_used = min(int(hours_passed), business["materials"])
    hours_effective = min(hours_passed, business["materials"])
    
    if materials_used > 0:
        business["materials"] -= materials_used
        profit = int(hours_effective * business["profit_per_hour"])
        
        # Применяем лимиты дохода
        actual_profit = check_income_limits(user_data["_user_id"], profit)
        if actual_profit > 0:
            business["profit_accumulated"] += actual_profit
    
    business["last_update"] = now.isoformat()
    save_casino_data()

# ================== ДОМА ==================
def update_house_stats(user_data):
    if not user_data.get("house"):
        return
    
    house = user_data["house"]
    if "last_update" not in house:
        house["last_update"] = datetime.now().isoformat()
        return
    
    last_update = datetime.fromisoformat(house["last_update"])
    now = datetime.now()
    hours_passed = (now - last_update).total_seconds() / 3600
    
    if hours_passed < 1:
        return
    
    # Начисляем прибыль от аренды
    profit = int(hours_passed * HOUSE_DATA[house["name"]]["profit_per_hour"])
    
    # Применяем лимиты дохода
    actual_profit = check_income_limits(user_data["_user_id"], profit)
    if actual_profit > 0:
        house["profit_accumulated"] += actual_profit
    
    house["last_update"] = now.isoformat()
    save_casino_data()

# ================== МАШИНЫ ==================
def update_car_stats(user_data):
    if not user_data.get("car"):
        return
    
    car = user_data["car"]
    if "last_update" not in car:
        car["last_update"] = datetime.now().isoformat()
        return
    
    last_update = datetime.fromisoformat(car["last_update"])
    now = datetime.now()
    hours_passed = (now - last_update).total_seconds() / 3600
    
    if hours_passed < 1:
        return
    
    # Начисляем прибыль от аренды машины
    profit = int(hours_passed * CAR_DATA[car["name"]]["profit_per_hour"])
    
    # Применяем лимиты дохода
    actual_profit = check_income_limits(user_data["_user_id"], profit)
    if actual_profit > 0:
        car["profit_accumulated"] += actual_profit
    
    car["last_update"] = now.isoformat()
    save_casino_data()

# ================== ТОП ИГРОКОВ ==================
def get_top_players():
    top_users = []
    for user_id, data in casino_data.items():
        try:
            user = bot.get_chat(user_id)
            username = user.username if user.username else user.first_name
            top_users.append((username, data["balance"]))
        except:
            top_users.append((f"User {user_id}", data["balance"]))
    
    top_users.sort(key=lambda x: x[1], reverse=True)
    return top_users[:100]

# ================== АВТОМАТИЧЕСКИЕ ПРОМОКОДЫ ==================
import random, string, threading, time, json, os
from telebot import types

PROMO_CODES_FILE = "promocodes.json"
PROMO_CHATS_FILE = "promo_chats.json"

# Загружаем сохранённые промокоды
if os.path.exists(PROMO_CODES_FILE):
    with open(PROMO_CODES_FILE, "r", encoding="utf-8") as f:
        promocodes = json.load(f)
else:
    promocodes = {}

# Загружаем чаты, куда шлются промики
if os.path.exists(PROMO_CHATS_FILE):
    with open(PROMO_CHATS_FILE, "r", encoding="utf-8") as f:
        promo_chats = json.load(f)
else:
    promo_chats = []

def save_promocodes():
    with open(PROMO_CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(promocodes, f, ensure_ascii=False, indent=2)

def save_promo_chats():
    with open(PROMO_CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(promo_chats, f, ensure_ascii=False, indent=2)

def generate_promo_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_random_promo():
    promo_name = generate_promo_code()
    while promo_name in promocodes:
        promo_name = generate_promo_code()

    amount = random.randint(100, 5000)
    activations = random.randint(1, 20)

    promocodes[promo_name] = {
        "amount": amount,
        "max_activations": activations,
        "current_activations": 0,
        "activated_by": []
    }
    save_promocodes()
    return promo_name, amount, activations

def send_promo_message(promo_name, amount, activations):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("АКТИВИРОВАТЬ", callback_data=f"activate_{promo_name}"))
    message_text = (
        f"💥 <b>Новый промокод!</b>\n\n"
        f"🎫 Код: <code>{promo_name}</code>\n"
        f"💰 Сумма: <b>{format_number(amount)} izzzy</b>\n"
        f"🔢 Активаций: <b>{activations}</b>\n\n"
        f"👉 Нажмите кнопку ниже, чтобы активировать!"
    )

    # Отправляем во все сохранённые чаты
    for chat_id in promo_chats:
        try:
            bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки промокода в чат {chat_id}: {e}")

def promo_scheduler():
    while True:
        try:
            delay = random.randint(55000, 65000)  # 1–1.5 часа
            time.sleep(delay)
            promo_name, amount, activations = create_random_promo()
            send_promo_message(promo_name, amount, activations)
        except Exception as e:
            logger.error(f"Ошибка при создании промокода: {e}")
            time.sleep(60)

@bot.callback_query_handler(func=lambda call: call.data.startswith("activate_"))
def handle_promo_activation(call):
    promo_name = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    mention = f"<a href='tg://user?id={user_id}'>{call.from_user.first_name}</a>"

    if promo_name not in promocodes:
        bot.answer_callback_query(call.id, "❌ Промокод не найден.")
        return

    promo = promocodes[promo_name]
    if user_id in promo["activated_by"]:
        bot.answer_callback_query(call.id, "бро ты уже активировал промик 😘")
        return

    if promo["current_activations"] >= promo["max_activations"]:
        bot.answer_callback_query(call.id, "⚠️ Все активации уже использованы.")
        return

    # Начисляем сумму пользователю
    user_data = get_user_data(user_id)
    user_data["balance"] += promo["amount"]
    promo["current_activations"] += 1
    promo["activated_by"].append(user_id)
    save_casino_data()
    save_promocodes()

    remaining = promo["max_activations"] - promo["current_activations"]
    bot.send_message(
        call.message.chat.id,
        f"💎 {mention} активировал промокод <b>{promo_name}</b>\n"
        f"и получил <b>{format_number(promo['amount'])} izzzy</b> 💸\n\n"
        f"🧾 Осталось активаций: <b>{remaining}</b>",
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id, "✅ Промокод успешно активирован!")

# Команда дюп
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "дюп")
def admin_generate_promo(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "Только администратор может использовать эту команду.")
        return
    promo_name, amount, activations = create_random_promo()
    send_promo_message(promo_name, amount, activations)
    bot.send_message(message.chat.id, f"✅ Промокод {promo_name} создан и отправлен!")

# ================== ПАНЕЛЬ ПРОМОКОДОВ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "панель промокода")
def promo_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У тебя нет доступа.")
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Добавить чат", callback_data="promo_add_chat"))
    kb.add(types.InlineKeyboardButton("📜 Чаты", callback_data="promo_list_chats"))
    kb.add(types.InlineKeyboardButton("🚀 Рассылка промокода", callback_data="promo_broadcast"))
    bot.send_message(message.chat.id, "🎛 <b>Панель промокодов</b>", parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "promo_add_chat")
def promo_add_chat(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    msg = bot.send_message(call.message.chat.id, "📩 Отправь ID группы, куда добавляем рассылку:")
    bot.register_next_step_handler(msg, process_add_chat)

def process_add_chat(message):
    try:
        chat_id = int(message.text.strip())
        if chat_id in promo_chats:
            bot.send_message(message.chat.id, "⚠️ Этот чат уже есть в списке.")
            return
        promo_chats.append(chat_id)
        save_promo_chats()
        bot.send_message(message.chat.id, f"<b>✅ Промокоды теперь будут кидаться ещё и в чат:</b> <code>{chat_id}</code>", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "promo_list_chats")
def promo_list_chats(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    if not promo_chats:
        bot.send_message(call.message.chat.id, "📭 Список чатов пуст.")
        return
    text = "📜 <b>Список чатов с автопромокодами:</b>\n\n"
    for i, chat_id in enumerate(promo_chats, 1):
        try:
            chat = bot.get_chat(chat_id)
            title = chat.title or "Без названия"
            username = f"@{chat.username}" if chat.username else "—"
            text += f"{i}. <b>{title}</b>\nID: <code>{chat_id}</code>\nСсылка: {username}\n\n"
        except:
            text += f"{i}. <code>{chat_id}</code> (недоступен)\n\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="promo_back"))
    bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "promo_broadcast")
def promo_broadcast(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    promo_name, amount, activations = create_random_promo()
    send_promo_message(promo_name, amount, activations)
    bot.send_message(call.message.chat.id, f"✅ Промокод {promo_name} отправлен во все чаты.")

@bot.callback_query_handler(func=lambda c: c.data == "promo_back")
def promo_back(call):
    promo_panel(call.message)

# Запуск автогенератора
threading.Thread(target=promo_scheduler, daemon=True).start()

# ================== АДМИН ПАНЕЛЬ ==================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ================== УСТАНОВКА КОМАНД ==================
commands = [
    BotCommand("start", "Приветствие пользователя"),
    BotCommand("help", "Список команд")
]
bot.set_my_commands(commands)

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def get_ai_response(prompt: str) -> str:
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        response = requests.get(f"{AI_TEXT_API}{encoded_prompt}")
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        logger.error(f"Ошибка получения AI ответа: {e}")
        return f" <b>AI Las Venturas не смог обработать запрос:</b>\n\nПроизошла ошибка при получении ответа. Пожалуйста, попробуйте позже."

# ================== ОБНОВЛЕНИЕ ВСЕХ ДОХОДОВ ==================
def update_all_incomes(user_id):
    """Обновляет доходы со всех активов пользователя"""
    user_data = get_user_data(user_id)
    update_tyanka_stats(user_data)
    update_business_stats(user_data)
    update_house_stats(user_data)
    update_car_stats(user_data)

# ================== МОДЕРАЦИЯ ==================
def get_user_warns(user_id):
    user_id_str = str(user_id)
    if user_id_str not in warns_data:
        warns_data[user_id_str] = {
            "warns": [],
            "muted_until": None
        }
    return warns_data[user_id_str]

def save_warns():
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(warns_data, f, ensure_ascii=False, indent=2)

def log_moderation(action, moderator_id, target_id, reason=None, duration=None):
    try:
        moderator = bot.get_chat(moderator_id)
        target = bot.get_chat(target_id)
        
        log_message = (f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                      f"Модератор: {moderator.first_name} (@{moderator.username if moderator.username else 'N/A'}) "
                      f"Действие: {action} "
                      f"Цель: {target.first_name} (@{target.username if target.username else 'N/A'})")
        
        if reason:
            log_message += f" Причина: {reason}"
        if duration:
            log_message += f" Длительность: {duration}"
            
        with open("moderation_logs.txt", "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
            
        logger.info(log_message)
    except Exception as e:
        logger.error(f"Ошибка логирования модерации: {e}")



# ================== КОМАНДЫ АДМИНИСТРИРОВАНИЯ ==================

def is_admin(user_id):
    """Проверка на администратора"""
    return user_id in ADMIN_IDS

def log_moderation(action, admin_id, target_id, details=""):
    """Логирование действий модерации"""
    logger.info(f"🛡 Модерация: {action} | Админ: {admin_id} | Цель: {target_id} | {details}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("меню юзера"))
def user_menu_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        target_user = None
        
        # Проверяем, есть ли реплай
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        else:
            # Пытаемся получить ID из текста команды
            parts = message.text.split()
            if len(parts) >= 3:
                target_user_id = int(parts[2])
                target_user = bot.get_chat(target_user_id)
            else:
                bot.reply_to(message, 
                           "❌ Использование:\n"
                           "• Ответьте на сообщение пользователя: <code>меню юзера</code>\n"
                           "• Или укажите ID: <code>меню юзера 123456789</code>", 
                           parse_mode="HTML")
                return
        
        if not target_user:
            bot.reply_to(message, "❌ Пользователь не найден!")
            return
            
        # Отправляем меню пользователя
        show_user_admin_menu(message.chat.id, target_user)
        
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат ID! Укажите только цифры.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка команды меню юзера: {e}")

def show_user_admin_menu(chat_id, target_user):
    """Показывает меню администрирования пользователя"""
    mention = f'<a href="tg://user?id={target_user.id}">{target_user.first_name}</a>'
    
    text = f"<b>👤 АДМИН ПАНЕЛЬ: {mention}</b>\n\nВыберите действие:"
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Полная информация", callback_data=f"admin_full_info_{target_user.id}"),
        InlineKeyboardButton("💰 Баланс", callback_data=f"admin_balance_info_{target_user.id}")
    )
    kb.add(
        InlineKeyboardButton("🎮 Игровые системы", callback_data=f"admin_games_info_{target_user.id}"),
        InlineKeyboardButton("🏦 Банк/Шахта/Мусор", callback_data=f"admin_other_info_{target_user.id}")
    )
    kb.add(
        InlineKeyboardButton("🛡 Выдать/Убрать модератора", callback_data=f"admin_mod_menu_{target_user.id}"),
        InlineKeyboardButton("💥 Селективный сброс", callback_data=f"admin_selective_reset_{target_user.id}")
    )
    
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)

# ================== ПОЛНАЯ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_full_info_"))
def admin_full_info(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        # Получаем все данные
        user_data = get_user_data(target_user_id)
        
        # ===== ОСНОВНАЯ ИНФОРМАЦИЯ =====
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        # Админ статус
        admin_status = "✅ Да" if target_user_id in ADMIN_IDS else "❌ Нет"
        
        # Префикс
        prefix_data = get_user_prefix(target_user_id)
        prefix_text = prefix_data["name"] if prefix_data else "Нет"
        
        # VIP
        vip = user_data.get("vip", {})
        vip_text = "Нет"
        if vip.get("level", 0) > 0:
            vip_info = VIP_LEVELS.get(vip["level"], {})
            vip_text = f"{vip_info.get('prefix', '⭐')} {vip_info.get('name', 'VIP')}"
        
        # ===== БАЛАНС И ФИНАНСЫ =====
        balance_text = f"{format_number(user_data.get('balance', 0))}$"
        
        # Банковский счет
        bank_account = get_bank_account(target_user_id)
        bank_text = "Нет"
        if bank_account:
            bank_text = f"{format_number(bank_account.get('balance', 0))}$ (счет: {bank_account.get('account_number', 'N/A')})"
        
        # ===== ИГРОВЫЕ СИСТЕМЫ =====
        # Тянка
        tyanka_text = "Нет"
        if user_data.get("tyanka"):
            tyanka = user_data["tyanka"]
            tyanka_text = f"{tyanka.get('name', 'Неизвестно')} ({tyanka.get('mood', 0)}%)"
        
        # Питомец
        pet_text = "Нет"
        pet_data = get_pet(target_user_id)
        if pet_data:
            pet_id, name, price, satiety, level, xp, last_update = pet_data
            pet_text = f"{name} (ур. {level}, сытость: {satiety}%)"
        
        # Машина
        car_text = "Нет"
        if user_data.get("car"):
            car = user_data["car"]
            car_text = f"{car.get('name', 'Неизвестно')}"
        
        # Бизнес
        business_text = "Нет"
        if user_data.get("business"):
            business = user_data["business"]
            business_text = f"{business.get('name', 'Неизвестно')}"
        
        # Дом
        house_text = "Нет"
        if user_data.get("house"):
            house = user_data["house"]
            house_text = f"{house.get('name', 'Неизвестно')}"
        
        # ===== ДОПОЛНИТЕЛЬНЫЕ СИСТЕМЫ =====
        # Шахта
        mining_user = get_mining_user(target_user_id)
        mining_text = "Нет данных"
        if mining_user:
            pickaxe = PICKAXES.get(mining_user.get("pickaxe_id", 1), {})
            mining_text = f"Кирка: {pickaxe.get('name', 'Нет')}, Энергия: {mining_user.get('energy', 0)}"
        
        # Мусор
        trash_inventory = get_user_trash_inventory(target_user_id)
        trash_text = f"Предметов: {len(trash_inventory.get('items', {}))}"
        
        # Новогодний календарь
        new_year_data = get_user_new_year_data(target_user_id)
        new_year_text = f"Подарков: {new_year_data.get('total_claimed', 0)}"
        
        # Рефералы
        ref_data = get_user_referral_data(target_user_id)
        ref_text = f"Рефералов: {len(ref_data.get('referrals', []))}"
        
        # ===== ФОРМИРОВАНИЕ ТЕКСТА =====
        text = (
            f"<b>📊 ПОЛНАЯ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ</b>\n\n"
            
            f"<b>👤 ОСНОВНОЕ:</b>\n"
            f"• Имя: {mention}\n"
            f"• ID: <code>{target_user_id}</code>\n"
            f"• Админ: {admin_status}\n"
            f"• Префикс: {prefix_text}\n"
            f"• VIP: {vip_text}\n\n"
            
            f"<b>💰 ФИНАНСЫ:</b>\n"
            f"• Баланс: {balance_text}\n"
            f"• Банковский счет: {bank_text}\n\n"
            
            f"<b>🎮 ИГРОВЫЕ СИСТЕМЫ:</b>\n"
            f"• Тянка: {tyanka_text}\n"
            f"• Питомец: {pet_text}\n"
            f"• Машина: {car_text}\n"
            f"• Бизнес: {business_text}\n"
            f"• Дом: {house_text}\n\n"
            
            f"<b>⚙️ ДОПОЛНИТЕЛЬНЫЕ СИСТЕМЫ:</b>\n"
            f"• Шахта: {mining_text}\n"
            f"• Мусор: {trash_text}\n"
            f"• Новогодний календарь: {new_year_text}\n"
            f"• Рефералы: {ref_text}\n\n"
            
            f"<i>Данные актуальны на {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка admin_full_info: {e}")
        
        # ================== ИНФОРМАЦИЯ О БАЛАНСЕ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_balance_info_"))
def admin_balance_info(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        # Банковский счет
        bank_account = get_bank_account(target_user_id)
        
        text = (
            f"<b>💰 ФИНАНСОВАЯ ИНФОРМАЦИЯ: {mention}</b>\n\n"
            
            f"<b>Основной баланс:</b>\n"
            f"• Текущий баланс: <code>{format_number(user_data.get('balance', 0))}$</code>\n\n"
            
            f"<b>Банковский счет:</b>\n"
        )
        
        if bank_account:
            text += (
                f"• Номер счета: <code>{bank_account.get('account_number', 'N/A')}</code>\n"
                f"• Баланс на счету: <code>{format_number(bank_account.get('balance', 0))}$</code>\n"
                f"• Начисленные проценты: <code>{format_number(bank_account.get('interest_earned', 0))}$</code>\n"
                f"• Ставка: {bank_account.get('interest_rate', 0)}% годовых\n"
                f"• Создан: {bank_account.get('created_at', 'N/A')}\n\n"
            )
        else:
            text += "• Счет не открыт\n\n"
            
        text += f"<i>ID пользователя: <code>{target_user_id}</code></i>"
        
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("💸 Изменить баланс", callback_data=f"admin_edit_balance_{target_user_id}"),
            InlineKeyboardButton("🏦 Управление банком", callback_data=f"admin_bank_manage_{target_user_id}")
        )
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# ================== ИНФОРМАЦИЯ О ИГРОВЫХ СИСТЕМАХ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_games_info_"))
def admin_games_info(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        # Тянка
        tyanka_text = "Нет"
        if user_data.get("tyanka"):
            tyanka = user_data["tyanka"]
            tyanka_text = f"{tyanka.get('name', 'Неизвестно')}\n" \
                         f"• Настроение: {tyanka.get('mood', 0)}%\n" \
                         f"• Последняя кормежка: {tyanka.get('last_fed', 'N/A')}\n"
        
        # Питомец
        pet_text = "Нет"
        pet_data = get_pet(target_user_id)
        if pet_data:
            pet_id, name, price, satiety, level, xp, last_update = pet_data
            pet_info = PETS_DATA.get(pet_id, {})
            pet_text = f"{name}\n" \
                      f"• Уровень: {level}\n" \
                      f"• Сытость: {satiety}%\n" \
                      f"• Опыт: {xp}\n" \
                      f"• Редкость: {PET_RARITY.get(pet_info.get('rarity', 1), {}).get('emoji', '❓')}"
        
        # Машина
        car_text = "Нет"
        if user_data.get("car"):
            car = user_data["car"]
            car_text = f"{car.get('name', 'Неизвестно')}\n" \
                      f"• Цена: {format_number(car.get('price', 0))}$\n" \
                      f"• Доход в час: {format_number(car.get('profit_per_hour', 0))}$"
        
        # Бизнес
        business_text = "Нет"
        if user_data.get("business"):
            business = user_data["business"]
            business_text = f"{business.get('name', 'Неизвестно')}\n" \
                          f"• Уровень: {business.get('level', 1)}\n" \
                          f"• Доход: {format_number(business.get('profit', 0))}$"
        
        # Дом
        house_text = "Нет"
        if user_data.get("house"):
            house = user_data["house"]
            house_text = f"{house.get('name', 'Неизвестно')}\n" \
                        f"• Уровень комфорта: {house.get('comfort', 1)}\n" \
                        f"• Вместимость: {house.get('capacity', 1)}"
        
        text = (
            f"<b>🎮 ИГРОВЫЕ СИСТЕМЫ: {mention}</b>\n\n"
            
            f"<b>💞 ТЯНКА:</b>\n{tyanka_text}\n"
            
            f"<b>🐾 ПИТОМЕЦ:</b>\n{pet_text}\n"
            
            f"<b>🚗 МАШИНА:</b>\n{car_text}\n"
            
            f"<b>🏢 БИЗНЕС:</b>\n{business_text}\n"
            
            f"<b>🏠 ДОМ:</b>\n{house_text}\n\n"
            
            f"<i>Для управления выберите опцию ниже</i>"
        )
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🗑 Удалить тянку", callback_data=f"admin_delete_tyanka_{target_user_id}"),
            InlineKeyboardButton("🗑 Удалить питомца", callback_data=f"admin_delete_pet_{target_user_id}")
        )
        kb.add(
            InlineKeyboardButton("🗑 Удалить машину", callback_data=f"admin_delete_car_{target_user_id}"),
            InlineKeyboardButton("🗑 Удалить бизнес", callback_data=f"admin_delete_business_{target_user_id}")
        )
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        
        # ================== ИНФОРМАЦИЯ О ДОПОЛНИТЕЛЬНЫХ СИСТЕМАХ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_other_info_"))
def admin_other_info(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        # Шахта
        mining_user = get_mining_user(target_user_id)
        mining_text = "Данные не найдены"
        if mining_user:
            pickaxe = PICKAXES.get(mining_user.get("pickaxe_id", 1), {})
            mining_text = (
                f"Кирка: {pickaxe.get('name', 'Неизвестно')}\n"
                f"• Энергия: {mining_user.get('energy', 0)}/{mining_user.get('max_energy', 50)}\n"
                f"• Прочность: {mining_user.get('pickaxe_durability', 0)}/{mining_user.get('max_durability', 100)}\n"
                f"• Добыто руд: {mining_user.get('total_ores_mined', 0)}\n"
            )
        
        # Инвентарь руд
        ores = get_user_ores(target_user_id)
        ores_text = "Руд нет"
        if ores:
            total_value = calculate_total_value(ores)
            ores_text = f"Всего видов: {len(ores)}\nОбщая стоимость: {format_number(total_value)}$"
        
        # Мусор
        trash_inventory = get_user_trash_inventory(target_user_id)
        trash_items = trash_inventory.get("items", {})
        trash_text = "Мусора нет"
        if trash_items:
            trash_value = calculate_total_value(trash_items)
            trash_text = f"Предметов: {sum(trash_items.values())}\nВидов: {len(trash_items)}\nСтоимость: {format_number(trash_value)}$"
        
        # Новогодний календарь
        new_year_data = get_user_new_year_data(target_user_id)
        new_year_text = f"Получено подарков: {new_year_data.get('total_claimed', 0)}\nПоследний: {new_year_data.get('last_claimed_date', 'Никогда')}"
        
        # Рефералы
        ref_data = get_user_referral_data(target_user_id)
        ref_text = f"Всего рефералов: {len(ref_data.get('referrals', []))}\nПригласил: {ref_data.get('referrer', 'Никто')}"
        
        text = (
            f"<b>⚙️ ДОПОЛНИТЕЛЬНЫЕ СИСТЕМЫ: {mention}</b>\n\n"
            
            f"<b>⛏️ ШАХТА:</b>\n{mining_text}\n"
            
            f"<b>🪨 ИНВЕНТАРЬ РУД:</b>\n{ores_text}\n\n"
            
            f"<b>🗑️ СБОРКА МУСОРА:</b>\n{trash_text}\n\n"
            
            f"<b>🎄 НОВОГОДНИЙ КАЛЕНДАРЬ:</b>\n{new_year_text}\n\n"
            
            f"<b>👥 РЕФЕРАЛЬНАЯ СИСТЕМА:</b>\n{ref_text}\n\n"
            
            f"<i>Для управления выберите опцию ниже</i>"
        )
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("⛏️ Сбросить шахту", callback_data=f"admin_reset_mine_{target_user_id}"),
            InlineKeyboardButton("🗑 Очистить мусор", callback_data=f"admin_clear_trash_{target_user_id}")
        )
        kb.add(
            InlineKeyboardButton("🪨 Продать все руды", callback_data=f"admin_sell_all_ores_{target_user_id}"),
            InlineKeyboardButton("🎄 Сбросить календарь", callback_data=f"admin_reset_newyear_{target_user_id}")
        )
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# ================== УПРАВЛЕНИЕ МОДЕРАТОРОМ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_mod_menu_"))
def admin_mod_menu(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        is_mod = target_user_id in ADMIN_IDS
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        text = (
            f"<b>🛡 УПРАВЛЕНИЕ МОДЕРАТОРОМ: {mention}</b>\n\n"
            f"Текущий статус: {'<b>✅ МОДЕРАТОР</b>' if is_mod else '<b>❌ НЕ МОДЕРАТОР</b>'}\n\n"
            f"Выберите действие:"
        )
        
        kb = InlineKeyboardMarkup()
        if is_mod:
            kb.add(InlineKeyboardButton("🚫 Снять с модератора", callback_data=f"admin_remove_mod_{target_user_id}"))
        else:
            kb.add(InlineKeyboardButton("✅ Назначить модератором", callback_data=f"admin_give_mod_{target_user_id}"))
        
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_give_mod_"))
def admin_give_mod(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        if target_user_id in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Пользователь уже является модератором!")
            return
        
        # Добавляем в список админов
        ADMIN_IDS.append(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = f"<b>✅ ПРАВА МОДЕРАТОРА ВЫДАНЫ: {mention}</b>\n\nПользователь получил полные права администратора в боте."
        
        # Отправляем уведомление пользователю
        try:
            bot.send_message(
                target_user_id,
                f"🎉 <b>Поздравляем!</b>\n\n"
                f"Вам были выданы права модератора в боте!\n"
                f"Теперь у вас есть доступ к административным командам.",
                parse_mode="HTML"
            )
        except:
            pass
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_mod_menu_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        log_moderation("выдача прав модератора", call.from_user.id, target_user_id)
        bot.answer_callback_query(call.id, "✅ Права модератора выданы!")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка admin_give_mod: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_remove_mod_"))
def admin_remove_mod(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        if target_user_id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Пользователь не является модератором!")
            return
        
        # Убираем из списка админов
        ADMIN_IDS.remove(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = f"<b>🚫 ПРАВА МОДЕРАТОРА СНЯТЫ: {mention}</b>\n\nПользователь больше не имеет прав администратора в боте."
        
        # Отправляем уведомление пользователю
        try:
            bot.send_message(
                target_user_id,
                f"ℹ️ <b>Уведомление</b>\n\n"
                f"Ваши права модератора в боте были отозваны.",
                parse_mode="HTML"
            )
        except:
            pass
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_mod_menu_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        log_moderation("снятие прав модератора", call.from_user.id, target_user_id)
        bot.answer_callback_query(call.id, "✅ Права модератора убраны!")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка admin_remove_mod: {e}")
        
        # ================== СЕЛЕКТИВНЫЙ СБРОС ДАННЫХ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_selective_reset_"))
def admin_selective_reset(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        text = (
            f"<b>💥 СЕЛЕКТИВНЫЙ СБРОС ДАННЫХ: {mention}</b>\n\n"
            f"Выберите какие данные вы хотите сбросить:\n\n"
            f"⚠️ <i>Внимание: Это действие необратимо!</i>"
        )
        
        kb = InlineKeyboardMarkup(row_width=2)
        
        # Финансы
        kb.add(
            InlineKeyboardButton("💰 Баланс", callback_data=f"admin_reset_balance_{target_user_id}"),
            InlineKeyboardButton("🏦 Банковский счет", callback_data=f"admin_reset_bank_{target_user_id}")
        )
        
        # Игровые системы
        kb.add(
            InlineKeyboardButton("💞 Тянка", callback_data=f"admin_reset_tyanka_{target_user_id}"),
            InlineKeyboardButton("🐾 Питомец", callback_data=f"admin_reset_pet_{target_user_id}")
        )
        kb.add(
            InlineKeyboardButton("🚗 Машина", callback_data=f"admin_reset_car_{target_user_id}"),
            InlineKeyboardButton("🏢 Бизнес", callback_data=f"admin_reset_business_{target_user_id}")
        )
        kb.add(
            InlineKeyboardButton("🏠 Дом", callback_data=f"admin_reset_house_{target_user_id}"),
            InlineKeyboardButton("⭐ VIP", callback_data=f"admin_reset_vip_{target_user_id}")
        )
        
        # Дополнительные системы
        kb.add(
            InlineKeyboardButton("⛏️ Шахта", callback_data=f"admin_reset_mine_full_{target_user_id}"),
            InlineKeyboardButton("🗑️ Мусор", callback_data=f"admin_reset_trash_full_{target_user_id}")
        )
        kb.add(
            InlineKeyboardButton("🔰 Префикс", callback_data=f"admin_reset_prefix_{target_user_id}"),
            InlineKeyboardButton("🎄 Календарь", callback_data=f"admin_reset_newyear_full_{target_user_id}")
        )
        
        # Полный сброс
        kb.add(InlineKeyboardButton("💀 ПОЛНЫЙ СБРОС ВСЕГО", callback_data=f"admin_reset_everything_{target_user_id}"))
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# ================== ФУНКЦИИ СБРОСА ==================

def confirm_reset(call, action, target_user_id, reset_function):
    """Показывает подтверждение сброса"""
    try:
        target_user = bot.get_chat(target_user_id)
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        text = (
            f"<b>⚠️ ПОДТВЕРЖДЕНИЕ СБРОСА</b>\n\n"
            f"Вы уверены, что хотите {action} для {mention}?\n\n"
            f"<i>Это действие нельзя отменить!</i>"
        )
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Да, сбросить", callback_data=reset_function),
            InlineKeyboardButton("❌ Нет, отмена", callback_data=f"admin_selective_reset_{target_user_id}")
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс баланса
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_balance_"))
def admin_reset_balance_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "сбросить баланс до начального", target_user_id, f"admin_do_reset_balance_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_balance_"))
def admin_do_reset_balance(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        old_balance = user_data["balance"]
        user_data["balance"] = START_BALANCE
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ БАЛАНС СБРОШЕН: {mention}</b>\n\n"
            f"• Старый баланс: {format_number(old_balance)}$\n"
            f"• Новый баланс: {format_number(START_BALANCE)}$\n"
            f"• Разница: {format_number(START_BALANCE - old_balance)}$"
        )
        
        log_moderation("сброс баланса", call.from_user.id, target_user_id, f"Старый: {old_balance}, Новый: {START_BALANCE}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс банковского счета
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_bank_"))
def admin_reset_bank_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить банковский счет", target_user_id, f"admin_do_reset_bank_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_bank_"))
def admin_do_reset_bank(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        target_user = bot.get_chat(target_user_id)
        
        bank_account = get_bank_account(target_user_id)
        old_balance = bank_account["balance"] if bank_account else 0
        
        # Удаляем счет
        conn = sqlite3.connect(BANK_DB)
        c = conn.cursor()
        c.execute("DELETE FROM bank_accounts WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ БАНКОВСКИЙ СЧЕТ УДАЛЕН: {mention}</b>\n\n"
            f"• Было на счету: {format_number(old_balance)}$\n"
            f"• Счет полностью удален\n\n"
            f"<i>Деньги на счету не были переведены на баланс!</i>"
        )
        
        log_moderation("удаление банковского счета", call.from_user.id, target_user_id, f"Баланс на счету: {old_balance}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс тянки
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_tyanka_"))
def admin_reset_tyanka_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить тянку", target_user_id, f"admin_do_reset_tyanka_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_tyanka_"))
def admin_do_reset_tyanka(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        had_tyanka = user_data.get("tyanka") is not None
        tyanka_name = user_data.get("tyanka", {}).get("name", "Неизвестно") if had_tyanka else None
        
        user_data["tyanka"] = None
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ ТЯНКА УДАЛЕНА: {mention}</b>\n\n"
            f"• Была тянка: {'Да' if had_tyanka else 'Нет'}\n"
            f"• Имя тянки: {tyanka_name if tyanka_name else 'Нет'}"
        )
        
        log_moderation("удаление тянки", call.from_user.id, target_user_id, f"Имя: {tyanka_name}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс питомца
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_pet_"))
def admin_reset_pet_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить питомца", target_user_id, f"admin_do_reset_pet_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_pet_"))
def admin_do_reset_pet(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        target_user = bot.get_chat(target_user_id)
        
        pet_data = get_pet(target_user_id)
        had_pet = pet_data is not None
        pet_name = pet_data[1] if had_pet else None
        
        delete_pet(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ ПИТОМЕЦ УДАЛЕН: {mention}</b>\n\n"
            f"• Был питомец: {'Да' if had_pet else 'Нет'}\n"
            f"• Имя питомца: {pet_name if pet_name else 'Нет'}"
        )
        
        log_moderation("удаление питомца", call.from_user.id, target_user_id, f"Имя: {pet_name}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        
        # Сброс машины
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_car_"))
def admin_reset_car_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить машину", target_user_id, f"admin_do_reset_car_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_car_"))
def admin_do_reset_car(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        had_car = user_data.get("car") is not None
        car_name = user_data.get("car", {}).get("name", "Неизвестно") if had_car else None
        
        user_data["car"] = None
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ МАШИНА УДАЛЕНА: {mention}</b>\n\n"
            f"• Была машина: {'Да' if had_car else 'Нет'}\n"
            f"• Модель: {car_name if car_name else 'Нет'}"
        )
        
        log_moderation("удаление машины", call.from_user.id, target_user_id, f"Модель: {car_name}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс бизнеса
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_business_"))
def admin_reset_business_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить бизнес", target_user_id, f"admin_do_reset_business_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_business_"))
def admin_do_reset_business(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        had_business = user_data.get("business") is not None
        business_name = user_data.get("business", {}).get("name", "Неизвестно") if had_business else None
        
        user_data["business"] = None
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ БИЗНЕС УДАЛЕН: {mention}</b>\n\n"
            f"• Был бизнес: {'Да' if had_business else 'Нет'}\n"
            f"• Название: {business_name if business_name else 'Нет'}"
        )
        
        log_moderation("удаление бизнеса", call.from_user.id, target_user_id, f"Название: {business_name}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс дома
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_house_"))
def admin_reset_house_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить дом", target_user_id, f"admin_do_reset_house_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_house_"))
def admin_do_reset_house(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        had_house = user_data.get("house") is not None
        house_name = user_data.get("house", {}).get("name", "Неизвестно") if had_house else None
        
        user_data["house"] = None
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ ДОМ УДАЛЕН: {mention}</b>\n\n"
            f"• Был дом: {'Да' if had_house else 'Нет'}\n"
            f"• Название: {house_name if house_name else 'Нет'}"
        )
        
        log_moderation("удаление дома", call.from_user.id, target_user_id, f"Название: {house_name}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс VIP
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_vip_"))
def admin_reset_vip_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить VIP статус", target_user_id, f"admin_do_reset_vip_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_vip_"))
def admin_do_reset_vip(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        had_vip = user_data.get("vip", {}).get("level", 0) > 0
        vip_level = user_data.get("vip", {}).get("level", 0)
        
        user_data["vip"] = {"level": 0, "expires": None}
        
        # Удаляем таймер дохода
        vip_income_timers.pop(target_user_id, None)
        
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ VIP СТАТУС УДАЛЕН: {mention}</b>\n\n"
            f"• Был VIP: {'Да' if had_vip else 'Нет'}\n"
            f"• Уровень VIP: {vip_level if had_vip else 'Нет'}"
        )
        
        log_moderation("удаление VIP", call.from_user.id, target_user_id, f"Уровень: {vip_level}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс шахты
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_mine_full_"))
def admin_reset_mine_full_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        confirm_reset(call, "полностью сбросить шахту", target_user_id, f"admin_do_reset_mine_full_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_mine_full_"))
def admin_do_reset_mine_full(call):
    try:
        target_user_id = int(call.data.split("_")[5])
        target_user = bot.get_chat(target_user_id)
        
        # Сбрасываем данные шахты
        conn = sqlite3.connect(MINING_DB)
        c = conn.cursor()
        
        # Удаляем данные пользователя
        c.execute("DELETE FROM mining_users WHERE user_id = ?", (target_user_id,))
        # Удаляем руды
        c.execute("DELETE FROM mining_ores WHERE user_id = ?", (target_user_id,))
        
        conn.commit()
        conn.close()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ ШАХТА ПОЛНОСТЬЮ СБРОШЕНА: {mention}</b>\n\n"
            f"• Данные шахты удалены\n"
            f"• Инвентарь руд очищен\n"
            f"• Прогресс сброшен до начального"
        )
        
        log_moderation("полный сброс шахты", call.from_user.id, target_user_id)
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        
        # Сброс мусора
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_trash_full_"))
def admin_reset_trash_full_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        confirm_reset(call, "очистить инвентарь мусора", target_user_id, f"admin_do_reset_trash_full_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_trash_full_"))
def admin_do_reset_trash_full(call):
    try:
        target_user_id = int(call.data.split("_")[5])
        target_user = bot.get_chat(target_user_id)
        
        # Очищаем инвентарь мусора
        update_user_trash_inventory(target_user_id, {}, 0, 0)
        
        # Останавливаем авто-сборку если активна
        AUTO_TRASH_USERS.pop(target_user_id, None)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ ИНВЕНТАРЬ МУСОРА ОЧИЩЕН: {mention}</b>\n\n"
            f"• Все предметы удалены\n"
            f"• Авто-сборка остановлена\n"
            f"• Прогресс сброшен"
        )
        
        log_moderation("очистка инвентаря мусора", call.from_user.id, target_user_id)
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс префикса
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_prefix_"))
def admin_reset_prefix_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "удалить префикс", target_user_id, f"admin_do_reset_prefix_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_prefix_"))
def admin_do_reset_prefix(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        target_user = bot.get_chat(target_user_id)
        
        prefix_data = get_user_prefix(target_user_id)
        had_prefix = prefix_data is not None
        prefix_name = prefix_data["name"] if had_prefix else None
        
        remove_user_prefix(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ ПРЕФИКС УДАЛЕН: {mention}</b>\n\n"
            f"• Был префикс: {'Да' if had_prefix else 'Нет'}\n"
            f"• Название префикса: {prefix_name if prefix_name else 'Нет'}"
        )
        
        log_moderation("удаление префикса", call.from_user.id, target_user_id, f"Префикс: {prefix_name}")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Сброс новогоднего календаря
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_newyear_full_"))
def admin_reset_newyear_full_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        confirm_reset(call, "сбросить новогодний календарь", target_user_id, f"admin_do_reset_newyear_full_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_newyear_full_"))
def admin_do_reset_newyear_full(call):
    try:
        target_user_id = int(call.data.split("_")[5])
        target_user = bot.get_chat(target_user_id)
        
        # Очищаем данные новогоднего календаря
        conn = sqlite3.connect(NEW_YEAR_DB)
        c = conn.cursor()
        c.execute("DELETE FROM new_year_calendar WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ НОВОГОДНИЙ КАЛЕНДАРЬ СБРОШЕН: {mention}</b>\n\n"
            f"• История подарков удалена\n"
            f"• Прогресс сброшен\n"
            f"• Можно получать подарки заново"
        )
        
        log_moderation("сброс новогоднего календаря", call.from_user.id, target_user_id)
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К выбору сброса", callback_data=f"admin_selective_reset_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# Полный сброс всего
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_everything_"))
def admin_reset_everything_confirm(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        confirm_reset(call, "полностью сбросить ВСЕ данные", target_user_id, f"admin_do_reset_everything_{target_user_id}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_do_reset_everything_"))
def admin_do_reset_everything(call):
    try:
        target_user_id = int(call.data.split("_")[4])
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        # Сохраняем старые значения для логов
        old_balance = user_data["balance"]
        had_tyanka = user_data.get("tyanka") is not None
        had_car = user_data.get("car") is not None
        had_business = user_data.get("business") is not None
        had_house = user_data.get("house") is not None
        vip_level = user_data.get("vip", {}).get("level", 0)
        
        # ===== СБРАСЫВАЕМ ОСНОВНЫЕ ДАННЫЕ =====
        user_data["balance"] = START_BALANCE
        user_data["tyanka"] = None
        user_data["business"] = None
        user_data["car"] = None
        user_data["house"] = None
        user_data["activated_promos"] = []
        user_data["daily_income"] = {"date": date.today().isoformat(), "amount": 0}
        user_data["daily_transfers"] = {"date": date.today().isoformat(), "amount": 0}
        user_data["vip"] = {"level": 0, "expires": None}
        
        # Удаляем таймер дохода VIP
        vip_income_timers.pop(target_user_id, None)
        
        save_casino_data()
        
        # ===== СБРАСЫВАЕМ ДОПОЛНИТЕЛЬНЫЕ СИСТЕМЫ =====
        # Питомец
        delete_pet(target_user_id)
        
        # Банковский счет
        conn = sqlite3.connect(BANK_DB)
        c = conn.cursor()
        c.execute("DELETE FROM bank_accounts WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        # Шахта
        conn = sqlite3.connect(MINING_DB)
        c = conn.cursor()
        c.execute("DELETE FROM mining_users WHERE user_id = ?", (target_user_id,))
        c.execute("DELETE FROM mining_ores WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        # Мусор
        update_user_trash_inventory(target_user_id, {}, 0, 0)
        AUTO_TRASH_USERS.pop(target_user_id, None)
        
        # Новогодний календарь
        conn = sqlite3.connect(NEW_YEAR_DB)
        c = conn.cursor()
        c.execute("DELETE FROM new_year_calendar WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        # Префикс
        remove_user_prefix(target_user_id)
        
        # Рефералы (только для этого пользователя)
        # (не удаляем реферальные связи, чтобы не ломать систему)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>💀 ВСЕ ДАННЫЕ ПОЛНОСТЬЮ СБРОШЕНЫ: {mention}</b>\n\n"
            
            f"<b>Сброшены следующие системы:</b>\n"
            f"• Баланс: {format_number(old_balance)}$ → {format_number(START_BALANCE)}$\n"
            f"• Тянка: {'Удалена' if had_tyanka else 'Не было'}\n"
            f"• Питомец: Удален\n"
            f"• Машина: {'Удалена' if had_car else 'Не было'}\n"
            f"• Бизнес: {'Удален' if had_business else 'Не было'}\n"
            f"• Дом: {'Удален' if had_house else 'Не было'}\n"
            f"• VIP: {'Удален' if vip_level > 0 else 'Не было'}\n"
            f"• Банковский счет: Удален\n"
            f"• Шахта: Полностью сброшена\n"
            f"• Мусор: Инвентарь очищен\n"
            f"• Новогодний календарь: Сброшен\n"
            f"• Префикс: Удален\n\n"
            
            f"<i>⚠️ Пользователь полностью обнулен!</i>"
        )
        
        # Формируем детали для логов
        log_details = (
            f"Баланс: {old_balance}→{START_BALANCE}, "
            f"Тянка: {had_tyanka}, "
            f"Машина: {had_car}, "
            f"Бизнес: {had_business}, "
            f"Дом: {had_house}, "
            f"VIP: {vip_level}"
        )
        log_moderation("полный сброс всех данных", call.from_user.id, target_user_id, log_details)
        
        # Отправляем уведомление пользователю
        try:
            bot.send_message(
                target_user_id,
                f"⚠️ <b>ВАЖНОЕ УВЕДОМЛЕНИЕ</b>\n\n"
                f"Все ваши данные в боте были сброшены администратором.\n"
                f"Баланс: {format_number(START_BALANCE)}$\n\n"
                f"Если это ошибка - свяжитесь с администрацией.",
                parse_mode="HTML"
            )
        except:
            pass
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ К меню пользователя", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка полного сброса данных: {e}")
        
        # ================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ УПРАВЛЕНИЯ ==================

# Изменение баланса
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_edit_balance_"))
def admin_edit_balance(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        user_data = get_user_data(target_user_id)
        
        text = (
            f"<b>💰 ИЗМЕНЕНИЕ БАЛАНСА: {mention}</b>\n\n"
            f"Текущий баланс: <code>{format_number(user_data['balance'])}$</code>\n\n"
            f"Отправьте новую сумму баланса (число):"
        )
        
        # Отправляем сообщение с запросом новой суммы
        msg = bot.send_message(call.message.chat.id, text, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_new_balance, target_user_id, call.message.message_id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

def process_new_balance(message, target_user_id, original_msg_id):
    if not is_admin(message.from_user.id):
        return
        
    try:
        # Пытаемся получить число
        try:
            new_balance = int(message.text.strip())
            if new_balance < 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "❌ Неверный формат! Укажите положительное число.")
            return
            
        user_data = get_user_data(target_user_id)
        target_user = bot.get_chat(target_user_id)
        
        old_balance = user_data["balance"]
        user_data["balance"] = new_balance
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = (
            f"<b>✅ БАЛАНС ИЗМЕНЕН: {mention}</b>\n\n"
            f"• Старый баланс: {format_number(old_balance)}$\n"
            f"• Новый баланс: {format_number(new_balance)}$\n"
            f"• Разница: {format_number(new_balance - old_balance)}$"
        )
        
        log_moderation("изменение баланса", message.from_user.id, target_user_id, 
                      f"Старый: {old_balance}, Новый: {new_balance}")
        
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        
        # Удаляем сообщения
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(message.chat.id, original_msg_id)
        except:
            pass
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# Управление банком
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_bank_manage_"))
def admin_bank_manage(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        bank_account = get_bank_account(target_user_id)
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        if not bank_account:
            text = f"<b>🏦 УПРАВЛЕНИЕ БАНКОМ: {mention}</b>\n\nУ пользователя нет банковского счета."
        else:
            text = (
                f"<b>🏦 УПРАВЛЕНИЕ БАНКОМ: {mention}</b>\n\n"
                f"Номер счета: <code>{bank_account.get('account_number', 'N/A')}</code>\n"
                f"Баланс: <code>{format_number(bank_account.get('balance', 0))}$</code>\n"
                f"Проценты начислено: <code>{format_number(bank_account.get('interest_earned', 0))}$</code>"
            )
        
        kb = InlineKeyboardMarkup()
        
        if bank_account:
            kb.add(InlineKeyboardButton("➕ Пополнить счет", callback_data=f"admin_bank_deposit_{target_user_id}"))
            kb.add(InlineKeyboardButton("➖ Снять со счета", callback_data=f"admin_bank_withdraw_{target_user_id}"))
            kb.add(InlineKeyboardButton("✏️ Изменить баланс", callback_data=f"admin_bank_set_{target_user_id}"))
        
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_balance_info_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# ================== ВОЗВРАТ К МЕНЮ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_back_"))
def admin_back(call):
    try:
        target_user_id = int(call.data.split("_")[2])
        target_user = bot.get_chat(target_user_id)
        show_user_admin_menu(call.message.chat.id, target_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")





CHAT_LINK = "https://t.me/meowchatgame"
DEV_LINK = "https://t.me/parvizwp"


def format_timedelta(td):
    minutes = td.seconds // 60
    hours = minutes // 60
    minutes %= 60
    return f"{hours}ч {minutes}м"


def user_mention(user):
    name = user.first_name or "Пользователь"
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


# ================== УЛУЧШЕННЫЙ БОНУС И ФЕРМА С ПРОВЕРКОЙ ОПИСАНИЯ ==================

# Текст, который должен быть в описании профиля для получения улучшенного бонуса
REQUIRED_BIO_TEXT = "@meow_gamechat_bot Лучший игровой чат-бот. Присоединяйся!"

def check_user_bio(user_id):
    """
    Проверяет, содержит ли описание профиля пользователя нужный текст.
    Возвращает True, если текст найден, иначе False.
    """
    try:
        # Получаем информацию о пользователе
        user = bot.get_chat(user_id)
        # В объекте chat может быть поле 'bio' (для пользователей)
        # Для групп/каналов его может не быть, но нас интересуют пользователи.
        user_bio = getattr(user, 'bio', '')
        
        if user_bio and REQUIRED_BIO_TEXT in user_bio:
            logger.info(f"✅ Пользователь {user_id} имеет нужный текст в bio.")
            return True
        else:
            logger.info(f"❌ Пользователь {user_id} НЕ имеет нужный текст в bio.")
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке bio пользователя {user_id}: {e}")
        # В случае ошибки (например, бот не имеет прав или это не пользователь)
        # считаем, что текст не найден.
        return False

def format_timedelta(td):
    """Форматирует timedelta в строку 'Xч Yм'"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}ч {minutes}м"

def user_mention(user):
    """Создает HTML-ссылку на пользователя"""
    name = user.first_name or "Пользователь"
    return f"<a href='tg://user?id={user.id}'>{name}</a>"

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "бонус")
def bonus_cmd(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    today = date.today().isoformat()

    # Проверяем, получал ли пользователь бонус сегодня
    if user_data.get("last_bonus") == today:
        now = datetime.now()
        tomorrow = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
        time_left = tomorrow - now
        # Отвечаем на сообщение пользователя
        bot.reply_to(
            message,
            f"⏳ {user_mention(message.from_user)}, ты уже получал бонус сегодня.\n"
            f"Следующий бонус будет доступен через {format_timedelta(time_left)}."
        )
        return

    # Проверяем наличие текста в описании профиля
    has_bio_text = check_user_bio(user_id)

    if has_bio_text:
        # Улучшенный бонус (10.000 - 35.000)
        bonus = random.randint(10000, 35000)
        actual_bonus = add_income(user_id, bonus, "bonus_premium")
        # Форматируем сообщение
        response_text = (
            f"🥞 {user_mention(message.from_user)}, на твой баланс был начислен бонус "
            f"<code>{format_number(actual_bonus)} izzzy</code>.\n"
            f"<b>Спасибо за продвижение нашего бота!</b>"
        )
        logger.info(f"Пользователь {user_id} получил ПРЕМИУМ бонус {actual_bonus}$")
    else:
        # Обычный бонус (1.000 - 5.000)
        bonus = random.randint(1000, 5000)
        actual_bonus = add_income(user_id, bonus, "bonus")
        # Форматируем сообщение
        response_text = (
            f"🍀 {user_mention(message.from_user)}, на твой баланс начислено "
            f"<code>{format_number(actual_bonus)} izzzy</code>.\n"
            f"Сумму ежедневного бонуса можно увеличить, вставь в описании своего аккаунта:\n"
            f"<code>{REQUIRED_BIO_TEXT}</code>"
        )
        logger.info(f"Пользователь {user_id} получил обычный бонус {actual_bonus}$")

    # Записываем дату получения бонуса
    user_data["last_bonus"] = today
    save_casino_data()

    # Отправляем ответ на сообщение пользователя
    bot.reply_to(message, response_text, parse_mode="HTML", disable_web_page_preview=True)


@bot.message_handler(func=lambda m: m.text and m.text.lower() == "ферма")
def farm_cmd(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    now = datetime.now()

    # Проверяем, не прошло ли 2 часа с последней фермы
    last_farm_str = user_data.get("last_farm")
    if last_farm_str:
        last_farm_dt = datetime.fromisoformat(last_farm_str)
        time_diff = now - last_farm_dt
        cooldown = timedelta(hours=2)
        if time_diff < cooldown:
            time_left = cooldown - time_diff
            # Отвечаем на сообщение пользователя
            bot.reply_to(
                message,
                f"🚜 {user_mention(message.from_user)}, ферма ещё отдыхает.\n"
                f"Сможешь собрать урожай через {format_timedelta(time_left)}."
            )
            return

    # Проверяем наличие текста в описании профиля для увеличения дохода с фермы
    has_bio_text = check_user_bio(user_id)

    if has_bio_text:
        # Увеличенный доход (10.000 - 35.000)
        earned = random.randint(10000, 35000)
        actual_earned = add_income(user_id, earned, "farm_premium")
        # Форматируем сообщение
        response_text = (
            f"🚜 {user_mention(message.from_user)}, ты отлично поработал на ферме и заработал "
            f"<code>{format_number(actual_earned)} izzzy</code>.\n"
            f"<b>Спасибо за продвижение нашего бота!</b>"
        )
        logger.info(f"Пользователь {user_id} получил ПРЕМИУМ доход с фермы {actual_earned}$")
    else:
        # Обычный доход (500 - 5.000)
        earned = random.randint(500, 5000)
        actual_earned = add_income(user_id, earned, "farm")
        # Форматируем сообщение
        response_text = (
            f"🚜 {user_mention(message.from_user)}, ты заработал на ферме "
            f"<code>{format_number(actual_earned)} izzzy</code>.\n"
            f"Доход с фермы можно увеличить, вставь в описании своего аккаунта:\n"
            f"<code>{REQUIRED_BIO_TEXT}</code>"
        )
        logger.info(f"Пользователь {user_id} получил обычный доход с фермы {actual_earned}$")

    # Обновляем время последней фермы
    user_data["last_farm"] = now.isoformat()
    save_casino_data()

    # Отправляем ответ на сообщение пользователя
    bot.reply_to(message, response_text, parse_mode="HTML", disable_web_page_preview=True)
            
            # ================== КРЕСТИКИ-НОЛИКИ (С ЗАЩИТОЙ) ==================
import random
import string
import time
import threading

TICTACTOE_GAMES = {}
TICTACTOE_LOCKS = {}

def generate_tictactoe_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_tictactoe_board():
    """Создает пустую доску 3x3"""
    return [
        [" ", " ", " "],
        [" ", " ", " "],
        [" ", " ", " "]
    ]

def format_tictactoe_board(board):
    """Форматирует доску для отображения"""
    emoji_map = {
        "X": "❌",
        "O": "🅾️",
        " ": "⬜"
    }
    
    lines = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = board[i][j]
            row.append(f"{emoji_map[cell]}")
        lines.append("".join(row))
    
    return "\n".join(lines)

def check_tictactoe_winner(board):
    """Проверяет победителя в крестиках-ноликах"""
    # Проверка строк
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != " ":
            return board[i][0]
    
    # Проверка столбцов
    for i in range(3):
        if board[0][i] == board[1][i] == board[2][i] != " ":
            return board[0][i]
    
    # Проверка диагоналей
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    
    # Проверка на ничью
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                return None  # Игра продолжается
    
    return "draw"  # Ничья

def get_tictactoe_keyboard(game_id, board, current_player_id, player1_id, player2_id):
    """Создает клавиатуру для игры"""
    kb = InlineKeyboardMarkup(row_width=3)
    
    # Создаем кнопки для доски
    buttons = []
    for i in range(3):
        row_buttons = []
        for j in range(3):
            cell = board[i][j]
            if cell == " ":
                # Пустая клетка - активная кнопка
                row_buttons.append(
                    InlineKeyboardButton(
                        "⬜", 
                        callback_data=f"ttt_move_{game_id}_{i}_{j}"
                    )
                )
            else:
                # Заполненная клетка - отображаем символ, но клик ничего не делает
                symbol = "❌" if cell == "X" else "🅾️"
                row_buttons.append(
                    InlineKeyboardButton(
                        symbol, 
                        callback_data="ttt_blocked"
                    )
                )
        kb.add(*row_buttons)
    
    # Добавляем кнопку отмены (могут нажимать оба игрока)
    kb.add(
        InlineKeyboardButton("🤝 Обеим игрокам удачи", callback_data=f"ttt_canаддвдсжв_{game_id}")
    )
    
    return kb

# ----------------------------- СТАРТ ИГРЫ -----------------------------
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(("кнб", "крестики", "tictactoe")))
def tictactoe_start(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        mention1 = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        # Парсим команду и ставку
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, 
                "❌ Неверный формат!\n"
                "Используйте: <code>кнб (ставка)</code> в ответ на сообщение пользователя\n"
                "Пример: <code>кнб 5000</code>",
                parse_mode="HTML"
            )
            return
        
        # Парсим ставку
        try:
            bet = int(parts[1])
            if bet < 100:
                bot.reply_to(message, "❌ Минимальная ставка: 100 izzzy")
                return
            if bet > 1000000000:
                bot.reply_to(message, "❌ Максимальная ставка: 1,000,000,000 izzzy")
                return
        except ValueError:
            bot.reply_to(message, "❌ Неверная ставка! Укажите число.")
            return
        
        # Проверяем, есть ли ответ на сообщение
        if not message.reply_to_message:
            bot.reply_to(message,
                "❌ Нужно ответить на сообщение пользователя!\n"
                "Ответьте командой <code>кнб (ставка)</code> на сообщение того, с кем хотите сыграть.",
                parse_mode="HTML"
            )
            return
        
        target_user = message.reply_to_message.from_user
        target_id = target_user.id
        
        if target_id == user_id:
            bot.reply_to(message, "❌ Нельзя играть с самим собой!")
            return
        
        if target_user.is_bot:
            bot.reply_to(message, "❌ Нельзя играть с ботом!")
            return
        
        # Проверяем баланс инициатора
        if user_data["balance"] < bet:
            bot.reply_to(message, 
                f"{mention1}, у тебя недостаточно денег чтобы играть в крестики-нолики!\n"
                f"Нужно: {bet:,} izzzy | У тебя: {user_data['balance']:,} izzzy",
                parse_mode="HTML"
            )
            return
        
        target_data = get_user_data(target_id)
        
        # Создаем игру
        game_id = generate_tictactoe_id()
        target_mention = f'<a href="tg://user?id={target_id}">{target_user.first_name}</a>'
        
        # Рандомно выбираем кто будет X, а кто O
        players = [user_id, target_id]
        random.shuffle(players)
        
        TICTACTOE_GAMES[game_id] = {
            "player1_id": user_id,  # Инициатор
            "player2_id": target_id,  # Цель
            "player_x_id": players[0],  # Крестики
            "player_o_id": players[1],  # Нолики
            "board": create_tictactoe_board(),
            "current_player": "X",  # Первым всегда ходят крестики
            "bet": bet,
            "status": "waiting",  # waiting, playing, finished
            "winner": None,
            "chat_id": message.chat.id,
            "message_id": None,
            "created_at": time.time()
        }
        
        TICTACTOE_LOCKS[game_id] = threading.Lock()
        
        # Списываем деньги у инициатора
        user_data["balance"] -= bet
        save_casino_data()
        
        # Создаем сообщение с приглашением
        text = (
            f"{target_mention}, внимание!\n"
            f"{mention1} предлагает сыграть в Крестики-Нолики.\n\n"
            f"💰 <b>Ставка: {bet:,} izzzy</b>\n\n"
            f"⏱ Приглашение действует 2 минуты"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Принять", callback_data=f"ttt_accept_{game_id}"),
            InlineKeyboardButton("Отказать", callback_data=f"ttt_decline_{game_id}")
        )
        
        msg = bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)
        
        TICTACTOE_GAMES[game_id]["message_id"] = msg.message_id
        
        # Таймер на отмену приглашения
        def timeout_invitation():
            time.sleep(120)  # 2 минуты
            if game_id in TICTACTOE_GAMES and TICTACTOE_GAMES[game_id]["status"] == "waiting":
                with TICTACTOE_LOCKS[game_id]:
                    game = TICTACTOE_GAMES.get(game_id)
                    if game and game["status"] == "waiting":
                        # Возвращаем деньги инициатору
                        get_user_data(game["player1_id"])["balance"] += game["bet"]
                        save_casino_data()
                        
                        bot.edit_message_text(
                            f"⏱ Время вышло! {mention1}, твое приглашение истекло.\n"
                            f"{bet:,} izzzy возвращены на баланс.",
                            game["chat_id"],
                            game["message_id"],
                            parse_mode="HTML"
                        )
                        
                        if game_id in TICTACTOE_GAMES:
                            del TICTACTOE_GAMES[game_id]
                        if game_id in TICTACTOE_LOCKS:
                            del TICTACTOE_LOCKS[game_id]
        
        threading.Thread(target=timeout_invitation, daemon=True).start()
        
    except Exception as e:
        logger.error(f"Ошибка старта крестиков-ноликов: {e}")
        bot.reply_to(message, "❌ Ошибка при создании игры!")

# ----------------------------- ПРИНЯТЬ ИГРУ -----------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("ttt_accept_"))
def tictactoe_accept(call):
    try:
        game_id = call.data.split("_")[2]
        
        if game_id not in TICTACTOE_GAMES:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return
        
        game = TICTACTOE_GAMES[game_id]
        
        # ВАЖНО: Проверяем, что нажимает только игрок 2 (тот, кому предложили)
        if call.from_user.id != game["player2_id"]:
            bot.answer_callback_query(call.id, "❌ Это не твое приглашение!", show_alert=True)
            return
        
        # Проверяем баланс второго игрока
        player2_data = get_user_data(game["player2_id"])
        if player2_data["balance"] < game["bet"]:
            bot.answer_callback_query(call.id, 
                f"❌ У тебя недостаточно денег!\nНужно: {game['bet']:,} izzzy", 
                show_alert=True
            )
            return
        
        # Списываем деньги у второго игрока
        player2_data["balance"] -= game["bet"]
        save_casino_data()
        
        # Меняем статус игры
        game["status"] = "playing"
        
        # Получаем информацию об игроках
        player1 = bot.get_chat(game["player1_id"])
        player2 = bot.get_chat(game["player2_id"])
        
        player_x = bot.get_chat(game["player_x_id"])
        player_o = bot.get_chat(game["player_o_id"])
        
        mention1 = f'<a href="tg://user?id={player1.id}">{player1.first_name}</a>'
        mention2 = f'<a href="tg://user?id={player2.id}">{player2.first_name}</a>'
        mention_x = f'<a href="tg://user?id={player_x.id}">{player_x.first_name}</a>'
        mention_o = f'<a href="tg://user?id={player_o.id}">{player_o.first_name}</a>'
        
        # Создаем текст для начала игры
        text = (
            f"💰 <b>Ставка: {game['bet']:,} izzzy</b>\n"
            f"🏆 <b>Банк: {game['bet'] * 2:,} izzzy</b>\n\n"
            f"❌ Крестики: {mention_x}\n"
            f"🅾️ Нолики: {mention_o}\n\n"
            f"⏰ <b>Сейчас ходят: Крестики (❌)</b>\n\n"
            f"{format_tictactoe_board(game['board'])}"
        )
        
        # Создаем клавиатуру с доской
        kb = get_tictactoe_keyboard(
            game_id, 
            game["board"], 
            game["player_x_id"], 
            game["player1_id"], 
            game["player2_id"]
        )
        
        # Обновляем сообщение
        bot.edit_message_text(
            text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id, "✅ Игра началась! Первыми ходят крестики.")
        
    except Exception as e:
        logger.error(f"Ошибка принятия игры: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ----------------------------- ОТКАЗ ОТ ИГРЫ -----------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("ttt_decline_"))
def tictactoe_decline(call):
    try:
        game_id = call.data.split("_")[2]
        
        if game_id not in TICTACTOE_GAMES:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return
        
        game = TICTACTOE_GAMES[game_id]
        
        # Проверяем, что нажимает один из игроков (игрок 1 или игрок 2)
        if call.from_user.id not in [game["player1_id"], game["player2_id"]]:
            bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
            return
        
        # Возвращаем деньги инициатору
        player1_data = get_user_data(game["player1_id"])
        player1_data["balance"] += game["bet"]
        save_casino_data()
        
        # Получаем информацию об игроках
        player1 = bot.get_chat(game["player1_id"])
        player2 = bot.get_chat(game["player2_id"])
        
        decliner = call.from_user
        decliner_mention = f'<a href="tg://user?id={decliner.id}">{decliner.first_name}</a>'
        player1_mention = f'<a href="tg://user?id={player1.id}">{player1.first_name}</a>'
        player2_mention = f'<a href="tg://user?id={player2.id}">{player2.first_name}</a>'
        
        # Определяем текст в зависимости от того, кто отказал
        if decliner.id == game["player2_id"]:  # Тот, кому предложили
            text = (
                f"{decliner_mention}, ты отказался от игры в Крестики-Нолики с {player1_mention}.\n"
                f"Ему возвращены {game['bet']:,} izzzy на баланс."
            )
        else:  # Тот, кто предложил
            text = (
                f"{decliner_mention}, ты отменил игру в Крестики-Нолики с {player2_mention}.\n"
                f"Тебе возвращены {game['bet']:,} izzzy на баланс."
            )
        
        # Обновляем сообщение
        bot.edit_message_text(
            text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML"
        )
        
        # Удаляем игру
        if game_id in TICTACTOE_GAMES:
            del TICTACTOE_GAMES[game_id]
        if game_id in TICTACTOE_LOCKS:
            del TICTACTOE_LOCKS[game_id]
        
        bot.answer_callback_query(call.id, "❌ Игра отменена")
        
    except Exception as e:
        logger.error(f"Ошибка отказа от игры: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ----------------------------- ХОД В ИГРЕ -----------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("ttt_move_"))
def tictactoe_move(call):
    try:
        parts = call.data.split("_")
        game_id = parts[2]
        row = int(parts[3])
        col = int(parts[4])
        
        if game_id not in TICTACTOE_GAMES:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return
        
        # БЛОКИРОВКА: сначала берем блокировку игры
        lock = TICTACTOE_LOCKS.get(game_id)
        if not lock:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return
        
        with lock:
            game = TICTACTOE_GAMES[game_id]
            
            # Проверяем статус игры
            if game["status"] != "playing":
                bot.answer_callback_query(call.id, "❌ Игра не активна!", show_alert=True)
                return
            
            # Определяем, чей сейчас ход
            current_symbol = game["current_player"]
            current_player_id = game["player_x_id"] if current_symbol == "X" else game["player_o_id"]
            
            # ВАЖНО: Проверяем, что нажимает только текущий игрок
            if call.from_user.id != current_player_id:
                bot.answer_callback_query(call.id, "❌ Сейчас не твой ход!", show_alert=True)
                return
            
            # Проверяем, что клетка свободна
            if game["board"][row][col] != " ":
                bot.answer_callback_query(call.id, "❌ Эта клетка уже занята!", show_alert=True)
                return
            
            # ДЕЛАЕМ ХОД (внутри блокировки, чтобы второй клик не прошел)
            game["board"][row][col] = current_symbol
            
            # Проверяем победителя
            winner = check_tictactoe_winner(game["board"])
            
            player1 = bot.get_chat(game["player1_id"])
            player2 = bot.get_chat(game["player2_id"])
            player_x = bot.get_chat(game["player_x_id"])
            player_o = bot.get_chat(game["player_o_id"])
            
            mention1 = f'<a href="tg://user?id={player1.id}">{player1.first_name}</a>'
            mention2 = f'<a href="tg://user?id={player2.id}">{player2.first_name}</a>'
            mention_x = f'<a href="tg://user?id={player_x.id}">{player_x.first_name}</a>'
            mention_o = f'<a href="tg://user?id={player_o.id}">{player_o.first_name}</a>'
            
            if winner:
                # Игра окончена
                game["status"] = "finished"
                game["winner"] = winner
                
                if winner == "draw":
                    # Ничья - возвращаем деньги обоим
                    get_user_data(game["player1_id"])["balance"] += game["bet"]
                    get_user_data(game["player2_id"])["balance"] += game["bet"]
                    save_casino_data()
                    
                    text = (
                        f"🎮 <b>Игра была закончена ничьей</b>\n\n"
                        f"💰 Каждому возвращено по {game['bet']:,} izzzy\n\n"
                        f"{format_tictactoe_board(game['board'])}\n\n"
                        f"❌ {mention_x}\n"
                        f"🅾️ {mention_o}"
                    )
                    
                else:
                    # Есть победитель
                    winner_id = game["player_x_id"] if winner == "X" else game["player_o_id"]
                    loser_id = game["player_o_id"] if winner == "X" else game["player_x_id"]
                    
                    winner_user = bot.get_chat(winner_id)
                    loser_user = bot.get_chat(loser_id)
                    
                    winner_mention = f'<a href="tg://user?id={winner_id}">{winner_user.first_name}</a>'
                    loser_mention = f'<a href="tg://user?id={loser_id}">{loser_user.first_name}</a>'
                    
                    # Начисляем выигрыш
                    get_user_data(winner_id)["balance"] += game["bet"] * 2
                    save_casino_data()
                    
                    text = (
                        f"🎮 <b>Игра закончилась - победитель есть</b>\n\n"
                        f"{winner_mention}, поздравляю! Ты выиграл {loser_mention} и получил {game['bet'] * 2:,} izzzy\n\n"
                        f"{format_tictactoe_board(game['board'])}\n\n"
                        f"❌ {mention_x}\n"
                        f"🅾️ {mention_o}"
                    )
                
                # Удаляем клавиатуру
                bot.edit_message_text(
                    text,
                    game["chat_id"],
                    game["message_id"],
                    parse_mode="HTML"
                )
                
                # Очищаем игру
                if game_id in TICTACTOE_GAMES:
                    del TICTACTOE_GAMES[game_id]
                if game_id in TICTACTOE_LOCKS:
                    del TICTACTOE_LOCKS[game_id]
                
                bot.answer_callback_query(call.id, "🎮 Игра окончена!")
                
            else:
                # Меняем ход
                next_symbol = "O" if current_symbol == "X" else "X"
                game["current_player"] = next_symbol
                
                next_player_id = game["player_x_id"] if next_symbol == "X" else game["player_o_id"]
                next_player = bot.get_chat(next_player_id)
                next_mention = f'<a href="tg://user?id={next_player_id}">{next_player.first_name}</a>'
                
                # Обновляем сообщение
                next_symbol_emoji = "❌" if next_symbol == "X" else "🅾️"
                
                text = (
                    f"🎮 <b>Игра в ❌Крестики - Нолики🅾️</b>\n\n"
                    f"💰 <b>Ставка: {game['bet']:,} izzzy</b>\n"
                    f"🏆 <b>Банк: {game['bet'] * 2:,} izzzy</b>\n\n"
                    f"❌ Крестики: {mention_x}\n"
                    f"🅾️ Нолики: {mention_o}\n\n"
                    f"⏰ <b>Сейчас ходят: {next_symbol} ({next_symbol_emoji})</b>\n"
                    f"Ходит: {next_mention}\n\n"
                    f"{format_tictactoe_board(game['board'])}"
                )
                
                # Создаем новую клавиатуру
                kb = get_tictactoe_keyboard(
                    game_id, 
                    game["board"], 
                    next_player_id, 
                    game["player1_id"], 
                    game["player2_id"]
                )
                
                # ОБНОВЛЯЕМ СООБЩЕНИЕ (все еще внутри блокировки)
                bot.edit_message_text(
                    text,
                    game["chat_id"],
                    game["message_id"],
                    parse_mode="HTML",
                    reply_markup=kb
                )
                
                bot.answer_callback_query(call.id, f"✅ Ход сделан! Теперь ходят {next_symbol}")
        
    except Exception as e:
        logger.error(f"Ошибка хода в крестиках-ноликах: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ----------------------------- ОТМЕНА ИГРЫ В ПРОЦЕССЕ -----------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("ttt_cancel_"))
def tictactoe_cancel(call):
    try:
        game_id = call.data.split("_")[2]
        
        if game_id not in TICTACTOE_GAMES:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!", show_alert=True)
            return
        
        game = TICTACTOE_GAMES[game_id]
        
        # Проверяем, что нажимает один из игроков (только игрок 1 или игрок 2)
        if call.from_user.id not in [game["player1_id"], game["player2_id"]]:
            bot.answer_callback_query(call.id, "❌ Это не твоя игра!", show_alert=True)
            return
        
        # Возвращаем деньги обоим игрокам (ничья)
        get_user_data(game["player1_id"])["balance"] += game["bet"]
        get_user_data(game["player2_id"])["balance"] += game["bet"]
        save_casino_data()
        
        player1 = bot.get_chat(game["player1_id"])
        player2 = bot.get_chat(game["player2_id"])
        
        canceller_mention = f'<a href="tg://user?id={call.from_user.id}">{call.from_user.first_name}</a>'
        player1_mention = f'<a href="tg://user?id={player1.id}">{player1.first_name}</a>'
        player2_mention = f'<a href="tg://user?id={player2.id}">{player2.first_name}</a>'
        
        # Определяем текст
        if call.from_user.id == game["player1_id"]:
            text = f"{canceller_mention} отменил игру с {player2_mention}. Деньги возвращены обоим игрокам."
        else:
            text = f"{canceller_mention} отменил игру с {player1_mention}. Деньги возвращены обоим игрокам."
        
        # Обновляем сообщение
        bot.edit_message_text(
            text,
            game["chat_id"],
            game["message_id"],
            parse_mode="HTML"
        )
        
        # Удаляем игру
        if game_id in TICTACTOE_GAMES:
            del TICTACTOE_GAMES[game_id]
        if game_id in TICTACTOE_LOCKS:
            del TICTACTOE_LOCKS[game_id]
        
        bot.answer_callback_query(call.id, "❌ Игра отменена")
        
    except Exception as e:
        logger.error(f"Ошибка отмены игры: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ----------------------------- ЗАЩИТА ОТ ПОСТОРОННИХ НАЖАТИЙ -----------------------------
@bot.callback_query_handler(func=lambda c: c.data == "ttt_blocked")
def tictactoe_blocked(call):
    """Обработчик для заблокированных кнопок (занятые клетки)"""
    bot.answer_callback_query(call.id, "❌ Эта клетка уже занята!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ttt_none"))
def tictactoe_none(call):
    """Пустой обработчик для неактивных кнопок"""
    bot.answer_callback_query(call.id)  # Просто закрываем уведомление

print("✅ Крестики-нолики загружены!")
            
          


# ================== АДМИН КОМАНДЫ ==================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def ensure_admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ <b>У тебя нет прав администратора.</b>", parse_mode="HTML")
        return False
    return True


# ---------- ВЫДАТЬ ДЕНЬГИ ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith('выдать '))
def admin_give_money(message):
    if not ensure_admin(message):
        return
        
    try:
        parts = message.text.split()
        if message.reply_to_message:
            recipient_id = message.reply_to_message.from_user.id
            amount = int(parts[1])
            recipient_name = f'<a href="tg://user?id={recipient_id}">{message.reply_to_message.from_user.first_name}</a>'
        else:
            recipient_id = int(parts[1])
            amount = int(parts[2])
            recipient_name = f'пользователю <code>{recipient_id}</code>'
            
        add_income(recipient_id, amount, "admin_gift")
        
        admin_name = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        bot.reply_to(message, f"🎁 <b>АДМИНИСТРАТОР</b> {admin_name}\n\n"
                              f"✅ <b>Выдал деньги:</b> {recipient_name}\n"
                              f"💵 <b>Сумма:</b> <code>{format_number(amount)}$</code>", 
                    parse_mode="HTML")
        logger.info(f"Админ {message.from_user.username} выдал {amount} пользователю {recipient_id}")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выдачи денег!")
        logger.error(f"Ошибка выдачи денег: {e}")


# ---------- УБРАТЬ ДЕНЬГИ ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith('убрать '))
def admin_take_money(message):
    if not ensure_admin(message):
        return
    try:
        parts = message.text.split()
        if message.reply_to_message:
            recipient_id = message.reply_to_message.from_user.id
            amount = int(parts[1])
            recipient_name = f'<a href="tg://user?id={recipient_id}">{message.reply_to_message.from_user.first_name}</a>'
        else:
            recipient_id = int(parts[1])
            amount = int(parts[2])
            recipient_name = f'пользователю <code>{recipient_id}</code>'
            
        data = get_user_data(recipient_id)
        amount = min(amount, data.get("balance", 0))
        data["balance"] -= amount
        save_casino_data()

        admin_name = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        bot.reply_to(message, f"🎁 <b>АДМИНИСТРАТОР</b> {admin_name}\n\n"
                              f"✅ <b>Убрал деньги у:</b> {recipient_name}\n"
                              f"💵 <b>Сумма:</b> <code>{format_number(amount)}$</code>", 
                    parse_mode="HTML")
        logger.info(f"Админ {message.from_user.username} убрал {amount} у пользователя {recipient_id}")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изъятия денег!")
        logger.error(f"Ошибка изъятия денег: {e}")


# ---------- СОЗДАТЬ ПРОМО ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith('создать промо '))
def create_promo(message):
    if not ensure_admin(message):
        return
    try:
        parts = message.text.split()
        promo_name = parts[2]
        amount = int(parts[3])
        activations = int(parts[4])
        if promo_name in promocodes:
            bot.reply_to(message, "❌ Промокод с таким именем уже существует!", parse_mode="HTML")
            return
        promocodes[promo_name] = {"amount": amount, "max_activations": activations,
                                  "current_activations": 0, "activated_by": []}
        save_promocodes()
        admin_name = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        bot.reply_to(message, f"🎫 <b>АДМИНИСТРАТОР</b> {admin_name}\n\n"
                              f"✅ <b>Создан промокод:</b> <code>{promo_name}</code>\n"
                              f"💵 <b>Сумма:</b> <code>{format_number(amount)}$</code>\n"
                              f"🔢 <b>Активаций:</b> <code>{activations}</code>",
                    parse_mode="HTML")
        logger.info(f"Админ {message.from_user.username} создал промокод {promo_name}")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка создания промокода!", parse_mode="HTML")
        logger.error(f"Ошибка создания промокода: {e}")


# ---------- ВЫДАТЬ / УДАЛИТЬ ТЯНКУ ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith('дать тянку '))
def admin_give_tyanka(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        parts = message.text.split()
        tyanka_name = parts[2]
        if tyanka_name not in TYANKA_DATA:
            bot.reply_to(message, f"❌ Такой тянки нет!\n\n"
                                  f"<b>Доступные:</b>\n" +
                       "\n".join([f"• <code>{n}</code>" for n in TYANKA_DATA.keys()]), parse_mode="HTML")
            return
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if data.get("tyanka"):
            bot.reply_to(message, "❌ У пользователя уже есть тянка!", parse_mode="HTML")
            return
        data["tyanka"] = {"name": tyanka_name, "satiety": 100,
                          "last_update": datetime.now().isoformat(), "profit_accumulated": 0}
        save_casino_data()
        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'
        bot.reply_to(message, f"👩‍❤️‍👨 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
                              f"✅ <b>Выдал тянку:</b> {user}\n"
                              f"🏷️ <b>Имя:</b> <code>{tyanka_name}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выдачи тянки!", parse_mode="HTML")
        logger.error(f"Ошибка выдачи тянки: {e}")


@bot.message_handler(func=lambda m: m.text and m.text.startswith('удалить тянку'))
def admin_take_tyanka(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if not data.get("tyanka"):
            bot.reply_to(message, "❌ У пользователя нет тянки!", parse_mode="HTML")
            return
        name = data["tyanka"]["name"]
        data["tyanka"] = None
        save_casino_data()
        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'
        bot.reply_to(message, f"👩‍❤️‍👨 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
                              f"❌ <b>Забрал тянку у:</b> {user}\n"
                              f"🏷️ <b>Имя тянки:</b> <code>{name}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изъятия тянки!", parse_mode="HTML")
        logger.error(f"Ошибка изъятия тянки: {e}")


# ---------- ДОМА ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith('дать дом '))
def admin_give_house(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        house_name = " ".join(message.text.split()[2:])
        found = next((n for n in HOUSE_DATA if house_name.lower() in n.lower()), None)
        if not found:
            bot.reply_to(message, f"❌ Такого дома нет!\n\n" +
                                  "\n".join([f"• <code>{n}</code>" for n in HOUSE_DATA.keys()]), parse_mode="HTML")
            return
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if data.get("house"):
            bot.reply_to(message, "❌ У пользователя уже есть дом!", parse_mode="HTML")
            return
        data["house"] = {"name": found, "last_update": datetime.now().isoformat(), "profit_accumulated": 0}
        save_casino_data()
        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'
        bot.reply_to(message, f"🏠 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
                              f"✅ <b>Выдал дом:</b> {user}\n"
                              f"🏠 <b>Название:</b> <code>{found}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выдачи дома!", parse_mode="HTML")
        logger.error(f"Ошибка выдачи дома: {e}")


@bot.message_handler(func=lambda m: m.text and m.text.startswith('удалить дом'))
def admin_take_house(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if not data.get("house"):
            bot.reply_to(message, "❌ У пользователя нет дома!", parse_mode="HTML")
            return
        name = data["house"]["name"]
        data["house"] = None
        save_casino_data()
        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'
        bot.reply_to(message, f"🏠 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
                              f"❌ <b>Забрал дом у:</b> {user}\n"
                              f"🏠 <b>Название:</b> <code>{name}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изъятия дома!", parse_mode="HTML")
        logger.error(f"Ошибка изъятия дома: {e}")


# ---------- МАШИНЫ ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith('дать машину '))
def admin_give_car(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        car_name = " ".join(message.text.split()[2:])
        found = next((n for n in CAR_DATA if car_name.lower() in n.lower()), None)
        if not found:
            bot.reply_to(message, f"❌ Такой машины нет!\n\n" +
                                  "\n".join([f"• <code>{n}</code>" for n in CAR_DATA.keys()]), parse_mode="HTML")
            return
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if data.get("car"):
            bot.reply_to(message, "❌ У пользователя уже есть машина!", parse_mode="HTML")
            return
        data["car"] = {"name": found, "last_update": datetime.now().isoformat(), "profit_accumulated": 0}
        save_casino_data()
        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'
        bot.reply_to(message, f"🚗 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
                              f"✅ <b>Выдал машину:</b> {user}\n"
                              f"🚗 <b>Модель:</b> <code>{found}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выдачи машины!", parse_mode="HTML")
        logger.error(f"Ошибка выдачи машины: {e}")


@bot.message_handler(func=lambda m: m.text and m.text.startswith('удалить машину'))
def admin_take_car(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if not data.get("car"):
            bot.reply_to(message, "❌ У пользователя нет машины!", parse_mode="HTML")
            return
        name = data["car"]["name"]
        data["car"] = None
        save_casino_data()
        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'
        bot.reply_to(message, f"🚗 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
                              f"❌ <b>Забрал машину у:</b> {user}\n"
                              f"🚗 <b>Модель:</b> <code>{name}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изъятия машины!", parse_mode="HTML")
        logger.error(f"Ошибка изъятия машины: {e}")


# ---------- БИЗНЕС ----------
@bot.message_handler(func=lambda m: m.text and m.text.startswith('дать бизнес '))
def admin_give_business(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        biz_name = " ".join(message.text.split()[2:])
        if biz_name not in BUSINESS_DATA:
            bot.reply_to(message, f"❌ Такого бизнеса нет!\n\n" +
                                  "\n".join([f"• <code>{n}</code>" for n in BUSINESS_DATA.keys()]), parse_mode="HTML")
            return
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if data.get("business"):
            bot.reply_to(message, "❌ У пользователя уже есть бизнес!", parse_mode="HTML")
            return
        info = BUSINESS_DATA[biz_name]
        data["business"] = {"name": biz_name, "profit_per_hour": info["profit_per_hour"],
                            "materials": 100, "last_update": datetime.now().isoformat(), "profit_accumulated": 0}
        save_casino_data()
        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'
        bot.reply_to(message, f"🏢 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
                              f"✅ <b>Выдал бизнес:</b> {user}\n"
                              f"🏢 <b>Название:</b> <code>{biz_name}</code>\n"
                              f"💵 <b>Прибыль в час:</b> <code>{format_number(info['profit_per_hour'])}$</code>",
                     parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выдачи бизнеса!", parse_mode="HTML")
        logger.error(f"Ошибка выдачи бизнеса: {e}")


@bot.message_handler(func=lambda m: m.text and m.text.startswith('удалить бизнес'))
def admin_take_business(message):
    if not ensure_admin(message):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!", parse_mode="HTML")
        return
    try:
        rid = message.reply_to_message.from_user.id
        data = get_user_data(rid)
        if not data.get("business"):
            bot.reply_to(message, "❌ У пользователя нет бизнеса!", parse_mode="HTML")
            return

        name = data["business"]["name"]
        data["business"] = None
        save_casino_data()

        admin = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        user = f'<a href="tg://user?id={rid}">{message.reply_to_message.from_user.first_name}</a>'

        bot.reply_to(
            message,
            f"🏢 <b>АДМИНИСТРАТОР</b> {admin}\n\n"
            f"❌ <b>Забрал бизнес у:</b> {user}\n"
            f"🏢 <b>Название бизнеса:</b> <code>{name}</code>",
            parse_mode="HTML"
        )

        logger.info(f"Админ {message.from_user.username} забрал бизнес {name} у пользователя {rid}")

    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изъятия бизнеса!", parse_mode="HTML")
        logger.error(f"Ошибка изъятия бизнеса: {e}")
        
# ================== ОПТИМИЗИРОВАННАЯ ПРОВЕРКА УХОДА ТЯНКИ ==================
def check_tyanka_leave(user_id, user_data):
    """Проверяет, не ушла ли тянка (без отправки сообщений для оптимизации)"""
    tyanka = user_data.get("tyanka")
    if not tyanka:
        return False

    # Быстрая проверка условий ухода (только сытость)
    if tyanka["satiety"] <= 0:
        # Просто удаляем тянку без уведомлений
        user_data["tyanka"] = None
        save_casino_data()
        logger.info(f"Тянка ушла от пользователя {user_id} (сытость: {tyanka['satiety']})")
        return True

    return False

# ================== ОПТИМИЗИРОВАННОЕ ОБНОВЛЕНИЕ СТАТИСТИКИ ТЯНКИ ==================
def update_tyanka_stats(user_data):
    """Обновляет сытость и накапливает доход (оптимизированная версия)"""
    tyanka = user_data.get("tyanka")
    if not tyanka:
        return

    # Быстрая инициализация полей если их нет (для совместимости)
    if "profit_accumulated" not in tyanka:
        tyanka["profit_accumulated"] = 0
    if "total_earned" not in tyanka:
        tyanka["total_earned"] = 0

    if "last_update" not in tyanka:
        tyanka["last_update"] = datetime.now().isoformat()
        return

    last_update = datetime.fromisoformat(tyanka["last_update"])
    now = datetime.now()
    hours_passed = (now - last_update).total_seconds() / 3600

    if hours_passed < 0.01:  # Меньше 36 секунд - не обновляем
        return

    tyanka_info = TYANKA_DATA[tyanka["name"]]

    # Быстрое обновление показателей (только сытость)
    satiety_lost = min(int(hours_passed * 3), tyanka["satiety"])

    if satiety_lost > 0:
        tyanka["satiety"] -= satiety_lost

    # Прибыль только если сытость > 0
    if tyanka["satiety"] > 0:
        profit = int(tyanka_info["profit_per_hour"] * hours_passed)
        tyanka["profit_accumulated"] += profit

    tyanka["last_update"] = now.isoformat()

    # Быстрая проверка ухода (без сообщений)
    if tyanka["satiety"] <= 0:
        user_data["tyanka"] = None
        logger.info(f"Тянка автоматически ушла (сытость: {tyanka['satiety']})")

# ================== МАГАЗИН ТЯНОК С ПАГИНАЦИЕЙ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["магазин тянок", "тянки"])
def tyanka_shop(message):
    user_id = message.from_user.id

    # Разделяем тянок на две страницы
    tyanka_list = list(TYANKA_DATA.keys())
    half = len(tyanka_list) // 2
    page1_tyanki = tyanka_list[:half]
    page2_tyanki = tyanka_list[half:]

    text = "💖 <b>Магазин тянок</b>\n\n"

    # Показываем первую страницу тянок
    for name in page1_tyanki:
        data = TYANKA_DATA[name]
        text += (
            f"<b>{name.capitalize()}</b>\n"
            f"Цена: <code>{format_number(data['price'])} izzzy</code>\n"
            f"Доход/час: <code>{format_number(data['profit_per_hour'])} izzzy</code>\n"
            f"Кормление: <code>{format_number(data['feed_cost'])} izzzy</code>\n"
            f"{data['rarity']}\n\n"
        )

    text += "<i>Нажми на кнопку ниже чтобы купить тянку</i>"

    # Создаем клавиатуру для первой страницы
    kb = InlineKeyboardMarkup(row_width=2)

    # Создаем кнопки для первой страницы
    buttons_row1 = []
    for name in page1_tyanki[:2]:  # Первые 2 тянки в первом ряду
        buttons_row1.append(InlineKeyboardButton(name.capitalize(), callback_data=f"tyanka_buy_{name}"))

    if buttons_row1:
        if len(buttons_row1) == 2:
            kb.row(buttons_row1[0], buttons_row1[1])
        else:
            kb.row(buttons_row1[0])

    # Второй ряд для первой страницы (если есть)
    if len(page1_tyanki) > 2:
        buttons_row2 = []
        for name in page1_tyanki[2:4]:  # Следующие 2 тянки
            buttons_row2.append(InlineKeyboardButton(name.capitalize(), callback_data=f"tyanka_buy_{name}"))

        if len(buttons_row2) == 2:
            kb.row(buttons_row2[0], buttons_row2[1])
        elif buttons_row2:
            kb.row(buttons_row2[0])

    # Если есть вторая страница - кнопка "Далее"
    if page2_tyanki:
        kb.add(InlineKeyboardButton("Далее", callback_data=f"tyanka_page_2_{user_id}"))

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)


# ================== ОБРАБОТЧИК ПАГИНАЦИИ ТЯНОК ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_page_"))
def callback_tyanka_pagination(call):
    try:
        user_id = int(call.data.split("_")[3])

        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return

        page_num = int(call.data.split("_")[2])
        show_tyanka_page(call, page_num, user_id)

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Ошибка в пагинации тянок: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


def show_tyanka_page(call, page_num, user_id):
    """Показывает страницу с тянками"""
    # Разделяем тянок на две страницы
    tyanka_list = list(TYANKA_DATA.keys())
    half = len(tyanka_list) // 2
    page1_tyanki = tyanka_list[:half]
    page2_tyanki = tyanka_list[half:]

    text = "💖 <b>Магазин тянок</b>\n\n"

    # Показываем тянок в зависимости от страницы
    if page_num == 2 and page2_tyanki:
        current_tyanki = page2_tyanki
    else:
        current_tyanki = page1_tyanki
        page_num = 1

    for name in current_tyanki:
        data = TYANKA_DATA[name]
        text += (
            f"<b>{name.capitalize()}</b>\n"
            f"Цена: <code>{format_number(data['price'])} izzzy</code>\n"
            f"Доход/час: <code>{format_number(data['profit_per_hour'])} izzzy</code>\n"
            f"Кормление: <code>{format_number(data['feed_cost'])} izzzy</code>\n"
            f"{data['rarity']}\n\n"
        )

    text += "<i>Нажми на кнопку ниже чтобы купить тянку</i>"

    # Создаем клавиатуру
    kb = InlineKeyboardMarkup(row_width=2)

    # Создаем кнопки для текущей страницы
    for i in range(0, len(current_tyanki), 2):
        row_buttons = []
        # Первая кнопка в ряду
        name1 = current_tyanki[i]
        row_buttons.append(InlineKeyboardButton(name1.capitalize(), callback_data=f"tyanka_buy_{name1}"))

        # Вторая кнопка в ряду (если есть)
        if i + 1 < len(current_tyanki):
            name2 = current_tyanki[i + 1]
            row_buttons.append(InlineKeyboardButton(name2.capitalize(), callback_data=f"tyanka_buy_{name2}"))

        if len(row_buttons) == 2:
            kb.row(row_buttons[0], row_buttons[1])
        else:
            kb.row(row_buttons[0])

    # Кнопки навигации
    nav_buttons = []

    if page_num == 2 and page1_tyanki:
        # На второй странице - только кнопка "Назад"
        nav_buttons.append(InlineKeyboardButton("Назад", callback_data=f"tyanka_page_1_{user_id}"))
    elif page_num == 1 and page2_tyanki:
        # На первой странице - только кнопка "Далее"
        nav_buttons.append(InlineKeyboardButton("Далее", callback_data=f"tyanka_page_2_{user_id}"))
    elif page1_tyanki and page2_tyanki:
        # Если есть обе страницы - обе кнопки
        nav_buttons.append(InlineKeyboardButton("Назад", callback_data=f"tyanka_page_1_{user_id}"))
        nav_buttons.append(InlineKeyboardButton("Далее", callback_data=f"tyanka_page_2_{user_id}"))

    if nav_buttons:
        kb.row(*nav_buttons)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_buy_"))
def buy_tyanka_callback(call):
    try:
        tyanka_name = call.data.split("_")[2]

        if tyanka_name not in TYANKA_DATA:
            bot.answer_callback_query(call.id, "❌ Тянка не найдена!")
            return

        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        tyanka_data = TYANKA_DATA[tyanka_name]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        # Проверяем, есть ли уже тянка
        if user_data.get("tyanka"):
            bot.edit_message_text(
                f"{mention}, у тебя уже есть тянка",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            return

        # Проверяем баланс
        if user_data["balance"] < tyanka_data["price"]:
            bot.edit_message_text(
                f"{mention}, недостаточно средств",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            return

        # Покупка тянки
        user_data["balance"] -= tyanka_data["price"]
        # Убираем mood, добавляем total_earned
        user_data["tyanka"] = {
            "name": tyanka_name,
            "satiety": 100,
            "profit_accumulated": 0,
            "total_earned": 0,  # Новый счетчик общего заработка
            "last_update": datetime.now().isoformat()
        }
        save_casino_data()

        # Красивый ответ
        bot.edit_message_text(
            f"💖 {mention}, ты купил тянку «<b>{tyanka_name.capitalize()}</b>» за <b>{format_number(tyanka_data['price'])} izzzy</b>\n\n"
            f"🎉 Поздравляем с покупкой! Теперь твоя тянка будет приносить тебе доход!",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        bot.answer_callback_query(call.id, "✅ Тянка куплена!")

    except Exception as e:
        logger.error(f"Ошибка покупки тянки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при покупке!")

# ================== ПОКУПКА ТЯНКИ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить тянку"))
def buy_tyanka_text(message):
    try:
        user_id = message.from_user.id
        parts = message.text.lower().split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Используйте: купить тянку [имя]")
            return

        tyanka_name = " ".join(parts[2:])
        handle_tyanka_buy(message.chat.id, user_id, tyanka_name, message.from_user.first_name, None)

    except Exception as e:
        logger.error(f"Ошибка покупки тянки: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при покупке тянки!")

# Вспомогательная функция для покупки
def handle_tyanka_buy(chat_id, user_id, tyanka_name, buyer_name, call=None):
    user_data = get_user_data(user_id)

    if user_data.get("tyanka"):
        msg = "❌ У вас уже есть тянка! Сначала продайте текущую."
    elif tyanka_name not in TYANKA_DATA:
        msg = "❌ Такой тянки нет в магазине!"
    else:
        tyanka_info = TYANKA_DATA[tyanka_name]
        if user_data["balance"] < tyanka_info["price"]:
            msg = f"❌ Недостаточно средств! Нужно {format_number(tyanka_info['price'])} izzzy"
        else:
            user_data["balance"] -= tyanka_info["price"]
            # Убираем mood, добавляем total_earned
            user_data["tyanka"] = {
                "name": tyanka_name,
                "satiety": 100,
                "profit_accumulated": 0,
                "total_earned": 0,
                "last_update": datetime.now().isoformat()
            }
            save_casino_data()

            msg = (f"🎉 <b>Поздравляем с покупкой!</b>\n\n"
                  f"👤 Покупатель: <b>{buyer_name}</b>\n"
                  f"💝 Тянка: <b>{tyanka_name.capitalize()}</b>\n"
                  f"💰 Стоимость: <code>{format_number(tyanka_info['price'])} izzzy</code>\n"
                  f"⭐ Редкость: {tyanka_info['rarity']}\n\n"
                  f"💖 Теперь ухаживай за своей тянкой!")

    if call:
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, msg, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, parse_mode="HTML")

# ================== МОЯ ТЯНКА ==================
# Константа для лимита заработка (во сколько раз можно заработать больше цены тянки)
MAX_EARN_MULTIPLIER = 1.5

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["моя тянка", "моя тяшка"])
def my_tyanka(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    if not user_data.get("tyanka"):
        bot.send_message(message.chat.id, "❌ У вас нет тянки! Купите в магазине тянок.")
        return

    update_tyanka_stats(user_data)
    tyanka = user_data["tyanka"]
    info = TYANKA_DATA[tyanka["name"]]
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

    # Расчет лимита заработка
    max_earn = int(info["price"] * MAX_EARN_MULTIPLIER)
    current_total_earned = tyanka.get("total_earned", 0)
    earn_limit_reached = current_total_earned >= max_earn
    
    # Текущая накопленная сумма (доступная для снятия)
    accumulated_profit = tyanka.get("profit_accumulated", 0)

    text = (
        f"👩🏼 {mention}, информация о вашей тянке \"<b>{tyanka['name'].capitalize()}</b>\":\n\n"
        f"🍪 Сытость: {tyanka['satiety']} ед.\n"
        f"🍉 Накоплено: {format_number(accumulated_profit)} izzzy\n"
        f"💸 Прибыль в час: {format_number(info['profit_per_hour'])} \n"
        f"🌟 Редкость: {info['rarity']}\n"
        f"🧮 Вся прибыль: {format_number(current_total_earned)}/{format_number(max_earn)} \n\n"
        f"🛠 <a href='https://t.me/meow_newsbot'>Канал разработчика</a>"
    )

    if earn_limit_reached:
        text += f"\n⛔ <b>Достигнут лимит заработка! Продайте тянку.</b>\n"
    elif tyanka["satiety"] <= 30:
        text += f"\n⚠️ <i>Тянка голодна! Покорми её!</i>\n"

    kb = InlineKeyboardMarkup(row_width=2)
    # Оставляем только нужные кнопки
    collect_button = InlineKeyboardButton("💴 Собрать доход", callback_data=f"tyanka_collect_{user_id}")
    feed_button = InlineKeyboardButton("🥞 Покормить", callback_data=f"tyanka_feed_{user_id}")
    sell_button = InlineKeyboardButton("👸 Продать", callback_data=f"tyanka_sell_{user_id}")

    # Делаем кнопку сбора неактивной, если лимит достигнут или нет прибыли (просто для вида, но callback все равно сработает, но проверим в обработчике)
    # В telebot нет прямого способа сделать кнопку неактивной, поэтому просто добавим проверку в обработчике.
    kb.add(collect_button, feed_button)
    kb.add(sell_button)

    if info.get("image"):
        bot.send_photo(message.chat.id, info["image"], caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

# ================== ОБРАБОТЧИК КНОПКИ "ПРОДАТЬ" (НОВЫЙ) ==================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("tyanka_sell_") and "confirm" not in c.data and "cancel" not in c.data)
def callback_tyanka_sell_prompt(call):
    user_id = int(call.data.split("_")[-1])

    # ЗАЩИТА: проверяем владельца
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!", show_alert=True)
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У тебя нет тянки!", show_alert=True)
        return

    tyanka_name = user_data["tyanka"]["name"]
    tyanka_info = TYANKA_DATA[tyanka_name]
    refund = tyanka_info["price"] // 2
    mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

    # Текст подтверждения
    text = (
        f"{mention}, вы точно хотите продать свою тянку?\n\n"
        f"👋 Тянка: <b>{tyanka_name.capitalize()}</b>\n"
        f"💰 После продажи получите: <code>{format_number(refund)} izzzy</code>"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да", callback_data=f"tyanka_sell_confirm_{user_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"tyanka_sell_cancel_{user_id}")
    )

    # Редактируем сообщение (предполагаем, что это то же сообщение с тянкой)
    try:
        # Пытаемся отредактировать как фото
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        # Если не вышло, пробуем как текст
        try:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"Не удалось отредактировать сообщение для продажи: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка интерфейса!", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("tyanka_sell_confirm_"))
def callback_tyanka_sell_confirm(call):
    user_id = int(call.data.split("_")[-1])

    # ЗАЩИТА: проверяем владельца
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У тебя нет тянки!", show_alert=True)
        return

    tyanka_name = user_data["tyanka"]["name"]
    tyanka_info = TYANKA_DATA[tyanka_name]
    refund = tyanka_info["price"] // 2

    user_data["balance"] += refund
    user_data["tyanka"] = None
    save_casino_data()

    mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

    # Успешная продажа
    success_text = f"✅ {mention}, тянка успешно продана!"
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=success_text,
            parse_mode="HTML"
        )
    except:
        try:
            bot.edit_message_text(
                success_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось отредактировать сообщение об успешной продаже: {e}")
            bot.send_message(call.message.chat.id, success_text, parse_mode="HTML")

    bot.answer_callback_query(call.id, f"✅ Продано за {format_number(refund)} izzzy")


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("tyanka_sell_cancel_"))
def callback_tyanka_sell_cancel(call):
    user_id = int(call.data.split("_")[-1])

    # ЗАЩИТА: проверяем владельца
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return

    # Просто возвращаем пользователя в меню его тянки
    # Для этого создаем фейковый объект сообщения и вызываем функцию my_tyanka
    class FakeMessage:
        def __init__(self, chat, from_user):
            self.chat = chat
            self.from_user = from_user
            self.chat_id = chat.id

    fake_msg = FakeMessage(call.message.chat, call.from_user)
    my_tyanka(fake_msg)
    bot.answer_callback_query(call.id, "❌ Продажа отменена")


# ================== КОРМЛЕНИЕ ТЯНКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_feed_"))
def callback_tyanka_feed(call):
    user_id = int(call.data.split("_")[-1])

    # ЗАЩИТА: проверяем владельца
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!", show_alert=True)
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У вас нет тянки!", show_alert=True)
        return

    tyanka = user_data["tyanka"]
    tyanka_name = tyanka["name"]
    feed_cost = TYANKA_DATA[tyanka_name]["feed_cost"]

    if user_data["balance"] < feed_cost:
        bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {format_number(feed_cost)} izzzy", show_alert=True)
        return

    # Списываем деньги и восстанавливаем сытость
    user_data["balance"] -= feed_cost
    tyanka["satiety"] = 100
    save_casino_data()

    # Обновляем сообщение с тянкой
    info = TYANKA_DATA[tyanka_name]
    user_mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
    
    # Расчет лимита заработка
    max_earn = int(info["price"] * MAX_EARN_MULTIPLIER)
    current_total_earned = tyanka.get("total_earned", 0)
    accumulated_profit = tyanka.get("profit_accumulated", 0)

    text = (
        f"👩🏼 {user_mention}, информация о вашей тянке \"<b>{tyanka_name.capitalize()}</b>\":\n\n"
        f"🍪 Сытость: {tyanka['satiety']} ед.\n"
        f"🍉 Накоплено: {format_number(accumulated_profit)} izzzy\n"
        f"💸 Прибыль в час: {format_number(info['profit_per_hour'])}\n"
        f"🌟 Редкость: {info['rarity']}\n"
        f"🧮 Вся прибыль: {format_number(current_total_earned)}/{format_number(max_earn)}\n\n"
        f"🛠 <a href='https://t.me/meow_newsbot'>Канал разработчика</a>"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💴 Собрать доход", callback_data=f"tyanka_collect_{user_id}"),
        InlineKeyboardButton("🥞 Покормить", callback_data=f"tyanka_feed_{user_id}")
    )
    kb.add(InlineKeyboardButton("👸 Продать", callback_data=f"tyanka_sell_{user_id}"))

    try:
        # Пробуем отредактировать подпись к фото
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        # Если не получилось, редактируем как обычный текст
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )

    bot.answer_callback_query(call.id, f"Тянка накормлена - а ты опять без ужина")

# ================== СБОР ДОХОДА ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_collect_"))
def callback_tyanka_collect(call):
    user_id = int(call.data.split("_")[-1])

    # ЗАЩИТА: проверяем владельца
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!", show_alert=True)
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У вас нет тянки!", show_alert=True)
        return

    update_tyanka_stats(user_data)
    tyanka = user_data["tyanka"]
    info = TYANKA_DATA[tyanka["name"]]

    # Проверка лимита заработка
    max_earn = int(info["price"] * MAX_EARN_MULTIPLIER)
    current_total_earned = tyanka.get("total_earned", 0)

    if current_total_earned >= max_earn:
        bot.answer_callback_query(call.id, "⛔ Тянка больше не приносит доход! Продайте её.", show_alert=True)
        return

    profit = tyanka.get("profit_accumulated", 0)

    if profit <= 0:
        bot.answer_callback_query(call.id, "❌ Нет накопленной прибыли!", show_alert=True)
        return

    # Начисляем прибыль и обновляем total_earned
    user_data["balance"] += profit
    tyanka["profit_accumulated"] = 0

    # Важно: обновляем total_earned, но не даем ему превысить лимит
    new_total = current_total_earned + profit
    tyanka["total_earned"] = min(new_total, max_earn)

    save_casino_data()

    # Обновляем сообщение с тянкой
    user_mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
    accumulated_profit = tyanka.get("profit_accumulated", 0)  # теперь 0

    text = (
        f"👩🏼 {user_mention}, информация о вашей тянке \"<b>{tyanka['name'].capitalize()}</b>\":\n\n"
        f"🍪 Сытость: {tyanka['satiety']} ед.\n"
        f"🍉 Накоплено: {format_number(accumulated_profit)} izzzy\n"
        f"💸 Прибыль в час: {format_number(info['profit_per_hour'])}\n"
        f"🌟 Редкость: {info['rarity']}\n"
        f"🧮 Вся прибыль: {format_number(tyanka['total_earned'])}/{format_number(max_earn)}\n\n"
        f"🛠 <a href='https://t.me/meow_newsbot'>Канал разработчика</a>"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💴 Собрать доход", callback_data=f"tyanka_collect_{user_id}"),
        InlineKeyboardButton("🥞 Покормить", callback_data=f"tyanka_feed_{user_id}")
    )
    kb.add(InlineKeyboardButton("👸 Продать", callback_data=f"tyanka_sell_{user_id}"))

    try:
        # Пробуем отредактировать подпись к фото
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        # Если не получилось, редактируем как обычный текст
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )

    bot.answer_callback_query(call.id, f"✅ +{format_number(profit)}$ на баланс!")


# ================== КНОПКА НАЗАД (обновлена с новым текстом) ==================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("back_tyanka_"))
def callback_back_tyanka(call):
    user_id = int(call.data.split("_")[-1])

    # ЗАЩИТА: проверяем владельца
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!", show_alert=True)
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="❌ У тебя нет тянки!",
            parse_mode="HTML"
        )
        return

    update_tyanka_stats(user_data)

    # Проверяем, не ушла ли тянка
    if check_tyanka_leave(user_id, user_data):
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="❌ Твоя тянка ушла!",
            parse_mode="HTML"
        )
        return

    tyanka = user_data["tyanka"]
    info = TYANKA_DATA[tyanka["name"]]

    # Кликабельная ссылка на пользователя
    user_mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

    # Расчет лимита заработка
    max_earn = int(info["price"] * MAX_EARN_MULTIPLIER)
    current_total_earned = tyanka.get("total_earned", 0)
    earn_limit_reached = current_total_earned >= max_earn
    accumulated_profit = tyanka.get("profit_accumulated", 0)

    # НОВЫЙ ТЕКСТ с "Накоплено"
    text = (
        f"👩🏼 {user_mention}, информация о вашей тянке \"{tyanka['name'].capitalize()}\":\n\n"
        f"🍪 Сытость: {tyanka['satiety']} ед.\n"
        f"🍉 Накоплено: {format_number(accumulated_profit)} izzzy\n"
        f"💸 Прибыль в час: {format_number(info['profit_per_hour'])}\n"
        f"🌟 Редкость: {info['rarity']}\n"
        f"🧮 Вся прибыль: {format_number(current_total_earned)}/{format_number(max_earn)}\n\n"
        f"🛠 <a href='https://t.me/meow_newsbot'>Канал разработчика</a>"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💴 Собрать доход", callback_data=f"tyanka_collect_{user_id}"),
        InlineKeyboardButton("🥞 Покормить", callback_data=f"tyanka_feed_{user_id}")
    )
    kb.add(InlineKeyboardButton("👸 Продать", callback_data=f"tyanka_sell_{user_id}"))

    try:
        # Пробуем отредактировать подпись к фото
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        # Если не получилось, редактируем как обычный текст
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
    
    bot.answer_callback_query(call.id)
    
    
# ================== КОМАНДЫ БИЗНЕСА (ИСПРАВЛЕННАЯ ВЕРСИЯ) ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["магазин бизнеса", "магазин бизнесов"])
def business_shop(message):
    text = "🏢 <b>МАГАЗИН БИЗНЕСОВ</b> 🏢\n\n"
    text += "💼 <i>Покубай бизнесы — получай пассивный доход!</i>\n\n"
    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, (name, data) in enumerate(BUSINESS_DATA.items(), 1):
        text += (
            f"🏪 <b>{name.upper()}</b>\n"
            f"├ 💰 Стоимость: <code>{format_number(data['price'])} izzzy</code>\n"
            f"├ 💵 Доход/час: <code>{format_number(data['profit_per_hour'])} izzzy</code>\n"
            f"├ 📦 Материалы: {data['material_units']}ед. за {format_number(data['material_cost'])} izzzy\n"
            f"└ 🎯 Рентабельность: <b>{(data['profit_per_hour'] / data['price'] * 100):.1f}%</b>\n\n"
        )
    
    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    text += "🛒 <b>Команда для покупки:</b>\n<code>купить бизнес [название]</code>\n\n"
    text += "💡 <i>Пример:</i> <code>купить бизнес магазин оружия</code>"

    bot.send_message(message.chat.id, text, parse_mode="HTML")
    logger.info(f"Пользователь {message.from_user.username} запросил магазин бизнесов")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить бизнес"))
def buy_business(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        if user_data.get("business"):
            bot.send_message(message.chat.id, 
                           f"❌ {mention}, у тебя уже есть бизнес!\n\n"
                           f"💼 Сначала продай текущий бизнес:", parse_mode="HTML")
            return
            
        business_name = " ".join(message.text.lower().split()[2:])
        
        if not business_name or business_name not in BUSINESS_DATA:
            bot.send_message(message.chat.id,
                           f"❌ {mention}, такого бизнеса не существует!\n\n"
                           f"📋 Доступные бизнесы:\n"
                           f"{', '.join([f'<code>{name}</code>' for name in BUSINESS_DATA.keys()])}", 
                           parse_mode="HTML")
            return
            
        business_info = BUSINESS_DATA[business_name]
        
        if user_data["balance"] < business_info["price"]:
            bot.send_message(message.chat.id,
                           f"💸 {mention}, недостаточно средств!\n\n"
                           f"💼 Бизнес: <b>{business_name.upper()}</b>\n"
                           f"💰 Нужно: <code>{format_number(business_info['price'])} izzzy</code>\n"
                           f"💳 На балансе: <code>{format_number(user_data['balance'])} izzzy</code>",
                           parse_mode="HTML")
            return
            
        # Покупка бизнеса
        user_data["balance"] -= business_info["price"]
        user_data["business"] = {
            "name": business_name,
            "profit_per_hour": business_info["profit_per_hour"],
            "materials": 100,  # Начинаем с полными материалами
            "last_update": datetime.now().isoformat(),
            "profit_accumulated": 0
        }
        save_casino_data()
        
        # Красивое сообщение об успешной покупке
        success_text = (
            f"🎉 <b>ПОЗДРАВЛЯЕМ С ПОКУПКОЙ!</b> 🎉\n\n"
            f"👤 {mention}\n"
            f"💼 Бизнес: <b>{business_name.upper()}</b>\n"
            f"💰 Стоимость: <code>{format_number(business_info['price'])} izzzy</code>\n"
            f"💵 Доход/час: <code>{format_number(business_info['profit_per_hour'])} izzzy</code>\n"
            f"📦 Материалы: <b>100/100</b> 🧸\n\n"
            f"💫 <i>Бизнес начал приносить доход!</i>"
        )
        
        # Пытаемся отправить с фото
        try:
            if business_info.get('image'):
                bot.send_photo(message.chat.id, business_info['image'], 
                             caption=success_text, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, success_text, parse_mode="HTML")
        except:
            bot.send_message(message.chat.id, success_text, parse_mode="HTML")
            
        logger.info(f"Пользователь {message.from_user.username} купил бизнес {business_name}")
        
    except Exception as e:
        logger.error(f"Ошибка покупки бизнеса: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при покупке бизнеса!")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("продать бизнес"))
def sell_business(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        if not user_data.get("business"):
            bot.send_message(message.chat.id, f"❌ {mention}, у тебя нет бизнеса для продажи!", parse_mode="HTML")
            return
            
        business = user_data["business"]
        business_name = business["name"]
        business_info = BUSINESS_DATA[business_name]
        
        # Используем цену из BUSINESS_DATA для продажи (50%)
        sell_price = business_info["price"] // 2
        
        user_data["balance"] += sell_price
        user_data["business"] = None
        save_casino_data()
        
        bot.send_message(message.chat.id,
                       f"💸 <b>Бизнес продан</b> 💸\n\n"
                       f"👤 {mention}\n"
                       f"💼 Бизнес: <b>{business_name.upper()}</b>\n"
                       f"💰 Получено: <code>{format_number(sell_price)} izzzy</code>\n\n"
                       f"💵 Новый баланс: <code>{format_number(user_data['balance'])} izzzy</code>",
                       parse_mode="HTML")
        
        logger.info(f"Пользователь {message.from_user.username} продал бизнес {business_name}")
        
    except Exception as e:
        logger.error(f"Ошибка продажи бизнеса: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при продаже бизнеса!")

def update_business_stats(user_data):
    """Обновляет статистику бизнеса и проверяет материалы"""
    if not user_data.get("business"):
        return
        
    business = user_data["business"]
    now = datetime.now()
    last_update = datetime.fromisoformat(business["last_update"])
    hours_passed = (now - last_update).total_seconds() / 3600
    
    if hours_passed > 0:
        # Начисляем прибыль только если есть материалы
        if business["materials"] > 0:
            # 🔥 ИСПРАВЛЕНИЕ: округляем прибыль до целых чисел
            profit_earned = business["profit_per_hour"] * hours_passed
            business["profit_accumulated"] += int(profit_earned)  # ⬅️ ДОБАВЛЕНО int()
            
            # Расходуем материалы (1 единица в час)
            materials_used = min(int(hours_passed), business["materials"])
            business["materials"] -= materials_used
            
            # Автоматически удаляем бизнес если материалы закончились
            if business["materials"] <= 0:
                user_data["business"] = None
                logger.info(f"Бизнес автоматически удален - закончились материалы")
        
        business["last_update"] = now.isoformat()
        save_casino_data()

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой бизнес", "бизнес"])
def my_business(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    if not user_data.get("business"):
        bot.send_message(message.chat.id, 
                       f"💼 {mention}, у тебя нет бизнеса!\n\n"
                       f"🛒 Посмотреть доступные бизнесы:\n<code>магазин бизнесов</code>", 
                       parse_mode="HTML")
        return
        
    update_business_stats(user_data)
    
    # Проверяем, не удалился ли бизнес после обновления (если материалы закончились)
    if not user_data.get("business"):
        bot.send_message(message.chat.id, 
                       f"💼 {mention}, твой бизнес закрылся из-за нехватки материалов!", 
                       parse_mode="HTML")
        return
        
    business = user_data["business"]
    business_info = BUSINESS_DATA[business["name"]]
    
    # Красивый текст с информацией о бизнесе
    business_text = (
        f"🏢 <b>Твой бизнес</b> 🏢\n\n"
        f"👤 Владелец: {mention}\n"
        f"💼 Название: <b>{business['name'].upper()}</b>\n\n"
        f"📊 <b>СТАТИСТИКА:</b>\n"
        f"├ 💵 Доход/час: <code>{format_number(business['profit_per_hour'])} izzzy</code>\n"
        f"├ 💰 Накоплено: <code>{format_number(int(business['profit_accumulated']))} izzzy</code>\n"  # ⬅️ ДОБАВЛЕНО int()
        f"├ 📦 Материалы: <b>{business['materials']}/100</b> 🧸\n"
        f"└ 🛒 Стоимость материалов: <code>{format_number(business_info['material_cost'])} izzzy</code>\n\n"
        f"💡 <i>Материалы тратятся со временем. Следи за их количеством!</i>"
    )
    
    # Создаем красивую клавиатуру
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("💰 Собрать доход", callback_data=f"business_collect_{user_id}"),
        InlineKeyboardButton("🛒 Купить материалы", callback_data=f"business_buy_{user_id}")
    )
    markup.row(InlineKeyboardButton("💸 Продать бизнес", callback_data=f"business_sell_{user_id}"))
    
    # Отправляем с фото бизнеса
    try:
        if business_info.get('image'):
            bot.send_photo(message.chat.id, business_info['image'], 
                         caption=business_text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, business_text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить фото бизнеса: {e}")
        bot.send_message(message.chat.id, business_text, reply_markup=markup, parse_mode="HTML")
    
    logger.info(f"Пользователь {message.from_user.username} запросил информацию о бизнесе")

# ================== ИНЛАЙН КНОПКИ ДЛЯ БИЗНЕСА ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("business_collect_"))
def collect_business_profit_callback(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        # Проверяем владельца
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твой бизнес!", show_alert=True)
            return
            
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        if not user_data.get("business"):
            bot.answer_callback_query(call.id, "❌ У тебя нет бизнеса!", show_alert=True)
            return
            
        update_business_stats(user_data)
        business = user_data["business"]
        
        profit = business["profit_accumulated"]
        if profit <= 0:
            bot.answer_callback_query(call.id, "❌ Нет накопленной прибыли!", show_alert=True)
            return
            
        # Собираем прибыль
        actual_profit = add_income(user_id, profit, "business")
        business["profit_accumulated"] = 0
        save_casino_data()
        
        if actual_profit > 0:
            # Обновляем сообщение
            business_info = BUSINESS_DATA[business["name"]]
            business_text = (
                f"🏢 <b>Твой бизнес</b> 🏢\n\n"
                f"👤 Владелец: {mention}\n"
                f"💼 Название: <b>{business['name'].upper()}</b>\n\n"
                f"📊 <b>СТАТИСТИКА:</b>\n"
                f"├ 💵 Доход/час: <code>{format_number(business['profit_per_hour'])} izzzy</code>\n"
                f"├ 💰 Накоплено: <code>0 izzzy</code> ✅\n"
                f"├ 📦 Материалы: <b>{business['materials']}/100</b> 🧸\n"
                f"└ 🛒 Стоимость материалов: <code>{format_number(business_info['material_cost'])} izzzy</code>\n\n"
                f"💸 <b>{mention}, вы собрали доход с вашего бизнеса.</b>"
            )
            
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("💰 Собрать доход", callback_data=f"business_collect_{user_id}"),
                InlineKeyboardButton("🛒 Купить материалы", callback_data=f"business_buy_{user_id}")
            )
            markup.row(InlineKeyboardButton("💸 Продать бизнес", callback_data=f"business_sell_{user_id}"))
            
            try:
                if business_info.get('image'):
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=business_text,
                        reply_markup=markup,
                        parse_mode="HTML"
                    )
                else:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=business_text,
                        reply_markup=markup,
                        parse_mode="HTML"
                    )
            except:
                pass
                
            bot.answer_callback_query(call.id, f"✅ +{format_number(int(actual_profit))} izzzy")  # ⬅️ ДОБАВЛЕНО int()
        else:
            bot.answer_callback_query(call.id, "❌ Достигнут дневный лимит дохода!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка сбора прибыли: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("business_buy_"))
def buy_materials_callback(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        # Проверяем владельца
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твой бизнес!", show_alert=True)
            return
            
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        if not user_data.get("business"):
            bot.answer_callback_query(call.id, "❌ У тебя нет бизнеса!", show_alert=True)
            return
            
        business = user_data["business"]
        business_info = BUSINESS_DATA[business["name"]]
        price = business_info["material_cost"]
        materials_to_add = business_info["material_units"]
        
        # Проверяем максимальное количество материалов
        if business["materials"] >= 100:
            bot.answer_callback_query(call.id, "❌ У тебя максимальное количество материалов!", show_alert=True)
            return
            
        # Вычисляем сколько можно докупить
        can_buy = 100 - business["materials"]
        if materials_to_add > can_buy:
            materials_to_add = can_buy
            # Пересчитываем стоимость за неполный пакет
            price = int(price * (materials_to_add / business_info["material_units"]))
        
        if user_data["balance"] < price:
            bot.answer_callback_query(call.id, 
                                   f"❌ Недостаточно средств! Нужно {format_number(price)} izzzy", 
                                   show_alert=True)
            return
            
        # Покупаем материалы
        user_data["balance"] -= price
        business["materials"] += materials_to_add
        save_casino_data()
        
        # Обновляем сообщение
        business_text = (
            f"🏢 <b>Твой бизнес</b> 🏢\n\n"
            f"👤 Владелец: {mention}\n"
            f"💼 Название: <b>{business['name'].upper()}</b>\n\n"
            f"📊 <b>СТАТИСТИКА:</b>\n"
            f"├ 💵 Доход/час: <code>{format_number(business['profit_per_hour'])} izzzy</code>\n"
            f"├ 💰 Накоплено: <code>{format_number(int(business['profit_accumulated']))} izzzy</code>\n"  # ⬅️ ДОБАВЛЕНО int()
            f"├ 📦 Материалы: <b>{business['materials']}/100</b> 🧸 ✅\n"
            f"└ 🛒 Стоимость материалов: <code>{format_number(business_info['material_cost'])} izzzy</code>\n\n"
            f"🛒 <b>{mention}, вы купили материалы для своего бизнеса. Максимум можно иметь 100 материалов🧸</b>"
        )
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("💰 Собрать доход", callback_data=f"business_collect_{user_id}"),
            InlineKeyboardButton("🛒 Купить материалы", callback_data=f"business_buy_{user_id}")
        )
        markup.row(InlineKeyboardButton("💸 Продать бизнес", callback_data=f"business_sell_{user_id}"))
        
        try:
            if business_info.get('image'):
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=business_text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=business_text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
        except:
            pass
            
        bot.answer_callback_query(call.id, f"✅ +{materials_to_add} материалов")
        
    except Exception as e:
        logger.error(f"Ошибка покупки материалов: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("business_sell_"))
def sell_business_callback(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        # Проверяем владельца
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твой бизнес!", show_alert=True)
            return
            
        user_data = get_user_data(user_id)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        if not user_data.get("business"):
            bot.answer_callback_query(call.id, "❌ У тебя нет бизнеса!", show_alert=True)
            return
            
        business = user_data["business"]
        business_info = BUSINESS_DATA[business["name"]]
        
        # Используем цену из BUSINESS_DATA для продажи (50%)
        sell_price = business_info["price"] // 2
        
        # Продажа бизнеса
        user_data["balance"] += sell_price
        user_data["business"] = None
        save_casino_data()
        
        # Удаляем сообщение с бизнесом
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
            
        bot.send_message(call.message.chat.id,
                       f"💸 <b>БИЗНЕС ПРОДАН</b> 💸\n\n"
                       f"👤 {mention}\n"
                       f"💼 Бизнес: <b>{business['name'].upper()}</b>\n"
                       f"💰 Получено: <code>{format_number(sell_price)} izzzy</code>\n\n"
                       f"💵 Новый баланс: <code>{format_number(user_data['balance'])} izzzy</code>",
                       parse_mode="HTML")
        
        bot.answer_callback_query(call.id, "✅ Бизнес продан!")
        
    except Exception as e:
        logger.error(f"Ошибка продажи бизнеса: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КОМАНДЫ ДОМОВ ==================
def check_button_owner(call, user_id):
    """Универсальная проверка владельца кнопки"""
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "🚫 Это не твоя кнопка!", show_alert=True)
        return False
    return True

def get_user_mention(user):
    """Создает кликабельное упоминание пользователя"""
    username = user.username or user.first_name
    if user.username:
        return f"@{user.username}"
    else:
        return f'<a href="tg://user?id={user.id}">{username}</a>'

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["магазин домов", "дома"])
def house_shop(message):
    user_mention = get_user_mention(message.from_user)
    
    shop_text = f"🏠 <b>Магазин домов</b> | {user_mention}\n\n"
    
    for name, data in HOUSE_DATA.items():
        shop_text += (f"🏡 <b>«{name.capitalize()}»</b>\n"
                     f"├ 💰 Цена: {format_number(data['price'])} izzzy\n"
                     f"├ 📈 Прибыль/час: {format_number(data['profit_per_hour'])} izzzy\n"
                     f"└ 🏠 Содержание: {format_number(data['upkeep_cost'])} izzzy/день\n\n")
    
    shop_text += ("📝 <b>Как купить:</b>\n"
                 "<code>купить дом [название]</code>\n"
                 "Пример: <code>купить дом Вилла</code>\n\n"
                 "⚠️ <i>Можно владеть только одним домом</i>")
    
    bot.send_message(message.chat.id, shop_text, parse_mode="HTML")
    logger.info(f"Пользователь {message.from_user.username} запросил магазин домов")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить дом"))
def buy_house(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        user_mention = get_user_mention(message.from_user)
        
        # Проверяем, есть ли уже дом
        if user_data.get("house"):
            bot.send_message(message.chat.id, 
                           f"❌ {user_mention}, у вас уже есть дом! Сначала продайте текущий.",
                           parse_mode="HTML")
            return
            
        # Извлекаем название дома
        house_name = message.text.lower().replace("купить дом", "").strip()
        
        if not house_name:
            bot.send_message(message.chat.id, 
                           f"❌ {user_mention}, укажите название дома!\n\n"
                           f"Пример: <code>купить дом Вилла</code>\n"
                           f"Доступные дома: {', '.join(HOUSE_DATA.keys())}",
                           parse_mode="HTML")
            return
        
        # Ищем дом по подстроке (частичное совпадение)
        found_house = None
        for name in HOUSE_DATA.keys():
            if house_name in name.lower():
                found_house = name
                break
        
        if not found_house:
            # Покажем доступные дома
            available_houses = "\n".join([f"• {name}" for name in HOUSE_DATA.keys()])
            bot.send_message(message.chat.id, 
                           f"❌ {user_mention}, дом '{house_name}' не найден!\n\n"
                           f"🏠 <b>Доступные дома:</b>\n{available_houses}",
                           parse_mode="HTML")
            return
            
        house_info = HOUSE_DATA[found_house]
        
        # Проверяем баланс
        if user_data["balance"] < house_info["price"]:
            bot.send_message(message.chat.id,
                           f"❌ {user_mention}, недостаточно средств!\n\n"
                           f"💰 Нужно: {format_number(house_info['price'])} izzzy\n"
                           f"💳 У вас: {format_number(user_data['balance'])} izzzy\n"
                           f"📊 Не хватает: {format_number(house_info['price'] - user_data['balance'])} izzzy",
                           parse_mode="HTML")
            return
            
        # Покупаем дом
        user_data["balance"] -= house_info["price"]
        user_data["house"] = {
            "name": found_house,
            "last_update": datetime.now().isoformat(),
            "profit_accumulated": 0
        }
        save_casino_data()
        
        bot.send_message(message.chat.id,
                        f"✅ {user_mention}, вы купили дом <b>«{found_house}»</b>!\n\n"
                        f"💰 Стоимость: {format_number(house_info['price'])} izzzy\n"
                        f"📈 Прибыль/час: {format_number(house_info['profit_per_hour'])} izzzy\n"
                        f"🏠 Содержание: {format_number(house_info['upkeep_cost'])} izzzy/день\n\n"
                        f"💫 Поздравляем с новой недвижимостью! 🏡",
                        parse_mode="HTML")
        logger.info(f"Пользователь {message.from_user.username} купил дом {found_house}")
        
    except Exception as e:
        logger.error(f"Ошибка покупки дома: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при покупке дома!")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("продать дом"))
def sell_house(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        user_mention = get_user_mention(message.from_user)
        
        if not user_data.get("house"):
            bot.send_message(message.chat.id,
                           f"❌ {user_mention}, у вас нет дома для продажи!\n\n"
                           f"🏠 Посмотреть дома: <code>магазин домов</code>",
                           parse_mode="HTML")
            return
            
        house_name = message.text.lower().replace("продать дом", "").strip()
        current_house = user_data["house"]["name"]
        
        if house_name and house_name != current_house.lower():
            bot.send_message(message.chat.id,
                           f"❌ {user_mention}, у вас нет дома '{house_name}'!\n\n"
                           f"🏠 Ваш текущий дом: <b>«{current_house}»</b>",
                           parse_mode="HTML")
            return
            
        house_info = HOUSE_DATA[current_house]
        sell_price = house_info["price"] // 2  # 50% от стоимости
        
        # Продаем дом
        user_data["balance"] += sell_price
        user_data["house"] = None
        save_casino_data()
        
        bot.send_message(message.chat.id,
                        f"✅ {user_mention}, вы продали дом <b>«{current_house}»</b>!\n\n"
                        f"💰 Получено: {format_number(sell_price)} izzzy\n"
                        f"💳 Новый баланс: {format_number(user_data['balance'])} izzzy\n\n"
                        f"🏡 Можете купить новый дом в магазине!",
                        parse_mode="HTML")
        logger.info(f"Пользователь {message.from_user.username} продал дом {current_house}")
        
    except Exception as e:
        logger.error(f"Ошибка продажи дома: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при продаже дома!")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой дом", "дом"])
def my_house(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        user_mention = get_user_mention(message.from_user)

        if not user_data.get("house"):
            bot.send_message(
                message.chat.id,
                f"🏠 {user_mention}, у вас нет дома!\n\n"
                f"🛒 <b>Магазин домов:</b> <code>магазин домов</code>\n"
                f"💳 <b>Купить дом:</b> <code>купить дом [название]</code>",
                parse_mode="HTML"
            )
            return

        update_house_stats(user_data)
        house = user_data["house"]
        house_info = HOUSE_DATA[house["name"]]

        # Рассчитываем время с последнего обновления
        last_update = datetime.fromisoformat(house["last_update"])
        hours_passed = (datetime.now() - last_update).total_seconds() / 3600

        # Деньги всегда целые
        accumulated = int(house["profit_accumulated"])
        house["profit_accumulated"] = accumulated

        house_text = (
            f"🏡 <b>Твой дом</b> | {user_mention}\n\n"
            f"✨ <b>«{house['name'].capitalize()}»</b>\n\n"
            f"💰 <b>Финансы:</b>\n"
            f"├ 💵 Прибыль/час: <code>{format_number(house_info['profit_per_hour'])} izzzy</code>\n"
            f"├ 💎 Накоплено: <code>{format_number(accumulated)} izzzy</code>\n"
            f"├ ⏱ Прошло часов: <code>{hours_passed:.1f}</code>\n"
            f"└ 🛠 Содержание: <code>{format_number(house_info['upkeep_cost'])} izzzy</code>/день\n\n"
            f"💫 <i>Доход накапливается автоматически</i>"
        )

        # Клавиатура с эмодзи
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("💰 Собрать аренду", callback_data=f"house_collect_{user_id}"),
            InlineKeyboardButton("🔧 Оплатить", callback_data=f"house_upkeep_{user_id}")
        )
        markup.row(
            InlineKeyboardButton("🛒 В магазин", callback_data=f"house_shop_{user_id}")
        )

        # Отправляем сообщение
        try:
            if house_info.get("image"):
                bot.send_photo(
                    message.chat.id,
                    house_info["image"],
                    caption=house_text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            else:
                bot.send_message(
                    message.chat.id,
                    house_text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Не удалось отправить дом: {e}")
            bot.send_message(
                message.chat.id,
                house_text,
                reply_markup=markup,
                parse_mode="HTML"
            )

        logger.info(
            f"Пользователь {message.from_user.username} запросил информацию о доме"
        )

    except Exception as e:
        logger.error(f"Ошибка отображения дома: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при загрузке информации о доме!"
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith("house_collect_"))
def house_collect_callback(call):
    """Обработка сбора аренды"""
    try:
        user_id = int(call.data.split("_")[2])

        # Проверяем владельца кнопки
        if not check_button_owner(call, user_id):
            return

        user_data = get_user_data(user_id)
        user_mention = get_user_mention(call.from_user)

        if not user_data.get("house"):
            bot.answer_callback_query(call.id, "❌ У вас нет дома!", show_alert=True)
            return

        update_house_stats(user_data)
        house = user_data["house"]

        accumulated = int(house["profit_accumulated"])
        house["profit_accumulated"] = accumulated

        if accumulated <= 0:
            bot.answer_callback_query(call.id, "❌ Нет накопленной аренды!", show_alert=True)
            return

        # Начисляем аренду
        user_data["balance"] = int(user_data["balance"] + accumulated)
        user_data["house"]["profit_accumulated"] = 0
        user_data["house"]["last_update"] = datetime.now().isoformat()
        save_casino_data()

        # Обновляем сообщение
        house_info = HOUSE_DATA[house["name"]]
        new_text = (
            f"🏡 <b>Твой дом</b> | {user_mention}\n\n"
            f"✨ <b>«{house['name'].capitalize()}»</b>\n\n"
            f"✅ <b>Аренда собрана!</b>\n"
            f"├ 💰 Получено: <code>{format_number(accumulated)} izzzy</code>\n"
            f"└ 💳 Баланс: <code>{format_number(user_data['balance'])} izzzy</code>\n\n"
            f"📈 Прибыль/час: <code>{format_number(house_info['profit_per_hour'])} izzzy</code>"
        )

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("💰 Собрать аренду", callback_data=f"house_collect_{user_id}"),
            InlineKeyboardButton("🔧 Оплатить", callback_data=f"house_upkeep_{user_id}")
        )
        markup.row(
            InlineKeyboardButton("🛒 В магазин", callback_data=f"house_shop_{user_id}")
        )

        try:
            bot.edit_message_text(
                new_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=markup
            )
        except:
            bot.edit_message_caption(
                new_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=markup
            )

        bot.answer_callback_query(
            call.id,
            f"✅ Получено {format_number(accumulated)} izzzy"
        )
        logger.info(
            f"Пользователь {call.from_user.username} собрал аренду: {accumulated} izzzy"
        )

    except Exception as e:
        logger.error(f"Ошибка сбора аренды: {e}")
        bot.answer_callback_query(
            call.id,
            "❌ Ошибка при сборе аренды!",
            show_alert=True
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith("house_upkeep_"))
def house_upkeep_callback(call):
    """Обработка оплаты содержания"""
    try:
        user_id = int(call.data.split("_")[2])
        
        # Проверяем владельца кнопки
        if not check_button_owner(call, user_id):
            return
        
        user_data = get_user_data(user_id)
        user_mention = get_user_mention(call.from_user)
        
        if not user_data.get("house"):
            bot.answer_callback_query(call.id, "❌ У вас нет дома!", show_alert=True)
            return
        
        house = user_data["house"]
        house_info = HOUSE_DATA[house["name"]]
        upkeep_cost = house_info["upkeep_cost"]
        
        if user_data["balance"] < upkeep_cost:
            bot.answer_callback_query(call.id, 
                                    f"❌ Недостаточно средств! Нужно {format_number(upkeep_cost)} izzzy", 
                                    show_alert=True)
            return
        
        # Оплачиваем содержание
        user_data["balance"] -= upkeep_cost
        save_casino_data()
        
        bot.answer_callback_query(call.id, 
                                f"✅ Оплачено содержание: {format_number(upkeep_cost)}$", 
                                show_alert=True)
        logger.info(f"Пользователь {call.from_user.username} оплатил содержание дома: {upkeep_cost} izzzy")
        
    except Exception as e:
        logger.error(f"Ошибка оплаты содержания: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при оплате содержания!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("house_shop_"))
def house_shop_callback(call):
    """Возврат в магазин домов"""
    try:
        user_id = int(call.data.split("_")[2])
        
        # Проверяем владельца кнопки
        if not check_button_owner(call, user_id):
            return
        
        # Создаем фейковое сообщение для вызова магазина
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = from_user
        
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        house_shop(fake_msg)
        
        # Удаляем старое сообщение
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка возврата в магазин домов: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

def update_house_stats(user_data):
    """Обновляет статистику дома (накопленную аренду)"""
    try:
        if not user_data.get("house"):
            return
        
        house = user_data["house"]
        last_update = datetime.fromisoformat(house["last_update"])
        now = datetime.now()
        hours_passed = (now - last_update).total_seconds() / 3600
        
        if hours_passed >= 1:  # Если прошёл хотя бы час
            house_info = HOUSE_DATA[house["name"]]
            profit_per_hour = house_info["profit_per_hour"]
            
            # Накапливаем аренду
            accumulated_profit = profit_per_hour * hours_passed
            user_data["house"]["profit_accumulated"] += accumulated_profit
            user_data["house"]["last_update"] = now.isoformat()
            save_casino_data()
            
    except Exception as e:
        logger.error(f"Ошибка обновления статистики дома: {e}")

print("✅ Система домов улучшена и готова к работе! 🏠")

# ================== 🚗 БЛОК "МАШИНЫ" ==================

def stylize_text(text):
    fancy = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘶𝘷𝘄𝘅𝘆𝘇"
    )
    return text.translate(fancy)

# ================== 🏪 МАГАЗИН МАШИН С ПАГИНАЦИЕЙ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["магазин машин", "машины"])
def car_shop(message):
    user = message.from_user
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    
    # Разделяем машины на две страницы
    car_list = list(CAR_DATA.keys())
    half = len(car_list) // 2
    page1_cars = car_list[:half]
    page2_cars = car_list[half:]
    
    text = (
        f"🚗 <b>Магазин машин</b>\n"
        f"------------------------------------------\n"
        f"👤 Покупатель: {mention}\n\n"
        f"<i>Выбери машину своей мечты:</i>\n\n"
    )
    
    # Показываем первую страницу машин
    for name in page1_cars:
        data = CAR_DATA[name]
        text += (
            f"<b>{name}</b>\n"
            f"Цена: <code>{format_number(data['price'])} izzzy</code>\n"
            f"Прибыль/час: <code>{format_number(data['profit_per_hour'])} izzzy</code>\n"
            f"Обслуживание: <code>{format_number(data['upkeep_cost'])} izzzy</code>\n"
            f"-----------------------------------------\n"
        )
    
    text += (
        "\n<b>Как купить:</b>\n"
        "<code>купить машину [название]</code>\n"
        "<i>Можно иметь только одну машину!</i>"
    )
    
    # Создаем клавиатуру для первой страницы
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Кнопки покупки машин с первой страницы
    for name in page1_cars:
        markup.add(InlineKeyboardButton(f"Купить {name}", callback_data=f"car_buy_{user.id}_{name}"))
    
    # Если есть вторая страница - кнопка "Далее"
    if page2_cars:
        markup.add(InlineKeyboardButton("Далее", callback_data=f"car_page_2_{user.id}"))
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    logger.info(f"{user.username} открыл магазин машин (страница 1)")


# ================== ОБРАБОТЧИК ПАГИНАЦИИ МАШИН ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("car_page_"))
def callback_car_pagination(call):
    try:
        user_id = int(call.data.split("_")[3])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        page_num = int(call.data.split("_")[2])
        show_car_page(call, page_num)
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка в пагинации машин: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


def show_car_page(call, page_num):
    """Показывает страницу с машинами"""
    user_id = int(call.data.split("_")[3])
    user = call.from_user
    
    mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
    
    # Разделяем машины на две страницы
    car_list = list(CAR_DATA.keys())
    half = len(car_list) // 2
    page1_cars = car_list[:half]
    page2_cars = car_list[half:]
    
    text = (
        f"🚗 <b>Магазин машин</b>\n"
        f"-----------------------------------------\n"
        f"👤 Покупатель: {mention}\n\n"
        f"<i>Выбери машину своей мечты:</i>\n\n"
    )
    
    # Показываем машины в зависимости от страницы
    if page_num == 2 and page2_cars:
        current_cars = page2_cars
    else:
        current_cars = page1_cars
        page_num = 1
    
    for name in current_cars:
        data = CAR_DATA[name]
        text += (
            f"<b>{name}</b>\n"
            f"Цена: <code>{format_number(data['price'])} izzzy</code>\n"
            f"Прибыль/час: <code>{format_number(data['profit_per_hour'])} izzzy</code>\n"
            f"Обслуживание: <code>{format_number(data['upkeep_cost'])} izzzy</code>\n"
            f"-------------------------------------------\n"
        )
    
    text += (
        "\n<b>Как купить:</b>\n"
        "<code>купить машину [название]</code>\n"
        "<i>Можно иметь только одну машину!</i>"
    )
    
    # Создаем клавиатуру
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Кнопки покупки машин
    for name in current_cars:
        markup.add(InlineKeyboardButton(f"Купить {name}", callback_data=f"car_buy_{user_id}_{name}"))
    
    # Кнопки навигации
    nav_buttons = []
    
    if page_num == 2 and page1_cars:
        # На второй странице - только кнопка "Назад"
        nav_buttons.append(InlineKeyboardButton("Назад", callback_data=f"car_page_1_{user_id}"))
    elif page_num == 1 and page2_cars:
        # На первой странице - только кнопка "Далее"
        nav_buttons.append(InlineKeyboardButton("Далее", callback_data=f"car_page_2_{user_id}"))
    elif page1_cars and page2_cars:
        # Если есть обе страницы - обе кнопки
        nav_buttons.append(InlineKeyboardButton("Назад", callback_data=f"car_page_1_{user_id}"))
        nav_buttons.append(InlineKeyboardButton("Далее", callback_data=f"car_page_2_{user_id}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    
    logger.info(f"{user.username} перешел на страницу {page_num} машин")

# ================== 💰 ПОКУПКА ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("car_buy_"))
def car_buy(call):
    try:
        _, _, owner_id, car_name = call.data.split("_")
        owner_id = int(owner_id)
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!")
            return
        user_data = get_user_data(owner_id)
        if user_data.get("car"):
            bot.send_message(call.message.chat.id, "❌ У тебя уже есть машина! Сначала продай текущую.")
            return
        if car_name not in CAR_DATA:
            bot.send_message(call.message.chat.id, "❌ Машина не найдена.")
            return
        car_info = CAR_DATA[car_name]
        if user_data["balance"] < car_info["price"]:
            bot.send_message(call.message.chat.id, f"❌ Недостаточно денег! Нужно {format_number(car_info['price'])} izzzy")
            return
        user_data["balance"] -= car_info["price"]
        user_data["car"] = {
            "name": car_name,
            "last_update": datetime.now().isoformat(),
            "profit_accumulated": 0,
            "last_wash": None
        }
        save_casino_data()
        bot.send_message(call.message.chat.id, f"✅ Ты купил {stylize_text(car_name)} за <code>{format_number(car_info['price'])} izzzy</code>! 🚗", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка покупки машины: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при покупке машины!")

# ================== 💸 ПРОДАЖА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("продать машину"))
def sell_car(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        if not user_data.get("car"):
            bot.send_message(message.chat.id, "🚫 У тебя нет машины для продажи!")
            return
        car_name = user_data["car"]["name"]
        car_info = CAR_DATA[car_name]
        sell_price = car_info["price"] // 2
        user_data["balance"] += sell_price
        user_data["car"] = None
        save_casino_data()
        bot.send_message(message.chat.id, f"✅ Ты продал {stylize_text(car_name)} за <code>{format_number(sell_price)} izzzy</code>!", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка продажи машины: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при продаже машины!")

# ================== 🚘 МОЯ МАШИНА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["моя машина", "машина"])
def my_car(message):
    user_id = message.from_user.id
    user = message.from_user
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    user_data = get_user_data(user_id)
    if not user_data.get("car"):
        bot.send_message(message.chat.id, "🚫 У тебя нет машины. Купи её в магазине машин!")
        return
    update_car_stats(user_data)
    car = user_data["car"]
    car_info = CAR_DATA[car["name"]]
    text = (
        f"🚘 <b>{stylize_text(car['name'].capitalize())}</b>\n"
        f"--------------------------------------------\n"
        f"👤 Владелец: {mention}\n"
        f"💲 Прибыль/час: <code>{format_number(car_info['profit_per_hour'])} izzzy</code>\n"
        f"💰 Накоплено: <code>{format_number(car['profit_accumulated'])} izzzy</code>\n"
        f"⛽Топливо стоит: <code>{format_number(car_info['upkeep_cost'])} izzzy</code>\n"
        f"--------------------------------------------"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("💰 Собрать прибыль", callback_data=f"car_collect_{user_id}"),
        InlineKeyboardButton("⛽ Заправить", callback_data=f"car_upkeep_{user_id}")
    )
    markup.row(InlineKeyboardButton("🚿 Помыть машину", callback_data=f"car_wash_{user_id}"))
    try:
        if car_info.get('image'):
            bot.send_photo(message.chat.id, car_info['image'], caption=text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

# ================== 💰 СОБРАТЬ ПРИБЫЛЬ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("car_collect_"))
def car_collect(call):
    try:
        _, _, owner_id = call.data.split("_")
        owner_id = int(owner_id)
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Не твоя кнопка!")
            return
        user_data = get_user_data(owner_id)
        car = user_data.get("car")
        if not car:
            bot.send_message(call.message.chat.id, "🚫 У тебя нет машины.")
            return
        update_car_stats(user_data)
        collected = car["profit_accumulated"]
        if collected <= 0:
            bot.send_message(call.message.chat.id, "⚠️ Нет накопленной прибыли.")
            return
        user_data["balance"] += collected
        car["profit_accumulated"] = 0
        save_casino_data()
        bot.send_message(call.message.chat.id, f"💰 Ты собрал <code>{format_number(collected)} izzzy</code> прибыли!", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка car_collect: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при сборе прибыли.")

# ================== 🔧 СОДЕРЖАНИЕ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("car_upkeep_"))
def car_upkeep(call):
    try:
        _, _, owner_id = call.data.split("_")
        owner_id = int(owner_id)
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Не твоя кнопка!")
            return
        user_data = get_user_data(owner_id)
        car = user_data.get("car")
        if not car:
            bot.send_message(call.message.chat.id, "🚫 У тебя нет машины.")
            return
        car_info = CAR_DATA[car["name"]]
        cost = car_info["upkeep_cost"]
        if user_data["balance"] < cost:
            bot.send_message(call.message.chat.id, f"❌ Недостаточно средств! Нужно <code>{format_number(cost)}$</code>.", parse_mode="HTML")
            return
        user_data["balance"] -= cost
        save_casino_data()
        bot.send_message(call.message.chat.id, f"⛽ Ты заправил свою машину за <code>{format_number(cost)} izzzy</code>.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка car_upkeep: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при оплате содержания.")

# ================== 🚿 МОЙКА МАШИНЫ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("car_wash_"))
def car_wash(call):
    try:
        _, _, owner_id = call.data.split("_")
        owner_id = int(owner_id)
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!")
            return
        user_data = get_user_data(owner_id)
        if not user_data.get("car"):
            bot.send_message(call.message.chat.id, "🚫 У тебя нет машины.")
            return
        car = user_data["car"]
        now = datetime.now()
        cooldown = timedelta(hours=6)
        last_wash_str = car.get("last_wash")
        if last_wash_str:
            last_wash = datetime.fromisoformat(last_wash_str)
            next_time = last_wash + cooldown
            if now < next_time:
                remain = next_time - now
                hours, minutes = divmod(remain.seconds // 60, 60)
                mention = f'<a href="tg://user?id={call.from_user.id}">{call.from_user.first_name}</a>'
                bot.send_message(
                    call.message.chat.id,
                    f"🧽 {mention}, ты уже мыл свою машину в <b>{last_wash.strftime('%d.%m %H:%M')}</b>.\n"
                    f"Она ещё чистая ✨\n"
                    f"Следующая мойка через <b>{hours} ч {minutes} мин</b>.",
                    parse_mode="HTML"
                )
                return
        reward = random.randint(5000, 150000)
        car["last_wash"] = now.isoformat()
        user_data["balance"] += reward
        save_casino_data()
        mention = f'<a href="tg://user?id={call.from_user.id}">{call.from_user.first_name}</a>'
        bot.send_message(
            call.message.chat.id,
            f"🚿 {mention} помыл(а) свою машину до блеска ✨\n"
            f"💸 На твой баланс зачислено <code>{format_number(reward)} izzzy</code>!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка car_wash: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при мойке машины.")

# ================== СИСТЕМА ЛИМИТОВ ПЕРЕВОДОВ ==================
# Максимальная сумма переводов в день (50 млн)
MAX_TRANSFER_DAILY = 50000000

# Файл для хранения исключений (пользователи без лимита)
TRANSFER_EXCEPTIONS_FILE = "transfer_exceptions.json"

def load_transfer_exceptions():
    try:
        if os.path.exists(TRANSFER_EXCEPTIONS_FILE):
            with open(TRANSFER_EXCEPTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Ошибка загрузки исключений переводов: {e}")
        return []

def save_transfer_exceptions(exceptions):
    try:
        with open(TRANSFER_EXCEPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(exceptions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения исключений переводов: {e}")

def is_transfer_limit_exempt(user_id):
    exceptions = load_transfer_exceptions()
    return user_id in exceptions

# ================== АДМИН КОМАНДА: СНЯТЬ ЛИМИТ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("снять лимит"))
def admin_remove_transfer_limit(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ <b>Использование:</b> Ответьте на сообщение пользователя командой <code>снять лимит</code>", parse_mode="HTML")
            return
        target_user = message.reply_to_message.from_user
        target_id = target_user.id
        if target_id == user_id:
            bot.reply_to(message, "❌ Нельзя снять лимит самому себе!", parse_mode="HTML")
            return
        exceptions = load_transfer_exceptions()
        if target_id in exceptions:
            return
        exceptions.append(target_id)
        save_transfer_exceptions(exceptions)
        admin_mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        target_mention = f'<a href="tg://user?id={target_id}">{target_user.first_name}</a>'
        bot.reply_to(message, f"✅ <b>ЛИМИТ ПЕРЕВОДОВ СНЯТ</b>\n\n🛡 Администратор: {admin_mention}\n👤 Пользователь: {target_mention}\n💰 Теперь может переводить неограниченные суммы!", parse_mode="HTML")
        logger.info(f"Админ {user_id} снял лимит переводов для пользователя {target_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка в команде снять лимит: {e}")

# ================== АДМИН КОМАНДА: ВЕРНУТЬ ЛИМИТ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("вернуть лимит"))
def admin_restore_transfer_limit(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ <b>Использование:</b> Ответьте на сообщение пользователя командой <code>вернуть лимит</code>", parse_mode="HTML")
            return
        target_user = message.reply_to_message.from_user
        target_id = target_user.id
        exceptions = load_transfer_exceptions()
        if target_id not in exceptions:
            return
        exceptions.remove(target_id)
        save_transfer_exceptions(exceptions)
        admin_mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        target_mention = f'<a href="tg://user?id={target_id}">{target_user.first_name}</a>'
        bot.reply_to(message, f"🔄 <b>ЛИМИТ ПЕРЕВОДОВ ВОССТАНОВЛЕН</b>\n\n🛡 Администратор: {admin_mention}\n👤 Пользователь: {target_mention}\n💰 Теперь действует стандартный лимит: {format_number(MAX_TRANSFER_DAILY)}$ в день", parse_mode="HTML")
        logger.info(f"Админ {user_id} вернул лимит переводов для пользователя {target_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка в команде вернуть лимит: {e}")

# ================== 💳 ПЕРЕВОД ДЕНЕГ С ЛИМИТАМИ ==================

@bot.message_handler(func=lambda m: m.text and any(
    m.text.lower().startswith(cmd) for cmd in ["п ", "перевести ", "перевод "]
))
def transfer_money(message):
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которому хотите перевести деньги.")
            return
        sender_id = message.from_user.id
        recipient_id = message.reply_to_message.from_user.id
        if sender_id == recipient_id:
            bot.reply_to(message, "❌ Нельзя переводить деньги самому себе!")
            return
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: п [сумма] (например: п 1000, п 2k, п 5к, п 1kk, п 3кк)")
            return
        amount_text = parts[1].lower()
        if amount_text.endswith("kk") or amount_text.endswith("кк"):
            amount = int(float(amount_text[:-2]) * 1000000)
        elif amount_text.endswith("k") or amount_text.endswith("к"):
            amount = int(float(amount_text[:-1]) * 1000)
        else:
            try:
                amount = int(amount_text)
            except ValueError:
                bot.reply_to(message, "❌ Неверный формат суммы!")
                return
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть положительной!")
            return
        sender_data = get_user_data(sender_id)
        recipient_data = get_user_data(recipient_id)
        if sender_data["balance"] < amount:
            bot.reply_to(message, f"❌ Недостаточно средств! Ваш баланс: {format_number(sender_data['balance'])} izzzy")
            return
        max_balance = 1000000000000000000000000000000
        if recipient_data["balance"] + amount > max_balance:
            bot.reply_to(message, f"❌ У получателя достигнут максимальный баланс ({format_number(max_balance)} izzzy)!")
            return
        if not is_transfer_limit_exempt(sender_id):
            today = date.today().isoformat()
            if sender_data["daily_transfers"]["date"] != today:
                sender_data["daily_transfers"] = {"date": today, "amount": 0}
                save_casino_data()
            if sender_data["daily_transfers"]["amount"] + amount > MAX_TRANSFER_DAILY:
                remaining = MAX_TRANSFER_DAILY - sender_data["daily_transfers"]["amount"]
                bot.reply_to(message, f"❌ Вы превысили дневной лимит переводов ({format_number(MAX_TRANSFER_DAILY)} izzzy)!\n💰 Сегодня можно перевести ещё: {format_number(remaining)} izzzy\n\n<i>Лимит обнуляется каждый день в 00:00 по МСК</i>", parse_mode="HTML")
                return
        fee = 0
        received_amount = amount
        fee_info = ""
        if amount > 100000:
            fee = int(amount * 0.10)
            received_amount = amount - fee
            fee_info = f"💸 <b>Комиссия (10%):</b> <code>-{format_number(fee)} izzzy</code>\n"
        sender_data["balance"] -= amount
        recipient_data["balance"] = min(recipient_data["balance"] + received_amount, max_balance)
        if not is_transfer_limit_exempt(sender_id):
            sender_data["daily_transfers"]["amount"] += amount
        save_casino_data()
        
        # Отправка уведомления отправителю
        sender_name = f"<a href='tg://user?id={sender_id}'>{message.from_user.first_name}</a>"
        recipient_name = f"<a href='tg://user?id={recipient_id}'>{message.reply_to_message.from_user.first_name}</a>"
        text = f"🥥 Вы успешно перевели пользователю {recipient_name}\n{fee_info}🍉 Сумма перевода с комиссией: <code>{format_number(received_amount)} izzzy</code>"
        bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)
        
        # Логирование
        logger.info(f"Перевод: {message.from_user.first_name} → {message.reply_to_message.from_user.first_name} | Отправил: {amount}$, Получил: {received_amount}$")
        
    except (IndexError, ValueError) as e:
        bot.reply_to(message, f"❌ Неверный формат! Использование: п [сумма] (например: п 1000, п 2k, п 5к, п 1kk, п 3кк)\nОшибка: {e}")
    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при переводе средств!")

# ================== МОЙ ПРОФИЛЬ (ОБНОВЛЕННАЯ ВЕРСИЯ) ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой профиль", "профиль"])
def my_profile(message):
    """Показывает профиль пользователя с расширенной информацией"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'
    
    # Получаем данные пользователя
    user_data = get_user_data(user_id)
    
    # Получаем описание профиля (био)
    try:
        user = bot.get_chat(user_id)
        user_bio = getattr(user, 'bio', None)
        if user_bio:
            bio_text = user_bio
        else:
            bio_text = "Нету..."
    except:
        bio_text = "Нету..."
    
    # Получаем username
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет"
    
    # Получаем префикс
    prefix_data = get_user_prefix(user_id)
    prefix_display = prefix_data["name"] if prefix_data else "Нет"
    
    # Получаем VIP статус
    vip_data = user_data.get("vip", {})
    vip_level = vip_data.get("level", 0)
    if vip_level > 0:
        vip_info = VIP_LEVELS.get(vip_level, {})
        vip_display = f"{vip_info.get('prefix', '⭐')} {vip_info.get('name', 'VIP')}"
    else:
        vip_display = "Нет"
    
    # Получаем информацию о браке
    marriage = get_marriage(user_id)
    if marriage:
        partner_id = marriage["partner_id"]
        try:
            partner = bot.get_chat(partner_id)
            partner_name = partner.first_name
            partner_mention = f'<a href="tg://user?id={partner_id}">{partner_name}</a>'
            marriage_status = f"В браке с {partner_mention}"
        except:
            marriage_status = "В браке"
    else:
        marriage_status = "Не в браке"
    
    # Получаем информацию о рефералах
    ref_data = get_user_referral_data(user_id)
    referrals_count = len(ref_data.get("referrals", []))
    
    # Получаем информацию о питомце
    pet_data = get_pet(user_id)
    if pet_data:
        pet_id, pet_name, pet_price, pet_satiety, pet_level, pet_xp, pet_last_update = pet_data
        pet_info = f"{pet_name} (ур. {pet_level})"
    else:
        pet_info = "Нет"
    
    # Получаем информацию о тянке
    if user_data.get("tyanka"):
        tyanka_name = user_data["tyanka"].get("name", "Неизвестно")
        tyanka_info = f"{tyanka_name}"
    else:
        tyanka_info = "Нет"
    
    # Получаем информацию о машине
    if user_data.get("car"):
        car_name = user_data["car"].get("name", "Неизвестно")
        car_info = f"{car_name}"
    else:
        car_info = "Нет"
    
    # Получаем информацию о бизнесе
    if user_data.get("business"):
        business_name = user_data["business"].get("name", "Неизвестно")
        business_info = f"{business_name}"
    else:
        business_info = "Нет"
    
    # Получаем информацию о доме
    if user_data.get("house"):
        house_name = user_data["house"].get("name", "Неизвестно")
        house_info = f"{house_name}"
    else:
        house_info = "Нет"
    
    # Формируем текст профиля со стикерами и жирными шрифтами
    text = (
        f"👤 <b>Ник:</b> {mention}\n"
        f"📱 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"📝 <b>Описание:</b> {bio_text}\n"
        f"💰 <b>Баланс:</b> <code>{format_number(user_data['balance'])} izzzy</code>\n"
        f"🏷️ <b>Префикс:</b> {prefix_display}\n"
        f"💎 <b>VIP:</b> {vip_display}\n"
        f"💍 <b>Брак:</b> {marriage_status}\n"
        f"👥 <b>Рефералы:</b> {referrals_count}\n"
        f"🐾 <b>Питомец:</b> {pet_info}\n"
        f"👩 <b>Тянка:</b> {tyanka_info}\n"
        f"🚗 <b>Машина:</b> {car_info}\n"
        f"🏢 <b>Бизнес:</b> {business_info}\n"
        f"🏠 <b>Дом:</b> {house_info}"
    )
    
    # Пробуем получить аватарку пользователя
    try:
        # Получаем файлы фото пользователя
        user_photos = bot.get_user_profile_photos(user_id)
        
        if user_photos.total_count > 0:
            # Берем самое последнее фото (индекс 0)
            file_id = user_photos.photos[0][-1].file_id  # Берем фото с наибольшим разрешением
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Отправляем фото с подписью
            bot.send_photo(
                message.chat.id,
                downloaded_file,
                caption=text,
                parse_mode="HTML",
                reply_to_message_id=message.message_id
            )
        else:
            # Если аватарки нет - отправляем текстом
            bot.reply_to(message, text, parse_mode="HTML")
            
    except Exception as e:
        # В случае ошибки (например, пользователь скрыл аватарку) - отправляем текстом
        print(f"Ошибка при получении аватарки: {e}")
        bot.reply_to(message, text, parse_mode="HTML")

# ================== ПРОМОКОДЫ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("промо "))
def activate_promo(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        promo_name = message.text.split()[1]
        
        if promo_name not in promocodes:
            bot.reply_to(message, "❌ Промокод не найден!")
            return
            
        promo = promocodes[promo_name]
        
        if user_id in promo["activated_by"]:
            bot.reply_to(message, "❌ Вы уже активировали этот промокод!")
            return
            
        if promo["current_activations"] >= promo["max_activations"]:
            bot.reply_to(message, "❌ Промокод исчерпал лимит активаций!")
            return
            
        # Активируем промокод
        actual_amount = add_income(user_id, promo["amount"], "promo")
        promo["current_activations"] += 1
        promo["activated_by"].append(user_id)
        
        save_casino_data()
        save_promocodes()
        
        # Создаем кликабельное упоминание пользователя
        user_mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        if actual_amount > 0:
            # Формируем сообщение в нужном формате
            response_text = f"{user_mention}, ты успешно активировал промокод и получил <code>{format_number(actual_amount)} izzzy</code>"
            bot.reply_to(message, response_text, parse_mode="HTML")
        else:
            bot.reply_to(message, "✅ Промокод активирован, но достигнут дневной лимит дохода!")
        
        logger.info(f"Пользователь {message.from_user.username} активировал промокод {promo_name}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: промо [название]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка активации промокода!")
        logger.error(f"Ошибка активации промокода: {e}")

# ================== ОБРАБОТКА СТАВОК ==================
@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def handle_bet(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["stage"] not in ["enter_bet", "roulette_bet"]:
        return

    bet = int(message.text)
    if bet <= 0 or bet > user_data["balance"]:
        bot.send_message(message.chat.id, "❌ Неверная ставка!")
        return

    user_data["bet"] = bet
    user_data["balance"] -= bet

    if user_data["game"] == "blackjack":
        user_data["stage"] = "playing"
        save_casino_data()
        bot.send_photo(
            message.chat.id,
            BLACKJACK_IMAGE_URL,
            caption=(
                f"🎯 Ваша ставка: {format_number(bet)}\n\n"
                f"Ваши карты: {format_hand(user_data['player'])} ({hand_value(user_data['player'])})\n"
                f"Карты дилера: {format_hand(user_data['dealer'], True)}"
            ),
            reply_markup=bj_action_keyboard()
        )

    elif user_data["game"] == "roulette":
        user_data["stage"] = "roulette_choice"
        save_casino_data()
        bot.send_photo(message.chat.id, CASINO_IMAGE_URL, 
                      caption=f"🎡 Ставка {format_number(bet)} принята.\nВыберите вариант:", 
                      reply_markup=roulette_keyboard())

# ================== ОБРАБОТКА РУЛЕТКИ (ЧИСЛО) ==================
@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and 
                    get_user_data(m.from_user.id)["stage"] == "roulette_number_input")
def roulette_number_choice(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    number_choice = int(message.text)
    if not (0 <= number_choice <= 36):
        bot.send_message(message.chat.id, "❌ Введите число от 0 до 36!")
        return

    number, color = roulette_spin()
    if number_choice == number:
        payout = user_data["bet"] * 36
        actual_payout = add_income(user_id, payout, "roulette")
        if actual_payout > 0:
            text = f"🎉 Джекпот! Выпало {number} ({color}).\nВыигрыш: {format_number(actual_payout)}\nБаланс: {format_number(user_data['balance'])}"
        else:
            text = f"🎉 Джекпот! Но достигнут дневной лимит дохода.\nБаланс: {format_number(user_data['balance'])}"
    else:
        text = f"❌ Вы проиграли. Выпало {number} ({color}).\nБаланс: {format_number(user_data['balance'])}"

    bot.send_photo(message.chat.id, CASINO_IMAGE_URL, caption=text)
    user_data["stage"] = "finished"
    save_casino_data()



@bot.callback_query_handler(func=lambda call: call.data.startswith('tyanka_collect_'))
def callback_tyanka_collect(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваша тянка!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("tyanka"):
        bot.send_message(call.message.chat.id, "❌ У вас нет тянка!")
        return
        
    update_tyanka_stats(user_data)
    
    profit = user_data["tyanka"]["profit_accumulated"]
    if profit <= 0:
        bot.send_message(call.message.chat.id, "❌ Нет накопленной прибыли для сбора!")
        return
        
    actual_profit = add_income(user_id, profit, "tyanka")
    user_data["tyanka"]["profit_accumulated"] = 0
    save_casino_data()
    
    if actual_profit > 0:
        bot.send_message(call.message.chat.id, f"✅ Вы собрали {format_number(actual_profit)}$ прибыли!")
    else:
        bot.send_message(call.message.chat.id, "❌ Достигнут дневной лимит дохода!")
    
    logger.info(f"Пользователь {call.from_user.username} собрал прибыль через кнопку")

@bot.callback_query_handler(func=lambda call: call.data.startswith('tyanka_feed_'))
def callback_tyanka_feed(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваша тянка!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("tyanka"):
        bot.send_message(call.message.chat.id, "❌ У вас нет тянка!")
        return
        
    feed_cost = TYANKA_DATA[user_data["tyanka"]["name"]]["feed_cost"]
    
    if user_data["balance"] < feed_cost:
        bot.send_message(call.message.chat.id, f"❌ Недостаточно средств для кормления ({format_number(feed_cost)}$)!")
        return
        
    user_data["balance"] -= feed_cost
    user_data["tyanka"]["satiety"] = 100
    save_casino_data()
    
    bot.send_message(call.message.chat.id, f"✅ Вы накормили тянку! Сытость восстановлена до 100. Потрачено {format_number(feed_cost)}$.")
    logger.info(f"Пользователь {call.from_user.username} покормил тянку через кнопку")

@bot.callback_query_handler(func=lambda call: call.data.startswith('business_collect_'))
def callback_business_collect(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваш бизнес!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("business"):
        bot.send_message(call.message.chat.id, "❌ У вас нет бизнеса!")
        return
        
    update_business_stats(user_data)
    business = user_data["business"]
    
    profit = business["profit_accumulated"]
    if profit <= 0:
        bot.send_message(call.message.chat.id, "❌ Нет накопленной прибыли для сбора!")
        return
        
    actual_profit = add_income(user_id, profit, "business")
    business["profit_accumulated"] = 0
    save_casino_data()
    
    if actual_profit > 0:
        bot.send_message(call.message.chat.id, f"✅ Вы собрали {format_number(actual_profit)}$ прибыли с бизнеса!")
    else:
        bot.send_message(call.message.chat.id, "❌ Достигнут дневной лимит дохода!")
    
    logger.info(f"Пользователь {call.from_user.username} собрал прибыль с бизнеса через кнопку")

@bot.callback_query_handler(func=lambda call: call.data.startswith('business_buy_'))
def callback_business_buy(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваш бизнес!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("business"):
        bot.send_message(call.message.chat.id, "❌ У вас нет бизнеса!")
        return
        
    business_info = BUSINESS_DATA[user_data["business"]["name"]]
    price = business_info["material_cost"]
    
    if user_data["balance"] < price:
        bot.send_message(call.message.chat.id, f"❌ Недостаточно средств для покупки материалов ({format_number(price)}$)!")
        return
        
    user_data["balance"] -= price
    user_data["business"]["materials"] += business_info["material_units"]
    save_casino_data()
    
    bot.send_message(call.message.chat.id, f"✅ Вы купили {business_info['material_units']} материалов за {format_number(price)}$!")
    logger.info(f"Пользователь {call.from_user.username} купил материалы через кнопку")

@bot.callback_query_handler(func=lambda call: call.data.startswith('house_collect_'))
def callback_house_collect(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваш дом!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("house"):
        bot.send_message(call.message.chat.id, "❌ У вас нет дома!")
        return
        
    update_house_stats(user_data)
    house = user_data["house"]
    
    profit = house["profit_accumulated"]
    if profit <= 0:
        bot.send_message(call.message.chat.id, "❌ Нет накопленной арендной платы для сбора!")
        return
        
    actual_profit = add_income(user_id, profit, "house")
    house["profit_accumulated"] = 0
    save_casino_data()
    
    if actual_profit > 0:
        bot.send_message(call.message.chat.id, f"✅ Вы собрали {format_number(actual_profit)}$ арендной платы!")
    else:
        bot.send_message(call.message.chat.id, "❌ Достигнут дневной лимит дохода!")
    
    logger.info(f"Пользователь {call.from_user.username} собрал аренду через кнопку")

@bot.callback_query_handler(func=lambda call: call.data.startswith('house_upkeep_'))
def callback_house_upkeep(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваш дом!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("house"):
        bot.send_message(call.message.chat.id, "❌ У вас нет дома!")
        return
        
    house_info = HOUSE_DATA[user_data["house"]["name"]]
    upkeep_cost = house_info["upkeep_cost"]
    
    if user_data["balance"] < upkeep_cost:
        bot.send_message(call.message.chat.id, f"❌ Недостаточно средств для оплаты содержания ({format_number(upkeep_cost)}$)!")
        return
        
    user_data["balance"] -= upkeep_cost
    save_casino_data()
    
    bot.send_message(call.message.chat.id, f"✅ Вы оплатили содержание дома! Потрачено {format_number(upkeep_cost)}$.")
    logger.info(f"Пользователь {call.from_user.username} оплатил содержание дома через кнопку")

@bot.callback_query_handler(func=lambda call: call.data.startswith('car_collect_'))
def callback_car_collect(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваша машина!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("car"):
        bot.send_message(call.message.chat.id, "❌ У вас нет машины!")
        return
        
    update_car_stats(user_data)
    car = user_data["car"]
    
    profit = car["profit_accumulated"]
    if profit <= 0:
        bot.send_message(call.message.chat.id, "❌ Нет накопленной арендной платы для сбора!")
        return
        
    actual_profit = add_income(user_id, profit, "car")
    car["profit_accumulated"] = 0
    save_casino_data()
    
    if actual_profit > 0:
        bot.send_message(call.message.chat.id, f"✅ Вы собрали {format_number(actual_profit)}$ арендной платы!")
    else:
        bot.send_message(call.message.chat.id, "❌ Достигнут дневной лимит дохода!")
    
    logger.info(f"Пользователь {call.from_user.username} собрал аренду через кнопку")

@bot.callback_query_handler(func=lambda call: call.data.startswith('car_upkeep_'))
def callback_car_upkeep(call):
    bot.answer_callback_query(call.id)
    user_id = int(call.data.split('_')[2])
    
    if call.from_user.id != user_id:
        bot.send_message(call.message.chat.id, "❌ Это не ваша машина!")
        return
        
    user_data = get_user_data(user_id)
    
    if not user_data.get("car"):
        bot.send_message(call.message.chat.id, "❌ У вас нет машины!")
        return
        
    car_info = CAR_DATA[user_data["car"]["name"]]
    upkeep_cost = car_info["upkeep_cost"]
    
    if user_data["balance"] < upkeep_cost:
        bot.send_message(call.message.chat.id, f"❌ Недостаточно средств для оплаты содержания ({format_number(upkeep_cost)}$)!")
        return
        
    user_data["balance"] -= upkeep_cost
    save_casino_data()
    
    bot.send_message(call.message.chat.id, f"✅ Вы оплатили содержание машины! Потрачено {format_number(upkeep_cost)}$.")
    logger.info(f"Пользователь {call.from_user.username} оплатил содержание машины через кнопку")

# ================== ОБРАБОТКА РУЛЕТКИ ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith('roulette_'))
def callback_roulette(call):
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["stage"] != "roulette_choice":
        bot.answer_callback_query(call.id, "❌ Ставка уже обработана!")
        return
        
    choice = call.data.replace('roulette_', '')
    user_data["choice"] = choice
    
    if choice == "number":
        user_data["stage"] = "roulette_number_input"
        bot.send_message(call.message.chat.id, "🎲 Введите число от 0 до 36:")
        bot.answer_callback_query(call.id)
        return
        
    number, color = roulette_spin()
    win = False
    
    if choice == "red" and color == "красное":
        win = True
    elif choice == "black" and color == "черное":
        win = True
    elif choice == "even" and number % 2 == 0 and number != 0:
        win = True
    elif choice == "odd" and number % 2 == 1:
        win = True
        
    if win:
        payout = user_data["bet"] * config["roulette_win_multiplier"]
        actual_payout = add_income(user_id, payout, "roulette")
        if actual_payout > 0:
            text = f"🎉 Поздравляем! Выпало {number} ({color}).\nВыигрыш: {format_number(actual_payout)}\nБаланс: {format_number(user_data['balance'])}"
        else:
            text = f"🎉 Поздравляем! Но достигнут дневной лимит дохода.\nБаланс: {format_number(user_data['balance'])}"
    else:
        text = f"❌ Вы проиграли. Выпало {number} ({color}).\nБаланс: {format_number(user_data['balance'])}"
        
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=text
    )
    user_data["stage"] = "finished"
    save_casino_data()
    bot.answer_callback_query(call.id)



# ================== РАССЫЛКА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("рассылка "))
def broadcast_message(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        text = message.text.split(maxsplit=1)[1]
        total = len(casino_data)
        success = 0
        
        msg = bot.send_message(message.chat.id, f"📢 Рассылка начата... Обработано 0/{total}")
        
        for i, (user_id, data) in enumerate(casino_data.items(), 1):
            try:
                bot.send_message(user_id, text)
                success += 1
            except:
                pass
                
            if i % 10 == 0:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=f"📢 Рассылка... Обработано {i}/{total}"
                )
                
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"✅ Рассылка завершена!\nУспешно: {success}/{total}"
        )
        logger.info(f"Админ {message.from_user.username} сделал рассылку: {text}")
        
    except IndexError:
        bot.reply_to(message, "❌ Используйте: рассылка [текст]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка рассылки!")
        logger.error(f"Ошибка рассылки: {e}")

        

# ================== ОБНОВЛЕННАЯ КОМАНДА ЛОГОВ /log ==================

# Словарь для хранения временных состояний, чтобы знать, какой лог мы ждем
_log_request_state = {}

@bot.message_handler(commands=['log'])
def log_panel(message):
    """Показывает панель управления логами (только для админов)"""
    user_id = message.from_user.id

    # Проверка на администратора
    if user_id not in ADMIN_IDS:
        # Игнорируем команду от обычного пользователя
        logger.info(f"Пользователь {user_id} попытался использовать команду /log")
        return

    # Текст панели
    panel_text = (
        "📋 <b>Панель управления логами</b>\n\n"
        "Выберите тип лога для просмотра:"
    )

    # Создаем клавиатуру с кнопками
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 Лог пользователя", callback_data="log_user"),
        InlineKeyboardButton("📜 Весь лог (bot_logs.txt)", callback_data="log_full")
    )
    markup.add(
        InlineKeyboardButton("💸 Лог переводов", callback_data="log_transfers"),
        InlineKeyboardButton("🛒 Лог покупок", callback_data="log_purchases")
    )
    markup.add(
        InlineKeyboardButton("🎮 Лог игр", callback_data="log_games")
    )

    bot.send_message(message.chat.id, panel_text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('log_'))
def log_callback_handler(call):
    """Обрабатывает нажатия на кнопки в панели логов"""
    user_id = call.from_user.id

    # Двойная проверка на администратора (на всякий случай)
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
        return

    action = call.data.split('_', 1)[1] # Отделяем 'log_' от остальной части

    # --- Обработка кнопки "Весь лог" (сразу отправляем файл) ---
    if action == "full":
        bot.answer_callback_query(call.id) # Просто закрываем уведомление
        try:
            with open("bot_logs.txt", "rb") as f:
                bot.send_document(call.message.chat.id, f, caption="📋 Полный лог бота (bot_logs.txt)")
            logger.info(f"Админ {user_id} запросил полный лог")
        except FileNotFoundError:
            bot.send_message(call.message.chat.id, "❌ Файл bot_logs.txt не найден.")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Ошибка отправки лога: {e}")
            logger.error(f"Ошибка отправки полного лога: {e}")
        return

    # --- Для остальных кнопок (где нужен ID пользователя) ---
    # Сохраняем, какой лог хочет админ
    _log_request_state[user_id] = action
    bot.answer_callback_query(call.id)

    # Запрашиваем ID
    bot.send_message(
        call.message.chat.id,
        f"👤 Введите ID пользователя для получения лога '<b>{action}</b>':",
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda message: message.from_user.id in _log_request_state)
def handle_log_id_input(message):
    """Обрабатывает ввод ID пользователя для получения конкретного лога"""
    admin_id = message.from_user.id

    # Проверка на администратора (на всякий случай)
    if admin_id not in ADMIN_IDS:
        # Если вдруг состояние осталось, но юзер не админ — чистим и игнорим
        _log_request_state.pop(admin_id, None)
        return

    # Получаем тип запрошенного лога из временного хранилища
    log_type = _log_request_state.pop(admin_id) # Удаляем запись после получения

    target_user_id = message.text.strip()

    # Простейшая валидация, что ввели число
    if not target_user_id.isdigit():
        bot.send_message(message.chat.id, "❌ ID должен состоять только из цифр. Попробуйте снова через /log.")
        return

    # Определяем имя файла в зависимости от типа лога
    filename = None
    caption_prefix = ""
    if log_type == "user":
        # Для лога пользователя мы должны создать отдельный файл.
        # Так как в исходном коде нет отдельного лога по пользователям,
        # мы создадим временный файл, отфильтровав основной лог.
        # Это пример. В идеале, нужно логировать действия пользователей в отдельный файл.
        try:
            # Попытка отфильтровать основной лог (bot_logs.txt) по ID
            user_log_filename = f"user_{target_user_id}_log.txt"
            with open("bot_logs.txt", "r", encoding="utf-8") as main_log, \
                 open(user_log_filename, "w", encoding="utf-8") as user_log:
                found = False
                for line in main_log:
                    if f" {target_user_id}" in line or f":{target_user_id}]" in line or f"({target_user_id})" in line:
                        user_log.write(line)
                        found = True
                if not found:
                    user_log.write(f"Записей для пользователя {target_user_id} не найдено в основном логе.")

            filename = user_log_filename
            caption_prefix = f"👤 Лог пользователя {target_user_id} (отфильтрован из bot_logs.txt)"
        except FileNotFoundError:
            bot.send_message(message.chat.id, "❌ Основной файл логов (bot_logs.txt) не найден.")
            return
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка обработки лога: {e}")
            logger.error(f"Ошибка фильтрации лога для пользователя {target_user_id}: {e}")
            return

    elif log_type == "transfers":
        filename = "transfer_logs.txt"
        caption_prefix = f"💸 Лог переводов для пользователя {target_user_id}"
    elif log_type == "purchases":
        filename = "purchase_logs.txt"
        caption_prefix = f"🛒 Лог покупок для пользователя {target_user_id}"
    elif log_type == "games":
        filename = "game_logs.txt"
        caption_prefix = f"🎮 Лог игр для пользователя {target_user_id}"
    else:
        bot.send_message(message.chat.id, "❌ Неизвестный тип лога.")
        return

    # Отправляем файл
    try:
        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f, caption=caption_prefix)
        logger.info(f"Админ {admin_id} запросил лог '{log_type}' для пользователя {target_user_id}")
    except FileNotFoundError:
        bot.send_message(message.chat.id, f"❌ Файл {filename} не найден.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка отправки лога: {e}")
        logger.error(f"Ошибка отправки лога {filename}: {e}")
    finally:
        # Если мы создавали временный файл для лога пользователя, удаляем его
        if log_type == "user" and filename and filename.startswith("user_"):
            try:
                import os
                os.remove(filename)
            except:
                pass
        
# ================== 🌟 СИСТЕМА ЗВЁЗД ЗА СООБЩЕНИЯ ==================
STAR_DB = "star_messages.db"
STAR_ENABLED = True  # Глобальный флаг включения/выключения ивента
STAR_CHAT_ID = -1003279681531  # ID чата для подсчёта сообщений
STARS_PER_MESSAGE = 0.005  # 0.01 звезды за 2 сообщения = 0.005 за 1 сообщение
MIN_WITHDRAWAL = 50  # Минимальная сумма для вывода
ADMIN_ID_FOR_STARS = 7526512670  # ID админа для уведомлений о выводах

# Инициализация базы данных
def init_star_db():
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute("""
        CREATE TABLE IF NOT EXISTS star_users (
            user_id INTEGER PRIMARY KEY,
            total_messages INTEGER DEFAULT 0,
            total_stars REAL DEFAULT 0
        )
    """)
    
    # Таблица заявок на вывод
    c.execute("""
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ База данных для звёзд инициализирована")

init_star_db()

# Функции для работы со звёздами
def get_user_star_stats(user_id):
    """Получает статистику пользователя по звёздам"""
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    c.execute("SELECT total_messages, total_stars FROM star_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            "total_messages": result[0],
            "total_stars": result[1]
        }
    return {
        "total_messages": 0,
        "total_stars": 0
    }

def update_user_star_stats(user_id, messages_add=1):
    """Обновляет статистику пользователя (добавляет сообщение и звёзды)"""
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    # Получаем текущие значения
    c.execute("SELECT total_messages, total_stars FROM star_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result:
        total_messages = result[0] + messages_add
        total_stars = result[1] + (messages_add * STARS_PER_MESSAGE)
        c.execute("UPDATE star_users SET total_messages = ?, total_stars = ? WHERE user_id = ?",
                 (total_messages, total_stars, user_id))
    else:
        total_messages = messages_add
        total_stars = messages_add * STARS_PER_MESSAGE
        c.execute("INSERT INTO star_users (user_id, total_messages, total_stars) VALUES (?, ?, ?)",
                 (user_id, total_messages, total_stars))
    
    conn.commit()
    conn.close()
    return total_messages, total_stars

def deduct_stars(user_id, amount):
    """Списывает звёзды с баланса пользователя"""
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    c.execute("SELECT total_stars FROM star_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if not result or result[0] < amount:
        conn.close()
        return False
    
    new_balance = result[0] - amount
    c.execute("UPDATE star_users SET total_stars = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()
    return True

def create_withdrawal_request(user_id, username, amount):
    """Создаёт заявку на вывод звёзд"""
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO withdrawal_requests (user_id, username, amount, status)
        VALUES (?, ?, ?, 'pending')
    """, (user_id, username, amount))
    
    request_id = c.lastrowid
    conn.commit()
    conn.close()
    return request_id

def get_pending_withdrawal_requests():
    """Получает все ожидающие заявки на вывод"""
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    c.execute("""
        SELECT id, user_id, username, amount, created_at
        FROM withdrawal_requests
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """)
    
    requests = c.fetchall()
    conn.close()
    return requests

def update_withdrawal_status(request_id, status):
    """Обновляет статус заявки на вывод"""
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    c.execute("UPDATE withdrawal_requests SET status = ? WHERE id = ?", (status, request_id))
    conn.commit()
    conn.close()



# ================== КОМАНДА: МОИ ЗВЁЗДЫ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мои звёзды", "звёзды", "мои звезды"])
def my_stars_command(message):
    """Показывает статистику звёзд пользователя"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'
    
    # Проверяем, включён ли ивент
    if not STAR_ENABLED:
        bot.reply_to(
            message,
            f"⛔ <b>Заработок звёзд уже был выключен, скоро будет снова включён</b>",
            parse_mode="HTML"
        )
        return
    
    # Получаем статистику пользователя
    stats = get_user_star_stats(user_id)
    
    # Формируем текст
    text = (
        f"📄 <b>Статистика твоих смс в нашем чате</b>\n"
        f"(Считаются только текстовые сообщения!):\n\n"
        f"💬 Написано всего смс: <code>{stats['total_messages']}</code>\n"
        f"⭐ Накоплено звёзд: <code>{stats['total_stars']:.2f}</code>\n\n"
        f"⛔ <b>Звёзды можно вывести минимум от 50! После подачи заявки на вывод, "
        f"он обрабатывается до 24 часов (обычно 0-3 часа, уведомление о выводе звёзд "
        f"придёт вам в личку с ботом)</b>"
    )
    
    # Создаём кнопку
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💸 Вывести звёзды", callback_data=f"withdraw_stars_{user_id}"))
    
    bot.reply_to(message, text, parse_mode="HTML", reply_markup=kb)

# ================== ОБРАБОТЧИК КНОПКИ ВЫВОДА ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("withdraw_stars_"))
def withdraw_stars_callback(call):
    """Обрабатывает нажатие на кнопку вывода звёзд"""
    try:
        owner_id = int(call.data.split("_")[2])
        
        # ЗАЩИТА: проверяем, что нажимает владелец кнопки
        if call.from_user.id != owner_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        user_id = call.from_user.id
        
        # Проверяем, включён ли ивент
        if not STAR_ENABLED:
            bot.answer_callback_query(
                call.id,
                "⛔ Заработок звёзд временно отключён!",
                show_alert=True
            )
            return
        
        # Получаем статистику пользователя
        stats = get_user_star_stats(user_id)
        
        # Проверяем минимальную сумму
        if stats['total_stars'] < MIN_WITHDRAWAL:
            bot.answer_callback_query(
                call.id,
                f"❌ К сожалению у вас меньше {MIN_WITHDRAWAL} звёзд, вывод только от {MIN_WITHDRAWAL} ⭐.",
                show_alert=True
            )
            return
        
        # Списываем звёзды
        amount_to_withdraw = stats['total_stars']  # Выводим все звёзды
        if not deduct_stars(user_id, amount_to_withdraw):
            bot.answer_callback_query(call.id, "❌ Ошибка при списании звёзд!", show_alert=True)
            return
        
        # Создаём заявку на вывод
        username = f"@{call.from_user.username}" if call.from_user.username else "Нет username"
        request_id = create_withdrawal_request(user_id, username, amount_to_withdraw)
        
        # Уведомляем пользователя
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        bot.edit_message_text(
            f"{mention}, <b>вы успешно поставили свои звёзды на вывод, "
            f"заказ обрабатывается обычно в течение 0-3 часов (может до 24 часов!)</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        # Отправляем уведомление админу
        admin_text = (
            f"📤 <b>НОВАЯ ЗАЯВКА НА ВЫВОД ЗВЁЗД</b>\n\n"
            f"👤 Пользователь: {mention}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📱 Username: {username}\n"
            f"⭐ Количество: <code>{amount_to_withdraw:.2f}</code>\n"
            f"🆔 Заявка #{request_id}\n\n"
            f"Выберите действие:"
        )
        
        admin_kb = InlineKeyboardMarkup(row_width=2)
        admin_kb.add(
            InlineKeyboardButton("✅ Успешно", callback_data=f"approve_withdraw_{request_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"reject_withdraw_{request_id}")
        )
        
        bot.send_message(ADMIN_ID_FOR_STARS, admin_text, parse_mode="HTML", reply_markup=admin_kb)
        
        bot.answer_callback_query(call.id, "✅ Заявка отправлена!")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике вывода звёзд: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
        
        # ================== ОБРАБОТЧИКИ ДЛЯ АДМИНА (ПОДТВЕРЖДЕНИЕ ВЫВОДА) ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_withdraw_"))
def approve_withdrawal(call):
    """Админ подтверждает вывод звёзд"""
    try:
        # Проверяем, что это админ
        if call.from_user.id != ADMIN_ID_FOR_STARS:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        request_id = int(call.data.split("_")[2])
        
        # Получаем информацию о заявке
        conn = sqlite3.connect(STAR_DB)
        c = conn.cursor()
        c.execute("SELECT user_id, username, amount FROM withdrawal_requests WHERE id = ? AND status = 'pending'", 
                 (request_id,))
        request = c.fetchone()
        conn.close()
        
        if not request:
            bot.answer_callback_query(call.id, "❌ Заявка не найдена или уже обработана!", show_alert=True)
            return
        
        user_id, username, amount = request
        
        # Обновляем статус заявки
        update_withdrawal_status(request_id, 'approved')
        
        # Уведомляем пользователя
        try:
            user = bot.get_chat(user_id)
            user_mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
            
            # Определяем username для отправки
            send_username = f"@{user.username}" if user.username else "отсутствует"
            
            bot.send_message(
                user_id,
                f"⭐ <b>Ваш заказ обработан, звёзды отправлены на ваш username {send_username}.</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")
        
        # Обновляем сообщение админа
        bot.edit_message_text(
            f"✅ Заявка #{request_id} одобрена!\n\n"
            f"Пользователь уведомлён.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, "✅ Одобрено!")
        
    except Exception as e:
        logger.error(f"Ошибка при одобрении вывода: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_withdraw_"))
def reject_withdrawal(call):
    """Админ отклоняет вывод звёзд"""
    try:
        # Проверяем, что это админ
        if call.from_user.id != ADMIN_ID_FOR_STARS:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        request_id = int(call.data.split("_")[2])
        
        # Получаем информацию о заявке
        conn = sqlite3.connect(STAR_DB)
        c = conn.cursor()
        c.execute("SELECT user_id, username, amount FROM withdrawal_requests WHERE id = ? AND status = 'pending'", 
                 (request_id,))
        request = c.fetchone()
        conn.close()
        
        if not request:
            bot.answer_callback_query(call.id, "❌ Заявка не найдена или уже обработана!", show_alert=True)
            return
        
        user_id, username, amount = request
        
        # Возвращаем звёзды пользователю
        conn = sqlite3.connect(STAR_DB)
        c = conn.cursor()
        c.execute("UPDATE star_users SET total_stars = total_stars + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        
        # Обновляем статус заявки
        update_withdrawal_status(request_id, 'rejected')
        
        # Уведомляем пользователя
        try:
            bot.send_message(
                user_id,
                f"⛔ <b>Ваш заказ был отклонен, причинами могут быть:</b>\n"
                f"1. У вас нет username\n"
                f"2. Заказ был отклонен по другой причине - пишите в лс @parvizwp.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")
        
        # Обновляем сообщение админа
        bot.edit_message_text(
            f"❌ Заявка #{request_id} отклонена!\n\n"
            f"Пользователь уведомлён.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, "❌ Отклонено")
        
    except Exception as e:
        logger.error(f"Ошибка при отклонении вывода: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== АДМИН КОМАНДА: ЗАКИНУТЬ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("закинуть"))
def admin_add_stars(message):
    """Админ начисляет звёзды пользователю (ответом на сообщение)"""
    user_id = message.from_user.id
    
    # Проверяем, что это админ
    if user_id != ADMIN_ID_FOR_STARS:
        # Игнорируем обычных пользователей
        return
    
    # Проверяем, что команда отправлена в ответ на сообщение
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которому хотите начислить звёзды!")
        return
    
    target_user = message.reply_to_message.from_user
    target_id = target_user.id
    
    # Парсим количество звёзд
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: закинуть [количество] (ответом на сообщение)")
            return
        
        amount = float(parts[1])
        if amount <= 0:
            bot.reply_to(message, "❌ Количество должно быть больше 0!")
            return
        
        if amount > 1000:
            bot.reply_to(message, "❌ Максимальная сумма за раз: 1000 звёзд!")
            return
        
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат! Укажите число (можно с точкой, например: 5.5)")
        return
    
    # Начисляем звёзды
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    c.execute("SELECT total_messages, total_stars FROM star_users WHERE user_id = ?", (target_id,))
    result = c.fetchone()
    
    if result:
        total_stars = result[1] + amount
        c.execute("UPDATE star_users SET total_stars = ? WHERE user_id = ?", (total_stars, target_id))
    else:
        c.execute("INSERT INTO star_users (user_id, total_messages, total_stars) VALUES (?, ?, ?)",
                 (target_id, 0, amount))
    
    conn.commit()
    conn.close()
    
    # Отправляем подтверждение
    admin_mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    target_mention = f'<a href="tg://user?id={target_id}">{target_user.first_name}</a>'
    
    bot.reply_to(
        message,
        f"✅ {admin_mention} начислил {target_mention}\n"
        f"⭐ <b>{amount}</b> звёзд!",
        parse_mode="HTML"
    )
    
    # Уведомляем пользователя
    try:
        bot.send_message(
            target_id,
            f"🎁 Вам начислено <b>{amount} ⭐</b>!\n"
            f"Проверить баланс: <code>мои звёзды</code>",
            parse_mode="HTML"
        )
    except:
        pass
    
    logger.info(f"Админ {user_id} начислил {amount} звёзд пользователю {target_id}")

# ================== АДМИН КОМАНДА: /off ==================
@bot.message_handler(commands=['off'])
def turn_off_stars(message):
    """Отключает ивент со звёздами"""
    global STAR_ENABLED
    
    user_id = message.from_user.id
    
    # Проверяем, что это админ
    if user_id != ADMIN_ID_FOR_STARS:
        # Игнорируем обычных пользователей
        return
    
    STAR_ENABLED = False
    bot.reply_to(
        message,
        f"✅ <b>Ивент со звёздами ОТКЛЮЧЁН!</b>\n"
        f"Теперь команда <code>мои звёзды</code> будет показывать сообщение об отключении.",
        parse_mode="HTML"
    )
    logger.info(f"Админ {user_id} отключил ивент со звёздами")

# ================== АДМИН КОМАНДА: /on ==================
@bot.message_handler(commands=['on'])
def turn_on_stars(message):
    """Включает ивент со звёздами"""
    global STAR_ENABLED
    
    user_id = message.from_user.id
    
    # Проверяем, что это админ
    if user_id != ADMIN_ID_FOR_STARS:
        # Игнорируем обычных пользователей
        return
    
    STAR_ENABLED = True
    bot.reply_to(
        message,
        f"✅ <b>Ивент со звёздами ВКЛЮЧЁН!</b>\n"
        f"Теперь сообщения снова начисляют звёзды.",
        parse_mode="HTML"
    )
    logger.info(f"Админ {user_id} включил ивент со звёздами")

# ================== АДМИН КОМАНДА: СТАТИСТИКА ЗВЁЗД ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "статистика звёзд")
def star_stats_admin(message):
    """Показывает статистику по звёздам (только для админа)"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID_FOR_STARS:
        return
    
    conn = sqlite3.connect(STAR_DB)
    c = conn.cursor()
    
    # Общая статистика
    c.execute("SELECT COUNT(*), SUM(total_messages), SUM(total_stars) FROM star_users")
    total_users, total_msgs, total_stars = c.fetchone()
    
    # Количество ожидающих заявок
    c.execute("SELECT COUNT(*) FROM withdrawal_requests WHERE status = 'pending'")
    pending_requests = c.fetchone()[0]
    
    # Топ-5 пользователей по звёздам
    c.execute("SELECT user_id, total_stars FROM star_users ORDER BY total_stars DESC LIMIT 5")
    top_users = c.fetchall()
    
    conn.close()
    
    text = (
        f"📊 <b>СТАТИСТИКА ЗВЁЗД</b>\n\n"
        f"👥 Всего участников: <code>{total_users or 0}</code>\n"
        f"💬 Всего сообщений: <code>{total_msgs or 0}</code>\n"
        f"⭐ Всего начислено звёзд: <code>{total_stars or 0:.2f}</code>\n"
        f"⏳ Ожидающих заявок: <code>{pending_requests}</code>\n\n"
        f"🏆 <b>Топ-5 по звёздам:</b>\n"
    )
    
    for i, (uid, stars) in enumerate(top_users, 1):
        try:
            user = bot.get_chat(uid)
            name = user.first_name
        except:
            name = f"User {uid}"
        
        text += f"{i}. <a href='tg://user?id={uid}'>{name}</a> — {stars:.2f}⭐\n"
    
    bot.send_message(message.chat.id, text, parse_mode="HTML")
    # ================== ПОДСЧЁТ СООБЩЕНИЙ БЕЗ БЛОКИРОВКИ КОМАНД ==================

@bot.message_handler(
    func=lambda m: (
        m.chat.id == STAR_CHAT_ID
        and m.text
        and not m.text.startswith("/")
        and not m.from_user.is_bot
    )
)
def count_messages_silent(message):
    """
    Считает текстовые сообщения в указанном чате.
    Не мешает работе других команд.
    """
    try:
        # Считаем сообщение
        total_msgs, total_stars = update_user_star_stats(message.from_user.id)

        # Редкий лог
        if total_msgs % 50 == 0:
            logger.info(
                f"⭐ Статистика: {message.from_user.id} | Сообщений: {total_msgs} | Звёзд: {total_stars:.2f}"
            )

    except Exception as e:
        logger.debug(f"Ошибка подсчёта сообщений: {e}")
# ================== ЗАПУСК БОТА ==================
if __name__ == "__main__":
    logger.info("Бот Iris запущен!")
    bot.infinity_polling()