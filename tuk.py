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
TOKEN = "8293824305:AAHgjsDcya_IX4jR0y0IIPY4b9wDlbhWSAQ"
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
    "обнять": "🫂 {user1} крепко обнял(а) {user2}",
    "поцеловать": "💋 {user1} страстно поцеловал(а) {user2}",
    "погладить": "✨ {user1} нежно погладил(а) {user2}",
    
    # Весёлые взаимодействия
    "пощекотать": "🪶 {user1} задорно пощекотал(а) {user2}",
    
    # Подарки
    "подарить": "🎁 {user1} сделал(а) подарок {user2}",
    
    # Агрессивные действия
    "ударить": "👊 {user1} ударил(а) {user2}",
    "шлёпнуть": "🖐️ {user1} шлёпнул(а) {user2}",
    "избить": "🥊 {user1} избил(а) {user2}",
    
    # Воровство
    "украсть": "🥷 {user1} украл(а) что-то у {user2}",
    
    # 18+ действия
    "выебать": "🍆 {user1} жестко выебал(а) {user2}",
    "трахнуть": "🔥 {user1} страстно трахнул(а) {user2}",
    "отсосать": "👅 {user1} жадно отсосал(а) у {user2}",
    "отлизать": "💦 {user1} умело отлизал(а) {user2}"
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
            f"├ Стоимость: <code>{format_number(price)}$</code>\n"
            f"├ Бонус: <b>+{bonus_percent}%</b> к доходам\n"
            f"└ Доход: <b>{format_number(info['income'])}$</b>/3ч\n\n"
        )

    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"👤 <b>Твой баланс:</b> <code>{format_number(user_data['balance'])}$</code>\n"
    
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
                f"💳 Нужно: <code>{format_number(price)}$</code>\n"
                f"💰 На балансе: <code>{format_number(user_data['balance'])}$</code>\n\n"
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
            f"💎 {mention} ты продал свой VIP-статус {vip_info['prefix']} {vip_info['name']} за <code>{format_number(sell_price)}$</code>\n\n"
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
                f"├ Стоимость: <code>{format_number(price)}$</code>\n"
                f"├ Бонус: <b>+{bonus_percent}%</b> к доходам\n"
                f"└ Доход: <b>{format_number(info['income'])}$</b>/3ч\n\n"
            )

        text += "━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"👤 <b>Твой баланс:</b> <code>{format_number(user_data['balance'])}$</code>\n"
        
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

# ================== СПИСОК RP КОМАНД В ОДНОМ СООБЩЕНИИ ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "рп")
def rp_list(message):
    text = "🎭 <b>СПИСОК RP-КОМАНД</b> 🎭\n\n"
    
    for cmd, action in RP_COMMANDS.items():
        # Убираем эмодзи и скобки, оставляем только текст действия
        action_text = action.split(' ', 1)[1] if ' ' in action else action
        text += f"<code>{cmd}</code>\n"
    
    text += "\n💫 <i>Используй команды в ответ на сообщение пользователя!</i>"
    
    bot.send_message(message.chat.id, text, parse_mode='HTML')
    
 
        
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
        f"🧾 <b>Чек на {amount} валюты </b>\n"
        f"🪪 Активаций: <b>{max_acts}</b>\n"
        f"💎 Награда: <b>{amount} валюты</b>\n\n"
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
        f"Ты активировал чек и получил <b>{cheque['amount']} на свой баланс!</b>",
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
        f"🧾 <b>Чек на {amount}</b>\n"
        f"🪪 Активаций: <b>{max_acts}</b>\n"
        f"💎 Награда: <b>{amount}</b>\n\n"
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
            f"💰 На твой счёт начислено <b>{format_number(REFERRAL_BONUS)}$</b>\n"
            f"💵 Баланс: {format_number(get_user_data(referrer_id)['balance'])}$\n\n"
            f"👥 Всего рефералов: {len(get_user_referral_data(referrer_id)['referrals'])}",
            parse_mode="HTML"
        )

        bot.send_message(
            new_user_id,
            f"👋 Добро пожаловать!\n\n"
            f"Ты перешёл по ссылке от {referrer_mention}!\n"
            f"🎁 Ему начислено <b>{format_number(REFERRAL_BONUS)}$</b> 🎉",
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
        f"Если хочешь добавить меня в свой чат, <a href='{add_to_group_url}'>сюда</a> "
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
        f"💌 За друга: <b>{format_number(REFERRAL_BONUS)}$</b>\n"
        f"👥 Приглашено: <b>{referrals_count}</b>\n"
        f"💰 Заработано: <b>{format_number(total_earned)}$</b>"
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
        f"💰 За друга: <b>{format_number(REFERRAL_BONUS)}$</b>\n"
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
        text += f"\n💰 Всего заработано: <b>{format_number(len(referrals)*REFERRAL_BONUS)}$</b>"

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
    
import requests
import logging
from telebot import TeleBot
from telebot.types import Message

# Настройка логирования
logging.basicConfig(
    filename='bot_logs.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ID подарков (Telegram Premium Gifts)
ALLOWED_GIFTS = [
    "5170145012310081615",  # 🎁 Gift 1
    "5170250947678437525",  # 🎁 Gift 2
    "5170564780938756245",  # 🎁 Gift 3
    "5170521118301225164"   # 🎁 Gift 4
]

@bot.message_handler(commands=['wp'])
def send_custom_gift(message: Message):
    """
    Отправляет подарок указанному пользователю.
    Форматы использования:
    1. /wp - отправить подарок себе
    2. /wp @username - отправить подарок пользователю по username
    3. /wp 123456789 - отправить подарок пользователю по ID
    4. Ответить на сообщение с командой /wp - отправить подарок тому, кому ответили
    """
    try:
        # Разбираем команду
        args = message.text.split()
        target_user_id = message.from_user.id
        target_name = "тебе"
        
        # Определяем цель отправки
        if message.reply_to_message:
            # Если ответ на сообщение - отправляем тому, кому ответили
            target_user_id = message.reply_to_message.from_user.id
            target_name = f"пользователю {message.reply_to_message.from_user.first_name}"
        elif len(args) > 1:
            arg = args[1]
            
            if arg.startswith('@'):
                # Поиск по username
                try:
                    user = bot.get_chat(arg)
                    target_user_id = user.id
                    target_name = f"пользователю @{arg[1:]}"
                except:
                    bot.reply_to(message, "❌ Пользователь не найден!")
                    return
            else:
                # По ID
                try:
                    target_user_id = int(arg)
                    # Получаем информацию о пользователе
                    try:
                        target_user = bot.get_chat(target_user_id)
                        target_name = f"пользователю {target_user.first_name}"
                    except:
                        target_name = f"пользователю с ID {target_user_id}"
                except ValueError:
                    bot.reply_to(message, "❌ Неверный формат! Используйте ID или @username")
                    return
        
        # Проверяем, не пытаются ли отправить подарок боту
        try:
            target_user = bot.get_chat(target_user_id)
            if target_user.is_bot:
                bot.reply_to(message, "❌ Нельзя отправить подарок боту!")
                return
        except:
            pass
        
        # Выбираем первый доступный подарок из списка
        gift_id = ALLOWED_GIFTS[0]
        
        params = {
            "chat_id": message.chat.id,
            "user_id": target_user_id,
            "gift_id": gift_id,
            "text": "🎁 Подарок от Meow Game | by Parviz"
        }
        
        # Отправляем запрос к Telegram API
        response = requests.post(
            f"https://api.telegram.org/bot{bot.token}/sendGift",
            json=params,
            timeout=10
        )
        
        # Проверяем ответ
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('ok'):
            if target_user_id == message.from_user.id:
                reply_text = "🎉 Подарок успешно отправлен тебе!"
            else:
                reply_text = f"🎉 Подарок успешно отправлен {target_name}!"
            
            bot.reply_to(message, reply_text)
            logging.info(f"Успешная отправка подарка {gift_id} пользователю {target_user_id}")
            return
        
        # Обработка ошибок от Telegram API
        error_code = response_data.get('error_code')
        error_message = response_data.get('description', 'Неизвестная ошибка')
        
        # Кастомные сообщения для разных ошибок
        if error_code == 400:
            if "gift not available" in error_message.lower():
                bot.reply_to(message, "❌ Этот подарок недоступен в данном регионе")
            elif "user not found" in error_message.lower():
                bot.reply_to(message, "❌ Пользователь не найден")
            else:
                bot.reply_to(message, f"❌ Ошибка запроса: {error_message}")
        
        elif error_code == 403:
            bot.reply_to(message, "❌ У бота недостаточно прав для отправки подарков")
        
        elif error_code == 429:
            bot.reply_to(message, "⏳ Слишком много запросов. Попробуйте позже")
        
        else:
            bot.reply_to(message, f"❌ Ошибка при отправке подарка: {error_message}")
        
        logging.error(f"Ошибка отправки подарка {gift_id}: {response_data}")
        
    except requests.exceptions.Timeout:
        logging.error(f"Таймаут при отправке подарка")
        bot.reply_to(message, "⏳ Время ожидания истекло. Попробуйте позже.")
        
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Сетевая ошибка: {req_err}")
        bot.reply_to(message, "❌ Произошла сетевая ошибка. Проверьте подключение к интернету.")
        
    except Exception as e:
        logging.exception(f"Критическая ошибка в send_custom_gift: {str(e)}")
        bot.reply_to(message, "❌ Произошла внутренняя ошибка бота.")

def handle_exception(bot, error):
    """Глобальный обработчик исключений бота"""
    logging.critical(f"Критическая ошибка в боте: {str(error)}")
    # Можно добавить уведомление администраторам о критической ошибке

# Подключаем обработчик ошибок
bot.error_handler = handle_exception

    
    
    # ================== АДМИН-КОМАНДЫ ДЛЯ ГРУПП (УЛУЧШЕНО) ==================

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

    parts = message.text.split()
    if len(parts) >= 2:
        try:
            return bot.get_chat(int(parts[1]))
        except:
            return None
    return None


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
        bot.reply_to(message, "❌ <b>Бот не администратор</b>", parse_mode="HTML")
        return

    target = get_target_user(message)
    if not target:
        bot.reply_to(message, "❌ <b>Ответь на сообщение или укажи ID</b>", parse_mode="HTML")
        return

    if is_chat_admin(chat_id, target.id):
        bot.reply_to(message, "❌ <b>Нельзя мутить администратора</b>", parse_mode="HTML")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(
            message,
            "❌ <b>Использование:</b>\n<code>мут 60 Спам</code>",
            parse_mode="HTML"
        )
        return

    try:
        minutes = int(args[1])
    except:
        bot.reply_to(message, "❌ <b>Время должно быть числом</b>", parse_mode="HTML")
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
        f"🔇 <b>МУТ</b>\n\n"
        f"👮 <b>Админ:</b> {mention(admin)}\n"
        f"👤 <b>Пользователь:</b> {mention(target)}\n"
        f"⏰ <b>Время:</b> <code>{minutes} мин</code>\n"
        f"📝 <b>Причина:</b> <code>{reason}</code>",
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
        bot.reply_to(message, "❌ <b>Укажи пользователя</b>", parse_mode="HTML")
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
        f"🔊 <b>МУТ СНЯТ</b>\n\n"
        f"👮 {mention(admin)}\n"
        f"👤 {mention(target)}",
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
        bot.reply_to(message, "❌ <b>Укажи пользователя</b>", parse_mode="HTML")
        return

    if is_chat_admin(chat_id, target.id):
        bot.reply_to(message, "❌ <b>Нельзя кикнуть администратора</b>", parse_mode="HTML")
        return

    bot.ban_chat_member(chat_id, target.id)
    bot.unban_chat_member(chat_id, target.id)

    bot.reply_to(
        message,
        f"👢 <b>КИК</b>\n\n"
        f"👮 {mention(admin)}\n"
        f"👤 {mention(target)}",
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
        bot.reply_to(message, "❌ <b>Укажи пользователя</b>", parse_mode="HTML")
        return

    if is_chat_admin(chat_id, target.id):
        bot.reply_to(message, "❌ <b>Нельзя банить администратора</b>", parse_mode="HTML")
        return

    bot.ban_chat_member(chat_id, target.id)

    bot.reply_to(
        message,
        f"🚫 <b>БАН</b>\n\n"
        f"👮 {mention(admin)}\n"
        f"👤 {mention(target)}\n"
        f"📌 <code>Перманентно</code>",
        parse_mode="HTML"
    )


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
    
    # ================== НОВОГОДНИЙ КАЛЕНДАРЬ (ИВЕНТ) ==================
NEW_YEAR_DB = "new_year_calendar.db"

# Инициализация базы данных для календаря
def init_new_year_db():
    conn = sqlite3.connect(NEW_YEAR_DB)
    c = conn.cursor()
    
    # Таблица для отслеживания наград
    c.execute("""
        CREATE TABLE IF NOT EXISTS new_year_calendar (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            last_claimed_date TEXT,
            total_claimed INTEGER DEFAULT 0,
            prizes_won TEXT DEFAULT '[]'
        )
    """)
    
    conn.commit()
    conn.close()

init_new_year_db()

def get_user_new_year_data(user_id):
    """Получает данные пользователя о новогоднем календаре"""
    conn = sqlite3.connect(NEW_YEAR_DB)
    c = conn.cursor()
    
    c.execute("SELECT last_claimed_date, total_claimed, prizes_won FROM new_year_calendar WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if not result:
        # Создаем запись если нет
        today = date.today().isoformat()
        c.execute("INSERT INTO new_year_calendar (user_id, username, last_claimed_date, total_claimed, prizes_won) VALUES (?, ?, ?, ?, ?)",
                  (user_id, "", today, 0, "[]"))
        conn.commit()
        
        conn.close()
        return {
            "last_claimed_date": today,
            "total_claimed": 0,
            "prizes_won": []
        }
    
    last_claimed_date, total_claimed, prizes_won_json = result
    
    # Парсим JSON список призов
    try:
        prizes_won = json.loads(prizes_won_json) if prizes_won_json else []
    except:
        prizes_won = []
    
    conn.close()
    
    return {
        "last_claimed_date": last_claimed_date,
        "total_claimed": total_claimed,
        "prizes_won": prizes_won
    }

def update_user_new_year_data(user_id, username, prize_info):
    """Обновляет данные пользователя после получения подарка"""
    conn = sqlite3.connect(NEW_YEAR_DB)
    c = conn.cursor()
    
    today = date.today().isoformat()
    
    # Получаем текущие данные
    c.execute("SELECT prizes_won FROM new_year_calendar WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result:
        try:
            prizes_won = json.loads(result[0]) if result[0] else []
        except:
            prizes_won = []
        
        # Добавляем новый приз
        prizes_won.append({
            "date": today,
            "prize": prize_info
        })
        
        # Обновляем запись
        c.execute("""
            UPDATE new_year_calendar 
            SET username = ?, last_claimed_date = ?, total_claimed = total_claimed + 1, prizes_won = ?
            WHERE user_id = ?
        """, (username, today, json.dumps(prizes_won), user_id))
    else:
        # Создаем новую запись
        prizes_won = [{"date": today, "prize": prize_info}]
        c.execute("""
            INSERT INTO new_year_calendar (user_id, username, last_claimed_date, total_claimed, prizes_won)
            VALUES (?, ?, ?, 1, ?)
        """, (user_id, username, today, json.dumps(prizes_won)))
    
    conn.commit()
    conn.close()

def can_claim_daily_gift(user_id):
    """Проверяет, может ли пользователь получить ежедневный подарок"""
    data = get_user_new_year_data(user_id)
    today = date.today().isoformat()
    return data["last_claimed_date"] != today

def get_random_prize(user_id):
    """Выбирает случайный подарок с учетом того, что уже есть у пользователя"""
    user_data = get_user_data(user_id)
    
    # Проверяем, что есть у пользователя
    has_vip = user_data.get("vip", {}).get("level", 0) > 0
    has_pet = get_pet(user_id) is not None
    has_car = user_data.get("car") is not None
    
    # Определяем доступные типы подарков
    available_prizes = []
    
    # Деньги - всегда доступны
    money_prizes = [
        {"type": "money", "amount": random.randint(1000, 5000), "emoji": "💰", "name": "Новогодний бонус"},
        {"type": "money", "amount": random.randint(5000, 15000), "emoji": "💰", "name": "Зимний куш"},
        {"type": "money", "amount": random.randint(15000, 30000), "emoji": "💎", "name": "Снежный джекпот"},
        {"type": "money", "amount": random.randint(50000, 100000), "emoji": "🎁", "name": "Подарок Деда Мороза"},
    ]
    available_prizes.extend(money_prizes)
    
    # Питомцы - если нет питомца
    if not has_pet:
        for pet_id, pet_info in PETS_DATA.items():
            available_prizes.append({
                "type": "pet",
                "pet_id": pet_id,
                "name": pet_info["name"],
                "price": pet_info["price"],
                "emoji": "🐾",
                "rarity": PET_RARITY[pet_info["rarity"]]["emoji"]
            })
    
    # Випы - если нет VIP
    if not has_vip:
        for level in range(1, 4):  # VIP 1-3 уровня
            vip_info = VIP_LEVELS[level]
            available_prizes.append({
                "type": "vip",
                "level": level,
                "name": vip_info["name"],
                "prefix": vip_info["prefix"],
                "days": random.randint(3, 7),
                "emoji": vip_info["prefix"]
            })
    
    # Машины - если нет машины
    if not has_car:
        for car_name, car_info in CAR_DATA.items():
            available_prizes.append({
                "type": "car",
                "name": car_name,
                "price": car_info["price"],
                "profit": car_info["profit_per_hour"],
                "emoji": "🚗"
            })
    
    # Префиксы - всегда доступны (если у пользователя нет префикса или можно заменить)
    user_prefix = get_user_prefix(user_id)
    if not user_prefix:
        prefix_prizes = [
            {"type": "prefix", "prefix_id": 1, "name": "🔰 Новичок", "price": 500000, "emoji": "🔰"},
            {"type": "prefix", "prefix_id": 2, "name": "🔥 Огонь", "price": 1000000, "emoji": "🔥"},
            {"type": "prefix", "prefix_id": 3, "name": "🎅 Дед Мороз", "price": 750000, "emoji": "🎅"},
            {"type": "prefix", "prefix_id": 4, "name": "⛄ Снеговик", "price": 600000, "emoji": "⛄"},
        ]
        available_prizes.extend(prefix_prizes)
    
    # Выбираем случайный подарок
    if available_prizes:
        return random.choice(available_prizes)
    else:
        # Если все типы подарков уже есть, даем деньги
        return {
            "type": "money",
            "amount": random.randint(50000, 150000),
            "emoji": "🎁",
            "name": "Особый новогодний бонус"
        }

def give_prize_to_user(user_id, prize):
    """Выдает подарок пользователю"""
    user_data = get_user_data(user_id)
    
    if prize["type"] == "money":
        amount = prize["amount"]
        user_data["balance"] += amount
        return f"{prize['emoji']} <b>{prize['name']}</b> — <code>{format_number(amount)}$</code>"
    
    elif prize["type"] == "pet":
        pet_info = PETS_DATA.get(prize["pet_id"])
        if pet_info:
            # Проверяем, нет ли уже питомца
            if get_pet(user_id):
                # Если есть питомец, продаем текущего и покупаем нового
                current_pet = get_pet(user_id)
                refund = current_pet[2] // 2  # 50% стоимости
                user_data["balance"] += refund
                delete_pet(user_id)
            
            # Создаем нового питомца
            set_pet(user_id, prize["pet_id"], pet_info["name"], pet_info["price"])
            rarity_info = PET_RARITY[pet_info["rarity"]]
            return f"{prize['emoji']} <b>{pet_info['name']}</b> {rarity_info['emoji']} — Новый питомец!"
    
    elif prize["type"] == "vip":
        vip_level = prize["level"]
        vip_info = VIP_LEVELS[vip_level]
        
        # Выдаем VIP
        user_data["vip"] = {
            "level": vip_level,
            "expires": (datetime.now() + timedelta(days=prize["days"])).isoformat(),
            "purchase_price": vip_level * 250000,
            "last_income": datetime.now().isoformat()
        }
        
        # Устанавливаем таймер для дохода
        vip_income_timers[user_id] = time.time()
        
        return f"{prize['emoji']} <b>VIP {vip_info['name']}</b> — на {prize['days']} дней!"
    
    elif prize["type"] == "car":
        car_name = prize["name"]
        car_info = CAR_DATA.get(car_name)
        
        if car_info:
            # Если уже есть машина, продаем старую
            if user_data.get("car"):
                old_car = user_data["car"]
                refund = old_car.get("price", 0) // 2
                user_data["balance"] += refund
            
            # Даем новую машину
            user_data["car"] = {
                "name": car_name,
                "price": car_info["price"],
                "profit_per_hour": car_info["profit_per_hour"],
                "image": car_info["image"],
                "upkeep_cost": car_info["upkeep_cost"]
            }
            return f"{prize['emoji']} <b>{car_name}</b> — Новый автомобиль!"
    
    elif prize["type"] == "prefix":
        # Устанавливаем префикс
        prefix_data = {
            1: {"id": 1, "name": "🔰 Новичок", "price": 500000},
            2: {"id": 2, "name": "🔥 Огонь", "price": 1000000},
            3: {"id": 3, "name": "🎅 Дед Мороз", "price": 750000},
            4: {"id": 4, "name": "⛄ Снеговик", "price": 600000},
        }
        
        prefix_info = prefix_data.get(prize["prefix_id"])
        if prefix_info:
            # Если есть префикс, продаем старый
            current_prefix = get_user_prefix(user_id)
            if current_prefix:
                refund = current_prefix["price_paid"] // 4
                user_data["balance"] += refund
            
            # Устанавливаем новый
            set_user_prefix(user_id, prefix_info["id"], prefix_info["price"])
            return f"{prize['emoji']} <b>{prefix_info['name']}</b> — Новый префикс!"
    
    save_casino_data()
    return f"{prize['emoji']} <b>{prize.get('name', 'Подарок')}</b>"

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["новогодний калдсжвжчдсарь", "кжвдсдвжрь", "фэажсдсьчдысдсж", "нжвжсжвжвж", "нйхвббфжсьжыжад"])
def new_year_calendar(message):
    """Показывает новогодний календарь"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    # Получаем данные о календаре
    calendar_data = get_user_new_year_data(user_id)
    today = date.today().isoformat()
    can_claim = calendar_data["last_claimed_date"] != today
    
    # Красивый новогодний дизайн
    calendar_image = "https://img.freepik.com/premium-photo/christmas-gift-box-bauble-isolated-white-background_146936-1271.jpg?semt=ais_hybrid&w=740"  # Новогодняя тематика
    
    # Формируем текст
    if can_claim:
        status_text = "🎁 <b>Подарок готов к получению!</b>"
        button_text = "☃️ Получить подарок"
        button_callback = f"new_year_claim_{user_id}"
    else:
        # Рассчитываем время до следующего подарка
        last_date = datetime.fromisoformat(calendar_data["last_claimed_date"])
        next_date = last_date + timedelta(days=1)
        now = datetime.now()
        
        if now < next_date:
            time_left = next_date - now
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            
            status_text = f"⏳ <b>Следующий подарок через:</b> {hours}ч {minutes}м"
            button_text = "❄️ Уже получено сегодня"
            button_callback = "new_year_already_claimed"
        else:
            status_text = "🎁 <b>Подарок готов к получению!</b>"
            button_text = "☃️ Получить подарок"
            button_callback = f"new_year_claim_{user_id}"
    
    text = (
        f"🎄✨ <b>НОВОГОДНИЙ КАЛЕНДАРЬ 2026</b> ✨🎄\n\n"
        f"🎅 Добро пожаловать в зимнюю сказку, {mention}!\n\n"
        f"{status_text}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего получено подарков: <b>{calendar_data['total_claimed']}</b>\n"
        f"• Последний подарок: <b>{'Сегодня' if calendar_data['last_claimed_date'] == today else 'Вчера' if calendar_data['last_claimed_date'] == (date.today() - timedelta(days=1)).isoformat() else 'Ранее'}</b>\n\n"
        f"🎁 <b>Возможные подарки: может выпасть все что угодно</b>\n"
    )
    
    # Создаем клавиатуру
    kb = InlineKeyboardMarkup()
    
    if can_claim or button_callback.startswith("new_year_claim"):
        kb.add(InlineKeyboardButton(button_text, callback_data=button_callback))
    else:
        kb.add(InlineKeyboardButton(button_text, callback_data="no_action"))
    
    kb.add(
        InlineKeyboardButton("📜 Мои подарки", callback_data=f"new_year_prizes_{user_id}"))
    
    # Отправляем сообщение с картинкой
    try:
        bot.send_photo(
            message.chat.id,
            calendar_image,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        # Если картинка не загружается, отправляем просто текст
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=kb
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith("new_year_claim_"))
def claim_new_year_gift(call):
    """Обработка получения подарка"""
    try:
        user_id = int(call.data.split("_")[3])
        
        # Проверяем, что нажимает владелец
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "🎅 Это не твой календарь!", show_alert=True)
            return
        
        # Проверяем, можно ли получить подарок
        if not can_claim_daily_gift(user_id):
            bot.answer_callback_query(call.id, "❄️ Ты уже получал подарок сегодня!", show_alert=True)
            return
        
        # Получаем случайный подарок
        prize = get_random_prize(user_id)
        username = call.from_user.username or call.from_user.first_name
        
        # Выдаем подарок
        prize_description = give_prize_to_user(user_id, prize)
        
        # Обновляем данные в календаре
        update_user_new_year_data(user_id, username, prize)
        
        # Формируем красивый ответ
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        # Создаем красивую анимацию с задержкой
        bot.answer_callback_query(call.id, "🎄 Ищем подарок...")
        time.sleep(1)
        
        # Первое обновление
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"🎄✨ {mention}, Дед Мороз ищет для тебя подарок... ⛄",
            parse_mode="HTML",
            reply_markup=None
        )
        time.sleep(1)
        
        # Второе обновление
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=f"🎁✨ {mention}, заглядываем в мешок с подарками... 🎅",
            parse_mode="HTML",
            reply_markup=None
        )
        time.sleep(1)
        
        # Финальное сообщение с результатом
        final_text = (
            f"🎉✨ <b>НОВОГОДНИЙ СЮРПРИЗ!</b> ✨🎉\n\n"
            f"🎅 Дорогой {mention},\n"
            f"Дед Мороз приготовил для тебя особый подарок!\n\n"
            f"🎁 <b>Ты получил(а):</b>\n"
            f"{prize_description}\n\n"
            f"❄️ <i>Возвращайся завтра за новым подарком!</i>\n\n"
            f"📅 Всего получено подарков: <b>{get_user_new_year_data(user_id)['total_claimed']}</b>"
        )
        
        # Обновляем клавиатуру
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🎁 Ещё подарки завтра", callback_data=f"new_year_tomorrow_{user_id}"),
            InlineKeyboardButton("📜 Мои подарки", callback_data=f"new_year_prizes_{user_id}")
        )
        kb.add(InlineKeyboardButton("🎄 В календарь", callback_data=f"new_year_calendar_{user_id}"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=final_text,
            parse_mode="HTML",
            reply_markup=kb
        )
        
    except Exception as e:
        logger.error(f"Ошибка выдачи новогоднего подарка: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при получении подарка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("new_year_prizes_"))
def show_user_prizes(call):
    """Показывает историю полученных подарков"""
    try:
        user_id = int(call.data.split("_")[3])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "🎅 Это не твои подарки!", show_alert=True)
            return
        
        calendar_data = get_user_new_year_data(user_id)
        prizes = calendar_data["prizes_won"]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        if not prizes:
            text = (
                f"📜 <b>ИСТОРИЯ ПОДАРКОВ</b>\n\n"
                f"{mention}, ты ещё не получал подарков из новогоднего календаря.\n\n"
                f"🎁 Нажми на кнопку «Получить подарок» в календаре, чтобы получить свой первый подарок!"
            )
        else:
            # Показываем последние 10 подарков
            recent_prizes = prizes[-10:]  # Последние 10 подарков
            recent_prizes.reverse()  # Новые сверху
            
            text = f"📜 <b>ПОСЛЕДНИЕ ПОДАРКИ {mention}</b>\n\n"
            
            for i, prize_data in enumerate(recent_prizes, 1):
                prize_date = datetime.fromisoformat(prize_data["date"]).strftime("%d.%m.%Y")
                prize = prize_data["prize"]
                
                # Форматируем описание подарка
                if prize["type"] == "money":
                    prize_desc = f"💰 {prize['name']}: {format_number(prize['amount'])}$"
                elif prize["type"] == "pet":
                    prize_desc = f"🐾 Питомец: {prize['name']}"
                elif prize["type"] == "vip":
                    prize_desc = f"👑 VIP {prize['name']}: {prize['days']} дней"
                elif prize["type"] == "car":
                    prize_desc = f"🚗 Машина: {prize['name']}"
                elif prize["type"] == "prefix":
                    prize_desc = f"🔰 Префикс: {prize['name']}"
                else:
                    prize_desc = f"🎁 {prize.get('name', 'Подарок')}"
                
                text += f"{i}. <b>{prize_date}</b> — {prize_desc}\n"
            
            text += f"\n📊 Всего подарков: <b>{len(prizes)}</b>"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 В календарь", callback_data=f"new_year_calendar_{user_id}"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка показа подарков: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("new_year_calendar_"))
def back_to_calendar(call):
    """Возврат к календарю"""
    try:
        user_id = int(call.data.split("_")[3])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "🎅 Это не твой календарь!", show_alert=True)
            return
        
        # Создаем фейковое сообщение
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = from_user
        
        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        new_year_calendar(fake_msg)
        
        # Удаляем старое сообщение
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка возврата в календарь: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("new_year_tomorrow_"))
def tomorrow_gift(call):
    """Информация о подарке на завтра"""
    try:
        user_id = int(call.data.split("_")[3])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "🎅 Это не твой календарь!", show_alert=True)
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        # Случайный предсказатель подарка на завтра
        tomorrow_gifts = [
            "возможно, это будут горы золотых монет! 💰",
            "может быть, тебя ждёт роскошный автомобиль! 🚗",
            "вероятно, это будет милый питомец! 🐾",
            "скорее всего, это будет VIP-статус! 👑",
            "возможно, это будет особый новогодний префикс! 🔰",
            "может быть, это будет огромный денежный приз! 🎁",
            "вероятно, тебя ждёт сюрприз от Деда Мороза! 🎅"
        ]
        
        text = (
            f"🔮✨ <b>ПРЕДСКАЗАНИЕ НА ЗАВТРА</b> ✨🔮\n\n"
            f"❄️ Дорогой {mention},\n\n"
            f"Заглянув в магический шар, я вижу...\n\n"
            f"🎁 <b>Завтра тебя ждёт:</b>\n"
            f"<i>{random.choice(tomorrow_gifts)}</i>\n\n"
            f"🎄 Не забудь заглянуть в календарь завтра, чтобы узнать, сбудется ли предсказание!"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎄 В календарь", callback_data=f"new_year_calendar_{user_id}"))
        
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка предсказания: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "new_year_already_claimed")
def already_claimed_today(call):
    """Уведомление, что подарок уже получен"""
    bot.answer_callback_query(call.id, "❄️ Ты уже получал подарок сегодня! Возвращайся завтра! 🎄", show_alert=True)

print("✅ Новогодний календарь загружен и готов к работе! 🎄")


# ================== СИСТЕМА СБОРА МУСОРА С АВТО-СБОРОКОЙ ==================
TRASH_DB = "trash.db"
AUTO_TRASH_PRICE = 330000  # 240к за авто-сбор
AUTO_TRASH_TIME = 40 * 60  # 40 минут
AUTO_TRASH_USERS = {}

# Инициализация базы данных для мусора
def init_trash_db():
    conn = sqlite3.connect(TRASH_DB)
    c = conn.cursor()
    
    # Таблица для инвентаря пользователей
    c.execute("""
        CREATE TABLE IF NOT EXISTS trash_inventory (
            user_id INTEGER PRIMARY KEY,
            items TEXT DEFAULT '{}',
            last_collected_time REAL DEFAULT 0,
            auto_trash_ends REAL DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()

init_trash_db()

# Данные мусора (сниженные цены)
TRASH_ITEMS = {
    "🍂 Листья": {"price": 50, "emoji": "🍂"},
    "🥤 Бутылка": {"price": 120, "emoji": "🥤"},
    "📰 Бумага": {"price": 80, "emoji": "📰"},
    "🍌 Банан": {"price": 60, "emoji": "🍌"},
    "🚬 Окурок": {"price": 100, "emoji": "🚬"},
    "🧦 Носок": {"price": 120, "emoji": "🧦"},
    "🧴 Флакон": {"price": 250, "emoji": "🧴"},
    "🍕 Пицца": {"price": 90, "emoji": "🍕"},
    "🥫 Банка": {"price": 100, "emoji": "🥫"},
    "📱 Телефон": {"price": 1000, "emoji": "📱"},
    "🧩 Игрушка": {"price": 500, "emoji": "🧩"},
    "💄 Помада": {"price": 750, "emoji": "💄"},
    "🧢 Кепка": {"price": 250, "emoji": "🧢"},
    "🍬 Фантик": {"price": 60, "emoji": "🍬"},
    "💍 Кольцо": {"price": 7500, "emoji": "💍"}
}

def get_user_trash_inventory(user_id):
    """Получает инвентарь пользователя"""
    conn = sqlite3.connect(TRASH_DB)
    c = conn.cursor()
    
    c.execute("SELECT items, last_collected_time, auto_trash_ends FROM trash_inventory WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if not result:
        # Создаем запись если нет
        c.execute("INSERT INTO trash_inventory (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return {"items": {}, "last_collected_time": 0, "auto_trash_ends": 0}
    
    items_json, last_collected_time, auto_trash_ends = result
    
    try:
        items = json.loads(items_json) if items_json else {}
    except:
        items = {}
    
    conn.close()
    return {
        "items": items,
        "last_collected_time": last_collected_time,
        "auto_trash_ends": auto_trash_ends
    }

def update_user_trash_inventory(user_id, items=None, last_collected_time=None, auto_trash_ends=None):
    """Обновляет инвентарь пользователя"""
    conn = sqlite3.connect(TRASH_DB)
    c = conn.cursor()
    
    # Получаем текущие данные
    c.execute("SELECT items, last_collected_time, auto_trash_ends FROM trash_inventory WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if not result:
        current_items = {}
        current_last_time = 0
        current_auto_ends = 0
    else:
        items_json, current_last_time, current_auto_ends = result
        try:
            current_items = json.loads(items_json) if items_json else {}
        except:
            current_items = {}
    
    # Обновляем только переданные значения
    if items is not None:
        current_items = items
    if last_collected_time is not None:
        current_last_time = last_collected_time
    if auto_trash_ends is not None:
        current_auto_ends = auto_trash_ends
    
    items_json = json.dumps(current_items)
    c.execute("""
        INSERT OR REPLACE INTO trash_inventory 
        (user_id, items, last_collected_time, auto_trash_ends) 
        VALUES (?, ?, ?, ?)
    """, (user_id, items_json, current_last_time, current_auto_ends))
    
    conn.commit()
    conn.close()

def can_collect_trash(user_id):
    """Проверяет, может ли пользователь собирать мусор"""
    inventory = get_user_trash_inventory(user_id)
    current_time = time.time()
    return current_time - inventory["last_collected_time"] >= 2  # 2 секунды кулдаун

def get_random_trash():
    """Возвращает случайный мусор с учетом вероятностей"""
    # 70% шанс найти что-то, 30% шанс ничего не найти
    if random.random() > 0.7:
        return None
    
    # Взвешенная вероятность: более дешевые предметы встречаются чаще
    weighted_items = []
    for item_name, item_data in TRASH_ITEMS.items():
        weight = 15 if item_data["price"] < 500 else 8 if item_data["price"] < 2000 else 3 if item_data["price"] < 5000 else 1
        weighted_items.extend([item_name] * weight)
    
    return random.choice(weighted_items)

def add_item_to_inventory(user_id, item_name):
    """Добавляет предмет в инвентарь пользователя"""
    inventory = get_user_trash_inventory(user_id)
    items = inventory["items"]
    
    if item_name in items:
        items[item_name] += 1
    else:
        items[item_name] = 1
    
    update_user_trash_inventory(user_id, items, time.time(), inventory["auto_trash_ends"])
    return items

def calculate_total_value(items):
    """Вычисляет общую стоимость всех предметов"""
    total = 0
    for item_name, count in items.items():
        if item_name in TRASH_ITEMS:
            total += TRASH_ITEMS[item_name]["price"] * count
    return total

def is_auto_trash_active(user_id):
    """Проверяет, активна ли авто-сборка у пользователя"""
    inventory = get_user_trash_inventory(user_id)
    return time.time() < inventory["auto_trash_ends"]

def check_button_owner(call, user_id):
    """Проверяет владельца кнопки"""
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "🚫 Это не твоя кнопка", show_alert=True)
        return False
    return True

def start_auto_trash(user_id):
    """Запускает авто-сборку мусора"""
    if user_id in AUTO_TRASH_USERS:
        return
    
    end_time = time.time() + AUTO_TRASH_TIME
    AUTO_TRASH_USERS[user_id] = end_time
    
    # Сохраняем время окончания в базу
    inventory = get_user_trash_inventory(user_id)
    update_user_trash_inventory(
        user_id, 
        inventory["items"], 
        inventory["last_collected_time"], 
        end_time
    )
    
    def auto_collect_loop():
        """Цикл авто-сбора"""
        start_time = time.time()
        items_collected = 0
        
        while time.time() < AUTO_TRASH_USERS.get(user_id, 0):
            # Собираем мусор каждую секунду
            item = get_random_trash()
            if item:
                add_item_to_inventory(user_id, item)
                items_collected += 1
            
            time.sleep(1)
        
        # Удаляем из активных сборок
        AUTO_TRASH_USERS.pop(user_id, None)
        
        # Обнуляем время окончания в базе
        inventory = get_user_trash_inventory(user_id)
        update_user_trash_inventory(
            user_id, 
            inventory["items"], 
            inventory["last_collected_time"], 
            0
        )
        
        logger.info(f"✅ Авто-сборка завершена для {user_id}, собрано предметов: {items_collected}")
    
    # Запускаем в отдельном потоке
    thread = threading.Thread(target=auto_collect_loop, daemon=True)
    thread.start()
    
    logger.info(f"🚗 Авто-сборка запущена для {user_id} на 40 минут")

# ================== КОМАНДА: НАЧАТЬ СБОРКУ МУСОРА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["начать сборку мусора", "сборка мусора"])
def start_trash_collection(message):
    """Начинает сбор мусора"""
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    text = f"{mention}, Начни собирать мусор и зарабатывать на этом деньги по кнопке ниже ↓"
    
    kb = InlineKeyboardMarkup()
    
    # Проверяем, активна ли авто-сборка
    if is_auto_trash_active(user_id):
        auto_time_left = get_user_trash_inventory(user_id)["auto_trash_ends"] - time.time()
        minutes_left = int(auto_time_left // 60)
        seconds_left = int(auto_time_left % 60)
        text += f"\n\n🚗 <b>Авто-сборка активна! Осталось: {minutes_left} минут {seconds_left} секунд</b>"
    else:
        # Только если авто-сборка НЕ активна - показываем кнопку ручного сбора
        kb.add(InlineKeyboardButton("🗑️ Собрать мусор", callback_data=f"collect_trash_{user_id}"))
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

# ================== КНОПКА: СОБРАТЬ МУСОР ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("collect_trash_"))
def collect_trash_callback(call):
    """Обработка сбора мусора"""
    try:
        user_id = int(call.data.split("_")[2])
        if not check_button_owner(call, user_id):
            return
        
        # Проверяем, активна ли авто-сборка
        if is_auto_trash_active(user_id):
            bot.answer_callback_query(call.id, "🚫 Авто-сборка активна! Подожди её завершения", show_alert=True)
            return

        # Проверяем кулдаун (тихо, без уведомлений)
        if not can_collect_trash(user_id):
            return

        found_item = get_random_trash()
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        # Создаем клавиатуру
        kb = InlineKeyboardMarkup()
        
        # Проверяем активную авто-сборку
        if is_auto_trash_active(user_id):
            auto_time_left = get_user_trash_inventory(user_id)["auto_trash_ends"] - time.time()
            minutes_left = int(auto_time_left // 60)
            seconds_left = int(auto_time_left % 60)
            text = f"{mention}, 🚗 <b>Авто-сборка активна! Осталось: {minutes_left} минут {seconds_left} секунд</b>"
        else:
            kb.add(InlineKeyboardButton("🗑️ Собрать мусор", callback_data=f"collect_trash_{user_id}"))
            kb.add(InlineKeyboardButton("🚗 Купить авто-сборку", callback_data=f"buy_autotrash_{user_id}"))
            
            if found_item:
                add_item_to_inventory(user_id, found_item)
                item_data = TRASH_ITEMS[found_item]
                text = f"{mention}, собирая мусор ты нашёл <code>{found_item}</code> (стоимость: {item_data['price']}$)"
            else:
                text = f"{mention}, собирая мусор ты не нашёл ничего ценного."

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Ошибка сбора мусора: {e}")

# ================== КНОПКА: КУПИТЬ АВТО-СБОРКУ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_autotrash_"))
def buy_autotrash(call):
    """Покупка авто-сборки мусора"""
    try:
        user_id = int(call.data.split("_")[2])
        if not check_button_owner(call, user_id):
            return
        
        # Проверяем, не активна ли уже авто-сборка
        if is_auto_trash_active(user_id):
            bot.answer_callback_query(call.id, "🚫 У тебя уже активна авто-сборка!", show_alert=True)
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = (
            f"{mention}, вы точно хотите купить авто-сборку мусора за <b>{format_number(AUTO_TRASH_PRICE)}$</b>?\n\n"
            f"🚗 <b>Авто-сборка на 40 минут</b>\n"
            f"⏱ <i>Будет собирать мусор каждую секунду автоматически</i>\n"
            f"💰 <i>Пока активна - ручной сбор отключен</i>"
        )
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅", callback_data=f"confirm_autotrash_{user_id}"),
            InlineKeyboardButton("❌", callback_data=f"cancel_autotrash_{user_id}")
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
        logger.error(f"Ошибка покупки авто-сбора: {e}")

# ================== КНОПКА: ПОДТВЕРДИТЬ ПОКУПКУ АВТО-СБОРКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_autotrash_"))
def confirm_autotrash(call):
    """Подтверждение покупки авто-сборки"""
    try:
        user_id = int(call.data.split("_")[2])
        if not check_button_owner(call, user_id):
            return
        
        # Проверяем баланс
        user_data = get_user_data(user_id)
        if user_data["balance"] < AUTO_TRASH_PRICE:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств!", show_alert=True)
            return
        
        # Проверяем, не активна ли уже авто-сборка
        if is_auto_trash_active(user_id):
            bot.answer_callback_query(call.id, "🚫 У тебя уже активна авто-сборка!", show_alert=True)
            return
        
        # Списываем деньги
        user_data["balance"] -= AUTO_TRASH_PRICE
        save_casino_data()
        
        # Запускаем авто-сборку
        start_auto_trash(user_id)
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        text = (
            f"✅ {mention}, авто-сборка мусора активирована на <b>40 минут</b>!\n\n"
            f"🚗 <b>Теперь мусор собирается автоматически</b>\n"
            f"⏱ <i>Ручной сбор временно отключен</i>\n"
            f"💰 Списано: {format_number(AUTO_TRASH_PRICE)}$\n"
            f"💵 Баланс: {format_number(user_data['balance'])}$"
        )
        
        # Обновляем сообщение
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id, "✅ Авто-сборка активирована!")
        
    except Exception as e:
        logger.error(f"Ошибка активации авто-сбора: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при активации!", show_alert=True)

# ================== КНОПКА: ОТМЕНА ПОКУПКИ АВТО-СБОРКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_autotrash_"))
def cancel_autotrash(call):
    """Отмена покупки авто-сборки"""
    try:
        user_id = int(call.data.split("_")[2])
        if not check_button_owner(call, user_id):
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        # Возвращаем к обычному сбору
        kb = InlineKeyboardMarkup()
        
        # Проверяем активную авто-сборку
        if is_auto_trash_active(user_id):
            auto_time_left = get_user_trash_inventory(user_id)["auto_trash_ends"] - time.time()
            minutes_left = int(auto_time_left // 60)
            seconds_left = int(auto_time_left % 60)
            text = f"{mention}, 🚗 <b>Авто-сборка активна! Осталось: {minutes_left} минут {seconds_left} секунд</b>"
        else:
            kb.add(InlineKeyboardButton("🗑️ Собрать мусор", callback_data=f"collect_trash_{user_id}"))
            kb.add(InlineKeyboardButton("🚗 Купить авто-сборку", callback_data=f"buy_autotrash_{user_id}"))
            text = f"{mention}, сборка мусора\n\nНажми кнопку ниже чтобы собрать мусор"
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        bot.answer_callback_query(call.id, "❌ Покупка отменена")
        
    except Exception as e:
        logger.error(f"Ошибка отмены авто-сбора: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при отмене!", show_alert=True)

# ================== КОМАНДА: МОЙ ИНВЕНТАРЬ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой инвентарь", "мой инв", "инв"])
def show_trash_inventory(message):
    """Показывает инвентарь пользователя"""
    user_id = message.from_user.id
    mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
    
    inventory = get_user_trash_inventory(user_id)
    items = inventory["items"]
    
    if not items:
        text = f"{mention}, твой мусорный пакет пуст. Начни собирать мусор!"
    else:
        text = f"{mention}, в твоём мусорном пакете лежат:\n\n"
        
        total_value = 0
        for item_name, count in items.items():
            if item_name in TRASH_ITEMS:
                item_data = TRASH_ITEMS[item_name]
                item_value = item_data["price"] * count
                total_value += item_value
                text += f"{item_data['emoji']} {item_name} ×{count} — {format_number(item_value)}$\n"
        
        text += f"\n💰 Продать всё можно за <b>{format_number(total_value)}$</b>"
    
    # Проверяем активную авто-сборку
    if is_auto_trash_active(user_id):
        auto_time_left = inventory["auto_trash_ends"] - time.time()
        minutes_left = int(auto_time_left // 60)
        seconds_left = int(auto_time_left % 60)
        text += f"\n\n🚗 <b>Авто-сборка активна! Осталось: {minutes_left} минут {seconds_left} секунд</b>"
    
    # Создаем клавиатуру
    kb = InlineKeyboardMarkup()
    
    if items:
        kb.add(InlineKeyboardButton("💰 Продать всё", callback_data=f"sell_all_trash_{user_id}"))
    
    # Показываем кнопку ручного сбора ТОЛЬКО если авто-сборка НЕ активна
    if not is_auto_trash_active(user_id):
        kb.add(InlineKeyboardButton("🗑️ Собрать мусор", callback_data=f"collect_trash_{user_id}"))
    
    # Показываем кнопку покупки авто-сборки только если она не активна
    if not is_auto_trash_active(user_id):
        kb.add(InlineKeyboardButton("🚗 Купить авто-сборку", callback_data=f"buy_autotrash_{user_id}"))
    
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

# ================== КНОПКА: ПРОДАТЬ ВСЁ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("sell_all_trash_"))
def sell_all_trash_callback(call):
    """Обработка продажи всего мусора"""
    try:
        user_id = int(call.data.split("_")[3])
        if not check_button_owner(call, user_id):
            return
        
        inventory = get_user_trash_inventory(user_id)
        items = inventory["items"]
        
        if not items:
            bot.answer_callback_query(call.id, "❌ Твой мусорный пакет пуст!", show_alert=True)
            return
        
        total_value = calculate_total_value(items)
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"{mention}, ты хочешь продать все вещи за <b>{format_number(total_value)}$</b>?\n\nВы точно хотите продать все вещи?"
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅", callback_data=f"confirm_sell_all_{user_id}"),
            InlineKeyboardButton("❌", callback_data=f"cancel_sell_all_{user_id}")
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
        logger.error(f"Ошибка продажи мусора: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при продаже!", show_alert=True)

# ================== КНОПКА: ПОДТВЕРДИТЬ ПРОДАЖУ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_sell_all_"))
def confirm_sell_all_callback(call):
    """Подтверждение продажи всего мусора"""
    try:
        user_id = int(call.data.split("_")[3])
        if not check_button_owner(call, user_id):
            return
        
        # Получаем инвентарь и вычисляем стоимость
        inventory = get_user_trash_inventory(user_id)
        items = inventory["items"]
        total_value = calculate_total_value(items)
        
        # Начисляем деньги на баланс
        user_data = get_user_data(user_id)
        user_data["balance"] += total_value
        save_casino_data()
        
        # Очищаем инвентарь
        update_user_trash_inventory(user_id, {}, inventory["last_collected_time"], inventory["auto_trash_ends"])
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        text = f"{mention}, ты продал все найденные вещи за <b>{format_number(total_value)}$</b>. Деньги уже на твоём счёту работяга 😸"
        
        # Обновляем сообщение без кнопок
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, f"✅ Получено: {format_number(total_value)}$")
        
    except Exception as e:
        logger.error(f"Ошибка подтверждения продажи: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при продаже!", show_alert=True)

# ================== КНОПКА: ОТМЕНИТЬ ПРОДАЖУ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_sell_all_"))
def cancel_sell_all_callback(call):
    """Отмена продажи всего мусора"""
    try:
        user_id = int(call.data.split("_")[3])
        if not check_button_owner(call, user_id):
            return
        
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        # Возвращаем к просмотру инвентаря
        inventory = get_user_trash_inventory(user_id)
        items = inventory["items"]
        
        if items:
            text = f"{mention}, в твоём мусорном пакете лежат:\n\n"
            
            total_value = 0
            for item_name, count in items.items():
                if item_name in TRASH_ITEMS:
                    item_data = TRASH_ITEMS[item_name]
                    item_value = item_data["price"] * count
                    total_value += item_value
                    text += f"{item_data['emoji']} {item_name} ×{count} — {format_number(item_value)}$\n"
            
            text += f"\n💰 Продать все можно за <b>{format_number(total_value)}$</b>"
            
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("💰 Продать всё", callback_data=f"sell_all_trash_{user_id}"))
            
            # Показываем кнопку ручного сбора ТОЛЬКО если авто-сборка НЕ активна
            if not is_auto_trash_active(user_id):
                kb.add(InlineKeyboardButton("🗑️ Собрать мусор", callback_data=f"collect_trash_{user_id}"))
            
            # Показываем кнопку покупки авто-сборки только если она не активна
            if not is_auto_trash_active(user_id):
                kb.add(InlineKeyboardButton("🚗 Купить авто-сборку", callback_data=f"buy_autotrash_{user_id}"))
        else:
            text = f"{mention}, твой мусорный пакет пуст. Начни собирать мусор!"
            kb = InlineKeyboardMarkup()
            
            # Показываем кнопку ручного сбора ТОЛЬКО если авто-сборка НЕ активна
            if not is_auto_trash_active(user_id):
                kb.add(InlineKeyboardButton("🗑️ Собрать мусор", callback_data=f"collect_trash_{user_id}"))
            
            if not is_auto_trash_active(user_id):
                kb.add(InlineKeyboardButton("🚗 Купить авто-сборку", callback_data=f"buy_autotrash_{user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id, "❌ Продажа отменена")
        
    except Exception as e:
        logger.error(f"Ошибка отмены продажи: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при отмене!", show_alert=True)

print("✅ Система сбора мусора с авто-сборкой загружена и готова к работе! 🗑️🚗")
        
 
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
        InlineKeyboardButton("⛏️", callback_data=f"mine_pickaxe_shop_{user_id}"),
        InlineKeyboardButton("🎒", callback_data=f"mine_inventory_{user_id}")
    )
    kb.add(InlineKeyboardButton("👤", callback_data=f"mine_profile_{user_id}"))
    
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
                text += f"⛏️ <b>{pick_data['name']}</b> - {format_number(pick_data['price'])}$\n"
            text += f"   └─ Бонус: x{pick_data['rarity_bonus']} | Прочность: {pick_data['durability']}\n\n"
        
        kb = InlineKeyboardMarkup(row_width=2)
        
        # Кнопки для покупки кирок (кроме деревянной)
        for pick_id in range(2, 8):
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
            InlineKeyboardButton("✅", callback_data=f"mine_confirm_buy_{user_id}_{pickaxe_id}"),
            InlineKeyboardButton("❌", callback_data=f"mine_pickaxe_shop_{user_id}")
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
            
            text += f"\n💰 Общая стоимость: {format_number(total_value)}$"
        
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
            f"💰 Общая стоимость: <code>{format_number(total_value)}$</code>"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅", callback_data=f"mine_confirm_sell_all_{user_id}"),
            InlineKeyboardButton("❌", callback_data=f"mine_my_ores_{user_id}")
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
            f"💰 Получено: <code>{format_number(total_value)}$</code>\n"
            f"📦 Баланс: <code>{format_number(user_data['balance'])}$</code>\n\n"
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
        bot.answer_callback_query(call.id, f"+{format_number(total_value)}$")

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
            f"за <code>{format_number(total)}$</code>?"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅", callback_data=f"mine_confirm_sell_ore_{user_id}_{ore_name}"),
            InlineKeyboardButton("❌", callback_data=f"mine_my_ores_{user_id}")
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
        text = f"✅ {mention}, ты продал <b>{ore_name} ×{quantity}</b> за <code>{format_number(total)}$</code>"

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
            f"💰 Текущий баланс: {format_number(user_data['balance'])}$"
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


# ================== ПРАВИЛА БОТА (УЛУЧШЕННЫЕ И КРАТКИЕ) ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["правила бота", "правила", "правило"])
def rules_command(message):
    rules_text = """
🔴 <b>ПРАВИЛА MEOW GAME</b> 

<b>Основные правила поведения:</b>

1️⃣ <b>Уважение к другим</b>
• Жёсткие оскорбления и угрозы
• Дискриминация, расизм
• Провокации на конфликты
<i>Наказание: Мут 60-180 минут</i>

2️⃣ <b>Запрещенный контент</b>
• Пропаганда наркотиков, насилия
• Политические споры
• Сексуальный контент в никах/аватарах
<i>Наказание: Мут 120-300 минут</i>

3️⃣ <b>Реклама и спам</b>
• Реклама каналов, сайтов, проектов
• Флуд (более 4 сообщений подряд)
• Ссылки на сторонние ресурсы
<i>Наказание: Мут 30-90 минут</i>

4️⃣ <b>Мошенничество</b>
• Обман других игроков
• Продажа аккаунтов в сторонних сервисах
• Выдача себя за администратора
<i>Наказание: Мут 180-360 минут</i>

5️⃣ <b>Работа с администрацией</b>
• Спам администраторам не по делу
• Критика без конструктивного диалога
• Нарушение указаний администраторов
<i>Наказание: Мут 60-180 минут</i>

━━━━━━━━━━━━━━━━━━━
<b>Важно:</b> Администрация оставляет за собой право выносить наказания по своему усмотрению в зависимости от ситуации.

<b>С любовью, ваша администрация MEOW GAME ❤️</b>
"""
    
    # Создаем инлайн клавиатуру с кнопкой
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🗨️ Наш чат", url="https://t.me/meowchatgame"))
    
    bot.send_message(message.chat.id, rules_text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)

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
        f"➤ <b>БАЛАНС</b>\n\n"
        f"👤 <b>Имя:</b> {clickable}\n"
        f"💰 <b>Баланс:</b> <code>{format_number(data['balance'])}$</code>\n"
        f"🔰 <b>Префикс:</b> {prefix_display}\n"
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
        fake = _make_fake_message_from_call(call)
        broadcast_panel(fake)
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
        broadcast_panel(message)
        return
    try:
        chat_id = int(message.text.strip())
        chats = load_broadcast_chats()
        if chat_id not in chats:
            bot.send_message(message.chat.id, f"❌ Чат <code>{chat_id}</code> не найден!", parse_mode="HTML")
            broadcast_panel(message)
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
    broadcast_panel(message)

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
    if msg.text:
        return {"type":"text","text":msg.text}
    if getattr(msg, "photo", None):
        return {"type":"photo","file_id":msg.photo[-1].file_id,"caption":(msg.caption or "")}
    if getattr(msg, "video", None):
        return {"type":"video","file_id":msg.video.file_id,"caption":(msg.caption or "")}
    if getattr(msg, "animation", None):
        return {"type":"animation","file_id":msg.animation.file_id,"caption":(msg.caption or "")}
    return {"type":"unknown"}

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
    msg = bot.send_message(call.message.chat.id,
                           f"📢 <b>Создание рассылки</b>\n\nБудет отправлено в: <b>{active_chats}</b> чатов\n\n"
                           f"Отправь сообщение для рассылки (текст / фото / видео / гиф / с подписью):",
                           parse_mode="HTML")
    bot.register_next_step_handler(msg, process_broadcast_send)

def process_broadcast_send(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    admin_id = message.from_user.id
    
    # Сохраняем форматирование (entities)
    entities = message.entities or message.caption_entities
    
    content = _store_broadcast_content_from_message(message)
    # Сохраняем entities для сохранения форматирования
    content["entities"] = entities
    
    # Инициализируем с пустым списком кнопок
    _broadcast_states[admin_id] = {
        "content": content,
        "pin": False,
        "inline_buttons": []  # Множественные кнопки
    }
    
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
    state = _broadcast_states[admin_id]
    if state["inline_buttons"]:
        buttons_text = f"\n📎 Кнопок: {len(state['inline_buttons'])}"
        for i, btn in enumerate(state["inline_buttons"], 1):
            buttons_text += f"\n{i}. {btn['text']} -> {btn['url']}"

    preview_info = (
        f"📋 <b>Превью рассылки</b>\n\n"
        f"📤 Будет отправлено в: <b>{len(active_chats)}</b> чатов\n"
        f"📌 Закрепить: <b>{'Да' if state['pin'] else 'Нет'}</b>"
        f"{buttons_text}\n\n"
        f"Нажми «Просмотр» чтобы увидеть сообщение или «Начать рассылку» для отправки."
    )

    bot.send_message(message.chat.id, preview_info, parse_mode="HTML", reply_markup=kb)

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
    
    # Создаем клавиатуру с кнопками если они есть
    rm = None
    if state["inline_buttons"]:
        kb = types.InlineKeyboardMarkup()
        for btn in state["inline_buttons"]:
            kb.add(types.InlineKeyboardButton(btn["text"], url=btn["url"]))
        rm = kb

    # Отправляем превью С СОХРАНЕНИЕМ ФОРМАТИРОВАНИЯ
    if content["type"] == "text":
        text = content["text"]
        if state["inline_buttons"]:
            text += "\n\n📎 <i>К сообщению прикреплены кнопки</i>"
        
        if entities:
            # Сохраняем форматирование через entities
            bot.send_message(
                call.message.chat.id, 
                f"📥 <b>Превью текста:</b>\n\n{text}",
                entities=entities,
                reply_markup=rm
            )
        else:
            bot.send_message(call.message.chat.id, f"📥 <b>Превью текста:</b>\n\n{text}", parse_mode="HTML", reply_markup=rm)
    
    elif content["type"] == "photo":
        caption = content.get("caption","") or ""
        if state["inline_buttons"]:
            caption += "\n\n📎 <i>К сообщению прикреплены кнопки</i>"
        
        if entities:
            bot.send_photo(
                call.message.chat.id, 
                content["file_id"], 
                caption=f"📷 <b>Превью фото:</b>\n\n{caption}",
                caption_entities=entities,
                reply_markup=rm
            )
        else:
            bot.send_photo(call.message.chat.id, content["file_id"], caption=f"📷 <b>Превью фото:</b>\n\n{caption}", parse_mode="HTML", reply_markup=rm)
    
    elif content["type"] == "video":
        caption = content.get("caption","") or ""
        if state["inline_buttons"]:
            caption += "\n\n📎 <i>К сообщению прикреплены кнопки</i>"
        
        if entities:
            bot.send_video(
                call.message.chat.id, 
                content["file_id"], 
                caption=f"📹 <b>Превью видео:</b>\n\n{caption}",
                caption_entities=entities,
                reply_markup=rm
            )
        else:
            bot.send_video(call.message.chat.id, content["file_id"], caption=f"📹 <b>Превью видео:</b>\n\n{caption}", parse_mode="HTML", reply_markup=rm)
    
    elif content["type"] == "animation":
        caption = content.get("caption","") or ""
        if state["inline_buttons"]:
            caption += "\n\n📎 <i>К сообщению прикреплены кнопки</i>"
        
        if entities:
            bot.send_animation(
                call.message.chat.id, 
                content["file_id"], 
                caption=f"🔁 <b>Превью гифки:</b>\n\n{caption}",
                caption_entities=entities,
                reply_markup=rm
            )
        else:
            bot.send_animation(call.message.chat.id, content["file_id"], caption=f"🔁 <b>Превью гифки:</b>\n\n{caption}", parse_mode="HTML", reply_markup=rm)
    else:
        bot.send_message(call.message.chat.id, "❌ Невозможно показать предварительный просмотр этого типа сообщения.")

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
        fake = _make_fake_message_from_call(call)
        broadcast_panel(fake)
        return

    content = state["content"]
    pin = state["pin"]
    inline_buttons = state.get("inline_buttons", [])
    entities = content.get("entities", [])

    # Создаем клавиатуру с кнопками если они есть
    rm = None
    if inline_buttons:
        kb = types.InlineKeyboardMarkup()
        for btn in inline_buttons:
            kb.add(types.InlineKeyboardButton(btn["text"], url=btn["url"]))
        rm = kb

    # Прогресс рассылки
    total = len(active_chats)
    sent = 0
    failed = 0
    progress_msg = bot.send_message(call.message.chat.id, f"📤 <b>Начинаю рассылку...</b>\n\n⏳ Прогресс: 0/{total}\n✅ Успешно: 0\n❌ Ошибок: 0", parse_mode="HTML")

    # Цикл рассылки
    for i, chat_id in enumerate(active_chats, 1):
        try:
            if content["type"] == "text":
                # Используем entities для сохранения форматирования
                if entities:
                    sent_msg = bot.send_message(
                        chat_id, 
                        content["text"], 
                        entities=entities,
                        reply_markup=rm
                    )
                else:
                    sent_msg = bot.send_message(
                        chat_id, 
                        content["text"], 
                        reply_markup=rm
                    )
            
            elif content["type"] == "photo":
                caption = content.get("caption","") or None
                if entities and caption:
                    sent_msg = bot.send_photo(
                        chat_id, 
                        content["file_id"], 
                        caption=caption,
                        caption_entities=entities,
                        reply_markup=rm
                    )
                else:
                    sent_msg = bot.send_photo(
                        chat_id, 
                        content["file_id"], 
                        caption=caption,
                        reply_markup=rm
                    )
            
            elif content["type"] == "video":
                caption = content.get("caption","") or None
                if entities and caption:
                    sent_msg = bot.send_video(
                        chat_id, 
                        content["file_id"], 
                        caption=caption,
                        caption_entities=entities,
                        reply_markup=rm
                    )
                else:
                    sent_msg = bot.send_video(
                        chat_id, 
                        content["file_id"], 
                        caption=caption,
                        reply_markup=rm
                    )
            
            elif content["type"] == "animation":
                caption = content.get("caption","") or None
                if entities and caption:
                    sent_msg = bot.send_animation(
                        chat_id, 
                        content["file_id"], 
                        caption=caption,
                        caption_entities=entities,
                        reply_markup=rm
                    )
                else:
                    sent_msg = bot.send_animation(
                        chat_id, 
                        content["file_id"], 
                        caption=caption,
                        reply_markup=rm
                    )
            else:
                # Просто текст без форматирования
                sent_msg = bot.send_message(chat_id, "📢 Сообщение от администрации.", reply_markup=rm)
            
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
                bot.edit_message_text(f"📤 <b>Рассылка в процессе...</b>\n\n⏳ Прогресс: {i}/{total}\n✅ Успешно: {sent}\n❌ Ошибок: {failed}", call.message.chat.id, progress_msg.message_id, parse_mode="HTML")
            except:
                pass
        time.sleep(0.3)

    # Финальный результат
    eff = round((sent/total)*100, 1) if total else 0
    bot.edit_message_text(f"🎉 <b>Рассылка завершена!</b>\n\n📊 Результаты:\n• Всего чатов: {total}\n• ✅ Успешно: {sent}\n• ❌ Ошибок: {failed}\n• 📈 Эффективность: {eff}%", call.message.chat.id, progress_msg.message_id, parse_mode="HTML")

    _broadcast_states.pop(admin_id, None)
    fake = _make_fake_message_from_call(call)
    broadcast_panel(fake)

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

# Также обнови функцию _store_broadcast_content_from_message:
def _store_broadcast_content_from_message(msg):
    # Сохраняем entities для форматирования
    entities = msg.entities or msg.caption_entities
    
    if msg.text:
        return {
            "type": "text",
            "text": msg.text,
            "entities": entities
        }
    if getattr(msg, "photo", None):
        return {
            "type": "photo",
            "file_id": msg.photo[-1].file_id,
            "caption": msg.caption or "",
            "entities": entities
        }
    if getattr(msg, "video", None):
        return {
            "type": "video",
            "file_id": msg.video.file_id,
            "caption": msg.caption or "",
            "entities": entities
        }
    if getattr(msg, "animation", None):
        return {
            "type": "animation",
            "file_id": msg.animation.file_id,
            "caption": msg.caption or "",
            "entities": entities
        }
    return {"type": "unknown", "entities": entities}

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

    # Ищем ВСЕ .db и .json
    for file in os.listdir(workdir):
        if file.endswith(".db") or file.endswith(".json"):
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
                "🛡 База безопасна"
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
                InlineKeyboardButton("💍 Согласиться", callback_data=f"marriage_accept_{user_id}_{target_user_id}"),
                InlineKeyboardButton("❌ Отказать", callback_data=f"marriage_reject_{user_id}_{target_user_id}")
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
                    f"💍 С ребёнком не тяните 👉👈"
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

# ================== КОМАНДА "МОЙ БРАК" ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой брак", "брак", "статистика брака"])
def my_marriage(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'
        
        marriage = get_marriage(user_id)
        stats = get_marriage_stats(user_id)
        
        if not marriage:
            text = (
                f"💔 {mention}, ты не состоишь в браке 😔\n\n"
                f"📊 <b>Статистика браков:</b>\n"
                f"• Всего браков: {stats['total_marriages']}\n"
                f"• Всего дней в браке: {stats['total_days_married']}\n"
                f"• Самый долгий брак: {stats['longest_marriage_days']} дней"
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
            f"💞 {mention}, ты состоишь в браке с {partner_mention}\n\n"
            f"💍 <b>Информация о браке:</b>\n"
            f"• Вместе уже: <b>{days_married}</b> дней\n"
            f"• Ранг: {marriage_rank}\n"
            f"• Дата брака: {datetime.fromisoformat(marriage['married_at']).strftime('%d.%m.%Y')}\n\n"
            f"📊 <b>Общая статистика:</b>\n"
            f"• Всего браков: {stats['total_marriages']}\n"
            f"• Всего дней в браке: {stats['total_days_married']}\n"
            f"• Рекорд: {stats['longest_marriage_days']} дней"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💔 Развестись", callback_data=f"marriage_divorce_{user_id}"))
        kb.add(InlineKeyboardButton("📊 Общая статистика", callback_data=f"marriage_stats_{user_id}"))
        
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка показа брака: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при получении информации о браке!")

# ================== ОБРАБОТЧИК КНОПКИ РАЗВОДА ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("marriage_divorce_"))
def divorce_marriage_callback(call):
    try:
        # Разбираем callback data
        parts = call.data.split("_")
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "❌ Ошибка в данных!", show_alert=True)
            return
            
        user_id = int(parts[2])
        
        # Проверяем, что нажимает именно участник брака
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Расторгаем брак
        success, result_msg = divorce_marriage(user_id)
        
        if success:
            # Получаем информацию о пользователе
            try:
                user = bot.get_chat(user_id)
                mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
                
                text = f"💔 {mention}, {result_msg}"
                
            except Exception as e:
                text = f"💔 {result_msg}"
            
            # Редактируем сообщение
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )
            
            bot.answer_callback_query(call.id, "💔 Брак расторгнут!")
        else:
            bot.answer_callback_query(call.id, f"❌ {result_msg}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка развода: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при разводе!", show_alert=True)

# ================== ОБРАБОТЧИК СТАТИСТИКИ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("marriage_stats_"))
def show_marriage_stats_callback(call):
    """Показывает подробную статистику браков"""
    try:
        # Разбираем callback data
        parts = call.data.split("_")
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "❌ Ошибка в данных!", show_alert=True)
            return
            
        user_id = int(parts[2])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя статистика!", show_alert=True)
            return
        
        stats = get_marriage_stats(user_id)
        user = bot.get_chat(user_id)
        mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
        
        text = (
            f"📊 <b>СТАТИСТИКА БРАКОВ</b>\n\n"
            f"👤 {mention}\n\n"
            f"💍 <b>Общая статистика:</b>\n"
            f"• Всего браков: {stats['total_marriages']}\n"
            f"• Всего дней в браке: {stats['total_days_married']}\n"
            f"• Самый долгий брак: {stats['longest_marriage_days']} дней\n\n"
        )
        
        # Добавляем достижения
        achievements = []
        if stats['total_marriages'] >= 10:
            achievements.append("🏆 Серийный брачующийся")
        if stats['longest_marriage_days'] >= 365:
            achievements.append("💎 Год вместе")
        if stats['longest_marriage_days'] >= 365 * 5:
            achievements.append("👑 Ветеран брака")
        
        if achievements:
            text += "🎖️ <b>Достижения:</b>\n" + "\n".join(f"• {ach}" for ach in achievements)
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад к браку", callback_data=f"back_to_marriage_{user_id}"))
        
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
        bot.answer_callback_query(call.id, "❌ Ошибка при показе статистики!", show_alert=True)

# ================== ОБРАБОТЧИК НАЗАД К БРАКУ ==================

@bot.callback_query_handler(func=lambda c: c.data.startswith("back_to_marriage_"))
def back_to_marriage_callback(call):
    """Возвращает к информации о браке"""
    try:
        # Разбираем callback data
        parts = call.data.split("_")
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "❌ Ошибка в данных!", show_alert=True)
            return
            
        user_id = int(parts[3])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)
            return
        
        # Создаем фейковое сообщение для вызова функции
        class FakeMsg:
            def __init__(self, chat_id, from_user):
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = from_user
        
        fake_msg = FakeMsg(call.message.chat.id, call.from_user)
        
        # Вызываем функцию показа брака
        my_marriage(fake_msg)
        
        # Удаляем старое сообщение
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка возврата к браку: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КОМАНДА "БРАКИ" ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["браки", "список браков", "топ браков"])
def marriages_list(message):
    try:
        marriages = get_all_marriages(40)
        
        if not marriages:
            bot.send_message(message.chat.id, "💔 Пока никто не состоит в браке...")
            return
        
        text = "💞 <b>СПИСОК АКТИВНЫХ БРАКОВ</b>\n\n"
        
        for i, (user1_id, user2_id, user1_name, user2_name, married_at) in enumerate(marriages, 1):
            days_married = get_marriage_days(married_at)
            marriage_rank = get_marriage_rank(days_married)
            
            text += (
                f"💍 <b>{i}.</b> "
                f"<a href='tg://user?id={user1_id}'>{user1_name}</a> ❤️ "
                f"<a href='tg://user?id={user2_id}'>{user2_name}</a>\n"
                f"   └─ {marriage_rank} (<b>{days_married}</b> дней)\n\n"
            )
        
        # Добавляем общую статистику
        conn = sqlite3.connect(MARRIAGE_DB)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM marriages")
        total_marriages = c.fetchone()[0]
        conn.close()
        
        text += f"📊 Всего активных браков: <b>{total_marriages}</b>"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔄 Обновить", callback_data="marriages_refresh"))
        
        bot.send_message(message.chat.id, text, parse_mode="HTML", 
                        disable_web_page_preview=True, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка показа списка браков: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при получении списка браков!")

# ================== ОБНОВЛЕНИЕ СПИСКА БРАКОВ ==================

@bot.callback_query_handler(func=lambda c: c.data == "marriages_refresh")
def refresh_marriages_callback(call):
    """Обновляет список браков"""
    try:
        # Создаем фейковое сообщение
        class FakeMsg:
            def __init__(self, chat_id, from_user):
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = from_user
        
        fake_msg = FakeMsg(call.message.chat.id, call.from_user)
        marriages_list(fake_msg)
        
        # Удаляем старое сообщение
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
            
        bot.answer_callback_query(call.id, "🔄 Список обновлен!")
        
    except Exception as e:
        logger.error(f"Ошибка обновления списка браков: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка обновления!", show_alert=True)

# ================== НОВОГОДНЯЯ ИГРА СО СНЕЖКАМИ (ПОЛНАЯ ВЕРСИЯ) ==================
SNOWBALLS_DB = "snowballs.db"

# -------------------------------------------------------------
#   ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# -------------------------------------------------------------
def init_snowballs_db():
    conn = sqlite3.connect(SNOWBALLS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS snowballs (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            snowballs_count INTEGER DEFAULT 0,
            golden_snowballs INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            last_snowball_time TEXT,
            daily_claimed TEXT
        )
    """)
    conn.commit()
    conn.close()

init_snowballs_db()

# -------------------------------------------------------------
#   КОНФИГУРАЦИЯ СНЕЖКОВ
# -------------------------------------------------------------
SNOWBALL_CONFIG = {
    "cooldown": 2,
    "exchange_rate": 50,
    "golden_chance": 0.05,
    "golden_multiplier": 5,
    "xp_per_snowball": 10,
    "levels": {
        1: 0, 2: 100, 3: 250, 4: 500, 5: 1000,
        6: 2000, 7: 4000, 8: 8000, 9: 15000, 10: 30000
    },
    "daily_reward": 10
}

# -------------------------------------------------------------
#   РАБОТА С ДАННЫМИ ПОЛЬЗОВАТЕЛЯ
# -------------------------------------------------------------
def get_user_snowballs(user_id):
    conn = sqlite3.connect(SNOWBALLS_DB)
    c = conn.cursor()
    c.execute("SELECT snowballs_count, golden_snowballs, level, xp, last_snowball_time, daily_claimed FROM snowballs WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()

    if result:
        return {
            "snowballs_count": result[0],
            "golden_snowballs": result[1],
            "level": result[2],
            "xp": result[3],
            "last_snowball_time": result[4],
            "daily_claimed": result[5]
        }

    conn = sqlite3.connect(SNOWBALLS_DB)
    c = conn.cursor()
    c.execute("INSERT INTO snowballs (user_id, username, snowballs_count, golden_snowballs, level, xp) VALUES (?, ?, ?, ?, ?, ?)", 
              (user_id, "", 0, 0, 1, 0))
    conn.commit()
    conn.close()

    return {"snowballs_count": 0, "golden_snowballs": 0, "level": 1, "xp": 0, "last_snowball_time": None, "daily_claimed": None}


def update_user_snowballs(user_id, username, snowballs_count, golden_snowballs, level, xp, last_time, daily_claimed):
    conn = sqlite3.connect(SNOWBALLS_DB)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO snowballs 
        (user_id, username, snowballs_count, golden_snowballs, level, xp, last_snowball_time, daily_claimed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, snowballs_count, golden_snowballs, level, xp, last_time, daily_claimed))
    conn.commit()
    conn.close()


def get_snowballs_top(limit=10):
    conn = sqlite3.connect(SNOWBALLS_DB)
    c = conn.cursor()
    c.execute("""
        SELECT user_id, username, snowballs_count, golden_snowballs, level
        FROM snowballs
        WHERE snowballs_count > 0 OR golden_snowballs > 0
        ORDER BY (snowballs_count + golden_snowballs * 5) DESC, level DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# -------------------------------------------------------------
#   СИСТЕМА УРОВНЕЙ
# -------------------------------------------------------------
def calculate_level(xp):
    levels = SNOWBALL_CONFIG["levels"]
    current_level = 1
    for level, required_xp in levels.items():
        if xp >= required_xp:
            current_level = level
        else:
            break
    return current_level

def get_level_progress(xp, level):
    levels = SNOWBALL_CONFIG["levels"]
    current_level_xp = levels[level]
    next_level_xp = levels.get(level + 1, current_level_xp)
    progress = ((xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100 if next_level_xp > current_level_xp else 100
    return min(progress, 100)

def add_xp(user_id, xp_amount):
    user_data = get_user_snowballs(user_id)
    new_xp = user_data["xp"] + xp_amount
    old_level = user_data["level"]
    new_level = calculate_level(new_xp)
    
    update_user_snowballs(
        user_id, 
        "", 
        user_data["snowballs_count"],
        user_data["golden_snowballs"],
        new_level,
        new_xp,
        user_data["last_snowball_time"],
        user_data["daily_claimed"]
    )
    
    return old_level != new_level, new_level

# -------------------------------------------------------------
#   ЛЕПКА СНЕЖКОВ
# -------------------------------------------------------------
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["слепить снежок", "снежок", "снежки"])
def make_snowball(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{first_name}</a>'

        user_data = get_user_snowballs(user_id)
        now = datetime.now()

        # cooldown
        if user_data["last_snowball_time"]:
            last_time = datetime.fromisoformat(user_data["last_snowball_time"])
            if (now - last_time).total_seconds() < SNOWBALL_CONFIG["cooldown"]:
                time_left = SNOWBALL_CONFIG["cooldown"] - int((now - last_time).total_seconds())
                bot.send_message(
                    message.chat.id,
                    f"⏰ {mention}, подожди еще {time_left} сек!",
                    parse_mode="HTML"
                )
                return

        # тип снежка
        is_golden = random.random() < SNOWBALL_CONFIG["golden_chance"]
        
        # Обновляем счетчики снежков
        if is_golden:
            user_data["golden_snowballs"] += 1
            snowball_text = "🌟 <b>ЗОЛОТОЙ СНЕЖОК!</b>"
            emoji = "🌟"
        else:
            user_data["snowballs_count"] += 1
            snowball_text = "❄️ Обычный снежок"
            emoji = "❄️"

        # Добавляем XP и получаем информацию о повышении уровня
        level_up, new_level = add_xp(user_id, SNOWBALL_CONFIG["xp_per_snowball"])
        
        # После add_xp нужно получить актуальные данные, включая новый уровень
        updated_data = get_user_snowballs(user_id)
        
        # Сохраняем изменения в снежках (уже учтенные в user_data)
        user_data["last_snowball_time"] = now.isoformat()

        # Обновляем данные в базе с учетом всех изменений
        update_user_snowballs(
            user_id, username,
            user_data["snowballs_count"],  # Используем обновленные счетчики
            user_data["golden_snowballs"],
            updated_data["level"],  # Берем актуальный уровень из updated_data
            updated_data["xp"],     # Берем актуальный XP из updated_data
            user_data["last_snowball_time"],
            user_data["daily_claimed"]
        )

        # Для отображения используем данные из updated_data
        text = (
            f"{emoji} {mention}, {snowball_text}\n\n"
            f"📦 Всего снежков: <b>{user_data['snowballs_count']}</b>\n"
            f"🌟 Золотых: <b>{user_data['golden_snowballs']}</b>\n"
            f"⭐ XP: +{SNOWBALL_CONFIG['xp_per_snowball']}\n"
            f"🎯 Уровень: <b>{updated_data['level']}</b>"
        )

        if level_up:
            text += f"\n\n🎉 <b>Новый уровень: {new_level}!</b> 🎉"

        bot.send_message(message.chat.id, text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Snowball error: {e}")

# -------------------------------------------------------------
#   ЕЖЕДНЕВНАЯ НАГРАДА
# -------------------------------------------------------------
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ежедневный", "ежедневный снежок", "снежок день"])
def daily_snowball(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{first_name}</a>'

        data = get_user_snowballs(user_id)
        today = date.today().isoformat()

        if data["daily_claimed"] == today:
            return bot.send_message(
                message.chat.id,
                f"🎁 {mention}, ты уже получал ежедневку сегодня!",
                parse_mode="HTML"
            )

        data["snowballs_count"] += SNOWBALL_CONFIG["daily_reward"]
        data["daily_claimed"] = today

        level_up, new_level = add_xp(user_id, SNOWBALL_CONFIG["xp_per_snowball"] * 2)

        data = get_user_snowballs(user_id)

        update_user_snowballs(
            user_id, username,
            data["snowballs_count"],
            data["golden_snowballs"],
            data["level"],
            data["xp"],
            data["last_snowball_time"],
            data["daily_claimed"]
        )

        text = (
            f"🎁 {mention}, ты получил ежедневный подарок!\n\n"
            f"❄️ +{SNOWBALL_CONFIG['daily_reward']} снежков\n"
            f"⭐ +{SNOWBALL_CONFIG['xp_per_snowball']*2} XP\n"
            f"📦 Всего: <b>{data['snowballs_count']}</b>\n"
            f"🎯 Уровень: <b>{data['level']}</b>"
        )

        if level_up:
            text += f"\n\n🎉 <b>Новый уровень: {new_level}!</b> 🎉"

        bot.send_message(message.chat.id, text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Daily snowball error: {e}")

# -------------------------------------------------------------
#   ПРОФИЛЬ
# -------------------------------------------------------------
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой профиль", "профиль", "снежный профиль"])
def snowball_profile(message):
    try:
        user_id = message.from_user.id
        name = message.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{name}</a>'

        data = get_user_snowballs(user_id)
        progress = get_level_progress(data["xp"], data["level"])

        rank = (
            "Новичок" if data["level"] < 3 else
            "Снежный боец" if data["level"] < 6 else
            "Мастер снежков" if data["level"] < 9 else
            "Снежный король"
        )

        text = (
            "🎄 <b>ТВОЙ СНЕЖНЫЙ ПРОФИЛЬ</b> 🎄\n\n"
            f"👤 Ник: {mention}\n"
            f"🎖️ Звание: {rank}\n"
            f"🎯 Уровень: {data['level']}\n"
            f"📊 Прогресс: {progress:.1f}%\n\n"
            f"❄️ Обычных: <code>{data['snowballs_count']}</code>\n"
            f"🌟 Золотых: <code>{data['golden_snowballs']}</code>\n"
            f"⭐ Опыт: {data['xp']} XP\n\n"
            f"💱 1 снежок = {SNOWBALL_CONFIG['exchange_rate']}$\n"
            f"💱 1 золотой = {SNOWBALL_CONFIG['exchange_rate'] * SNOWBALL_CONFIG['golden_multiplier']}$"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🏆 ТОП игроков", callback_data=f"snow_top_{user_id}_1"),
            InlineKeyboardButton("💎 Обменять", callback_data=f"snow_exchange_{user_id}")
        )
        kb.add(
            InlineKeyboardButton("🎁 Ежедневный", callback_data=f"snow_daily_{user_id}"),
            InlineKeyboardButton("📊 Статистика", callback_data=f"snow_stats_{user_id}")
        )

        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.error("Profile error:", e)

# -------------------------------------------------------------
#   СТАТИСТИКА
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("snow_stats_"))
def show_stats(call):
    try:
        user_id = int(call.data.split("_")[2])

        if call.from_user.id != user_id:
            return bot.answer_callback_query(call.id, "❌ Не твоя кнопка!", True)

        data = get_user_snowballs(user_id)
        total = data["snowballs_count"] + data["golden_snowballs"]

        total_value = (
            data["snowballs_count"] * SNOWBALL_CONFIG["exchange_rate"] +
            data["golden_snowballs"] * SNOWBALL_CONFIG["exchange_rate"] * SNOWBALL_CONFIG["golden_multiplier"]
        )

        top = get_snowballs_top(1000)
        pos = None
        for i, (uid, *_ ) in enumerate(top, 1):
            if uid == user_id:
                pos = i
                break

        text = (
            "📊 <b>СТАТИСТИКА</b>\n\n"
            f"❄️ Всего: {total}\n"
            f"📦 Обычных: {data['snowballs_count']}\n"
            f"🌟 Золотых: {data['golden_snowballs']}\n"
            f"💰 Стоимость: {total_value}$\n\n"
            f"🎯 Уровень: {data['level']}\n"
            f"⭐ Опыт: {data['xp']} XP\n"
        )

        if pos:
            text += f"🏆 Место в топе: #{pos}"

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"snow_profile_{user_id}"))

        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    except:
        bot.answer_callback_query(call.id, "❌ Ошибка!", True)

# -------------------------------------------------------------
#   ТОП
# -------------------------------------------------------------
def show_snowball_top_page(chat_id, message_id, viewer_id, page=1):
    try:
        top = get_snowballs_top(100)
        per_page = 10
        pages = (len(top) + per_page - 1) // per_page

        page = max(1, min(page, pages))
        start = (page - 1) * per_page
        end = start + per_page

        text = f"🎅 <b>ТОП ИГРОКОВ</b>\nСтраница {page}/{pages}\n\n"

        for i, (uid, _, count, golden, level) in enumerate(top[start:end], start + 1):
            try:
                name = bot.get_chat(uid).first_name
                mention = f'<a href="tg://user?id={uid}">{name}</a>'
            except:
                mention = f"User {uid}"

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {mention}\n"
            text += f"   ❄️ {count} | 🌟 {golden} | 🎯 {level}\n\n"

        kb = InlineKeyboardMarkup()

        row = []
        if page > 1:
            row.append(InlineKeyboardButton("⬅️", callback_data=f"snow_top_{viewer_id}_{page-1}"))
        row.append(InlineKeyboardButton(f"{page}/{pages}", callback_data="nope"))
        if page < pages:
            row.append(InlineKeyboardButton("➡️", callback_data=f"snow_top_{viewer_id}_{page+1}"))

        kb.row(*row)
        kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"snow_profile_{viewer_id}"))

        bot.edit_message_text(
            text, chat_id, message_id,
            parse_mode="HTML", reply_markup=kb
        )

    except Exception as e:
        logger.error("Top error:", e)

# -------------------------------------------------------------
#   МЕНЮ ОБМЕНА
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("snow_exchange_") and not any(x in c.data for x in ["normal", "golden", "all"]))
def exchange_menu(call):
    try:
        user_id = int(call.data.split("_")[2])

        if call.from_user.id != user_id:
            return bot.answer_callback_query(call.id, "❌ Не твоя кнопка!", True)

        data = get_user_snowballs(user_id)

        if data["snowballs_count"] == 0 and data["golden_snowballs"] == 0:
            return bot.answer_callback_query(call.id, "❌ Нет снежков!", True)

        total_value = (
            data["snowballs_count"] * SNOWBALL_CONFIG["exchange_rate"] +
            data["golden_snowballs"] * SNOWBALL_CONFIG["exchange_rate"] * SNOWBALL_CONFIG["golden_multiplier"]
        )

        name = call.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{name}</a>'

        text = (
            f"💎 <b>ОБМЕН СНЕЖКОВ</b>\n\n"
            f"{mention}\n\n"
            f"❄️ Обычных: {data['snowballs_count']}\n"
            f"🌟 Золотых: {data['golden_snowballs']}\n\n"
            f"💰 К получению: {total_value}$"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        
        if data["snowballs_count"] > 0:
            kb.add(InlineKeyboardButton(f"❄️ Обычные", callback_data=f"snow_exchange_normal_{user_id}"))
        
        if data["golden_snowballs"] > 0:
            kb.add(InlineKeyboardButton(f"🌟 Золотые", callback_data=f"snow_exchange_golden_{user_id}"))
        
        if data["snowballs_count"] > 0 or data["golden_snowballs"] > 0:
            kb.add(InlineKeyboardButton("💎 Все", callback_data=f"snow_exchange_all_{user_id}"))

        kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"snow_profile_{user_id}"))

        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=kb
        )

    except Exception as e:
        logger.error("Exchange menu error:", e)

# -------------------------------------------------------------
#   ПОДТВЕРЖДЕНИЕ ОБМЕНА
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("snow_exchange_") and any(x in c.data for x in ["normal", "golden", "all"]))
def handle_exchange_type(call):
    try:
        _, _, action, user_id = call.data.split("_")
        user_id = int(user_id)

        if call.from_user.id != user_id:
            return bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", True)

        data = get_user_snowballs(user_id)

        if action == "normal":
            if data["snowballs_count"] == 0:
                return bot.answer_callback_query(call.id, "❌ Нет обычных снежков!", True)
            amount = data["snowballs_count"]
            money = amount * SNOWBALL_CONFIG["exchange_rate"]
            callback = f"snow_confirm_normal_{user_id}"
            text = f"❄️ Обменять {amount} снежков за {money}$?"

        elif action == "golden":
            if data["golden_snowballs"] == 0:
                return bot.answer_callback_query(call.id, "❌ Нет золотых!", True)
            amount = data["golden_snowballs"]
            money = amount * SNOWBALL_CONFIG["exchange_rate"] * SNOWBALL_CONFIG["golden_multiplier"]
            callback = f"snow_confirm_golden_{user_id}"
            text = f"🌟 Обменять {amount} золотых за {money}$?"

        else:
            normal = data["snowballs_count"] * SNOWBALL_CONFIG["exchange_rate"]
            golden = data["golden_snowballs"] * SNOWBALL_CONFIG["exchange_rate"] * SNOWBALL_CONFIG["golden_multiplier"]
            money = normal + golden
            callback = f"snow_confirm_all_{user_id}"
            text = f"💎 Обменять ВСЕ снежки за {money}$?"

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Да", callback_data=callback),
            InlineKeyboardButton("❌ Нет", callback_data=f"snow_exchange_{user_id}")
        )

        name = call.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{name}</a>'

        bot.edit_message_text(
            f"💎 <b>ПОДТВЕРЖДЕНИЕ</b>\n\n{mention}\n\n{text}",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=kb
        )

    except Exception as e:
        logger.error("Confirm exchange error:", e)

# -------------------------------------------------------------
#   ВЫПОЛНЕНИЕ ОБМЕНА
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("snow_confirm_"))
def execute_exchange(call):
    try:
        parts = call.data.split("_")
        action = parts[2]
        user_id = int(parts[3])
        
        if call.from_user.id != user_id:
            return bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)

        data = get_user_snowballs(user_id)
        name = call.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{name}</a>'

        money_earned = 0
        snowballs_used = 0
        golden_used = 0

        if action == "normal" and data["snowballs_count"] > 0:
            snowballs_used = data["snowballs_count"]
            money_earned = snowballs_used * SNOWBALL_CONFIG["exchange_rate"]
            data["snowballs_count"] = 0
            
        elif action == "golden" and data["golden_snowballs"] > 0:
            golden_used = data["golden_snowballs"]
            money_earned = golden_used * SNOWBALL_CONFIG["exchange_rate"] * SNOWBALL_CONFIG["golden_multiplier"]
            data["golden_snowballs"] = 0
            
        elif action == "all":
            snowballs_used = data["snowballs_count"]
            golden_used = data["golden_snowballs"]
            money_earned = (snowballs_used * SNOWBALL_CONFIG["exchange_rate"] + 
                          golden_used * SNOWBALL_CONFIG["exchange_rate"] * SNOWBALL_CONFIG["golden_multiplier"])
            data["snowballs_count"] = 0
            data["golden_snowballs"] = 0

        if money_earned > 0:
            # Начисляем деньги в основную игру
            user_game_data = get_user_data(user_id)
            user_game_data["balance"] += money_earned
            save_casino_data()

            # Сохраняем обновленные данные снежков
            update_user_snowballs(
                user_id, 
                call.from_user.username or "", 
                data["snowballs_count"],
                data["golden_snowballs"],
                data["level"],
                data["xp"],
                data["last_snowball_time"],
                data["daily_claimed"]
            )

            # Формируем сообщение об успехе
            snowballs_text = ""
            if snowballs_used > 0:
                snowballs_text += f"❄️ Обычных: {snowballs_used}\n"
            if golden_used > 0:
                snowballs_text += f"🌟 Золотых: {golden_used}\n"

            text = (
                f"🎉 <b>ОБМЕН УСПЕШНО ВЫПОЛНЕН!</b> 🎉\n\n"
                f"👤 {mention}\n\n"
                f"{snowballs_text}\n"
                f"💰 Получено: <b>{money_earned}$</b>\n\n"
                f"💵 Новый баланс: <b>{user_game_data['balance']}$</b>"
            )

            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 В профиль", callback_data=f"snow_profile_{user_id}"))

            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)
            bot.answer_callback_query(call.id, f"✅ +{money_earned}$")

        else:
            bot.answer_callback_query(call.id, "❌ Нечего обменивать!", show_alert=True)

    except Exception as e:
        logger.error(f"Exchange execution error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при обмене!", show_alert=True)

# -------------------------------------------------------------
#   ЕЖЕДНЕВНАЯ НАГРАДА (CALLBACK)
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("snow_daily_"))
def daily_callback(call):
    try:
        user_id = int(call.data.split("_")[2])
        
        if call.from_user.id != user_id:
            return bot.answer_callback_query(call.id, "❌ Это не твоя кнопка!", show_alert=True)

        # Повторяем логику ежедневной награды
        username = call.from_user.username or ""
        first_name = call.from_user.first_name
        mention = f'<a href="tg://user?id={user_id}">{first_name}</a>'

        user_data = get_user_snowballs(user_id)
        today = date.today().isoformat()

        if user_data["daily_claimed"] == today:
            bot.answer_callback_query(call.id, "🎁 Ты уже получал награду сегодня!", show_alert=True)
            return

        # Выдаем награду
        user_data["snowballs_count"] += SNOWBALL_CONFIG["daily_reward"]
        user_data["daily_claimed"] = today
        
        # Добавляем опыт
        level_up, new_level = add_xp(user_id, SNOWBALL_CONFIG["xp_per_snowball"] * 2)
        
        update_user_snowballs(
            user_id, username, 
            user_data["snowballs_count"],
            user_data["golden_snowballs"],
            user_data["level"],
            user_data["xp"],
            user_data["last_snowball_time"],
            user_data["daily_claimed"]
        )

        message_text = (
            f"🎁 {mention}, ты получил ежедневную награду!\n\n"
            f"❄️ +{SNOWBALL_CONFIG['daily_reward']} снежков\n"
            f"⭐ +{SNOWBALL_CONFIG['xp_per_snowball'] * 2} XP\n"
            f"📦 Всего снежков: <b>{user_data['snowballs_count']}</b>\n"
            f"🎯 Уровень: <b>{user_data['level']}</b>"
        )
        
        if level_up:
            message_text += f"\n\n🎉 <b>ПОЗДРАВЛЯЮ! Ты достиг {new_level} уровня!</b> 🎉"

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 В профиль", callback_data=f"snow_profile_{user_id}"))

        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Daily callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# -------------------------------------------------------------
#   ГЛАВНЫЙ CALLBACK ОБРАБОТЧИК
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("snow_"))
def handle_snow_callbacks(call):
    try:
        parts = call.data.split("_")
        action = parts[1]
        
        if action == "no_action":
            bot.answer_callback_query(call.id)
            return

        user_id = int(parts[2])
        
        if call.from_user.id != user_id:
            return bot.answer_callback_query(call.id, "🎅 Это не твоя кнопка!", show_alert=True)

        # ---------- ТОП (С ПАГИНАЦИЕЙ) ----------
        if action == "top":
            page = int(parts[3]) if len(parts) > 3 else 1
            show_snowball_top_page(call.message.chat.id, call.message.message_id, user_id, page)

        # ---------- ПРОФИЛЬ ----------
        elif action == "profile":
            data = get_user_snowballs(user_id)
            name = call.from_user.first_name
            mention = f'<a href="tg://user?id={user_id}">{name}</a>'
            progress = get_level_progress(data["xp"], data["level"])
            rank = "Новичок" if data["level"] < 3 else "Снежный боец" if data["level"] < 6 else "Мастер снежков" if data["level"] < 9 else "Снежный король"

            text = (
                "🎄 <b>ТВОЙ СНЕЖНЫЙ ПРОФИЛЬ</b> 🎄\n\n"
                f"👤 <b>Ник:</b> {mention}\n"
                f"🎖️ <b>Звание:</b> {rank}\n"
                f"🎯 <b>Уровень:</b> {data['level']}\n"
                f"📊 <b>Прогресс:</b> {progress:.1f}%\n\n"
                f"❄️ <b>Обычных снежков:</b> <code>{data['snowballs_count']}</code>\n"
                f"🌟 <b>Золотых снежков:</b> <code>{data['golden_snowballs']}</code>\n"
                f"⭐ <b>Опыт:</b> {data['xp']} XP"
            )

            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("🏆 ТОП игроков", callback_data=f"snow_top_{user_id}_1"),
                InlineKeyboardButton("💎 Обменять", callback_data=f"snow_exchange_{user_id}")
            )
            kb.add(
                InlineKeyboardButton("🎁 Ежедневный", callback_data=f"snow_daily_{user_id}"),
                InlineKeyboardButton("📊 Статистика", callback_data=f"snow_stats_{user_id}")
            )

            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Snow callback error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# -------------------------------------------------------------
#   КОМАНДА /TOP ДЛЯ СНЕЖКОВ
# -------------------------------------------------------------
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["топ снежков", "снежный топ"])
def snow_top_command(message):
    try:
        user_id = message.from_user.id
        show_snowball_top_page(message.chat.id, None, user_id, 1)
    except Exception as e:
        logger.error(f"Snow top command error: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при загрузке топа!")

print("✅ Снежки загружены и готовы к работе!")

# ================== КОМАНДА "ЧС ЧАТА" ==================
CHAT_ACCESS_BLOCK = {}  # словарь с заблокированными чатами

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "чс чата")
def block_chat_access(message):
    user = message.from_user
    chat_id = message.chat.id
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

    # Проверка — админ ли пользователь
    if user.id not in ADMIN_IDS:
        bot.send_message(chat_id, f"{mention}\n\n<b>У тебя нет прав администратора в моей базе данных.</b>", parse_mode="HTML")
        return

    # Если уже в ЧС
    if CHAT_ACCESS_BLOCK.get(chat_id):
        bot.send_message(chat_id, f"{mention}\n\n<b>Этот чат уже находится в ЧС.</b>", parse_mode="HTML")
        return

    # Добавляем чат в ЧС
    CHAT_ACCESS_BLOCK[chat_id] = True

    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("🗨️ Убрать ЧС", callback_data=f"unblock_chat_{chat_id}"))

    bot.send_message(
        chat_id,
        f"{mention}\n\n<b>Ты убрал доступ к основным командам бота для всех пользователей в этом чате.</b>\n\n"
        "<b>Обратно выдать можно ниже:</b>",
        parse_mode="HTML",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("unblock_chat_"))
def unblock_chat(call):
    user = call.from_user
    chat_id = call.message.chat.id
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

    # Проверяем, админ ли
    if user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"{mention}\n\n<b>Ты не администратор.</b>", parse_mode="HTML")
        return

    # Снимаем блокировку
    CHAT_ACCESS_BLOCK[chat_id] = False

    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass

    bot.send_message(
        chat_id,
        f"<b>Администратор {mention} вернул доступ к боту для всех пользователей в этой группе.</b>",
        parse_mode="HTML"
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
        f"<b>⭐ {mention} Я тут!</b>",
        f"<b>🌟 {mention} Привет! Чем могу помочь?</b>",
        f"<b>💫 {mention} На связи! Готов к работе!</b>",
        f"<b>✨ {mention} Зови - отвечаю!</b>",
        f"<b>🎯 {mention} Я здесь! Команды ждут!</b>",
        f"<b>🚀 {mention} Всем привет! MEOW на связи!</b>",
        f"<b>💎 {mention} Приветствую! Чем займёмся?</b>",
        f"<b>🎰 {mention} Я готов! Выбирай игру!</b>",
        f"<b>🐾 {mention} Мяу! Я здесь!</b>",
        f"<b>👑 {mention} На месте! Что нужно?</b>",
        f"<b>🔥 {mention} Привет! Готов к приключениям!</b>",
        f"<b>💖 {mention} Здравствуй! Рад тебя видеть!</b>"
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
# ================== ГЛОБАЛЬНАЯ ПРОВЕРКА НА ЧС ==================
@bot.message_handler(func=lambda m: CHAT_ACCESS_BLOCK.get(m.chat.id))
def ignore_blocked_chat(message):
    """Если чат в ЧС — бот вообще не реагирует ни на что"""
    return




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
        f"➤ <b>БАЛАНС</b>\n\n"
        f"👤 <b>Имя:</b> {clickable}\n"
        f"💰 <b>Баланс:</b> <code>{format_number(data['balance'])}$</code>\n"
        f"🔰 <b>Префикс:</b> {prefix_display}\n"
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
        text += f"{p['name']} — <b>{format_number(p['price'])}$</b>\n"

    kb = types.InlineKeyboardMarkup()
    for p in prefixes:
        kb.add(types.InlineKeyboardButton(
            f"Купить {p['name']}",
            callback_data=f"buy_prefix_{p['id']}_{user_id}"
        ))

    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"back_to_balance_{user_id}"))

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
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"back_to_balance_{owner_id}"))

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

    text = f"💸 {mention}, префикс продан за <b>{format_number(sell_price)}$</b>!"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"back_to_balance_{owner_id}"))

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
# ТОПЫ
# ======================================================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "топ")
def top_cmd(message):
    # Быстро собираем данные
    users = []
    
    for uid_str, data in casino_data.items():
        try:
            uid = int(uid_str)
            bal = data.get("balance", 0)
            if bal > 0:  # Только те, у кого есть деньги
                users.append((uid, bal))
        except:
            continue

    # Сортируем по балансу
    users.sort(key=lambda x: x[1], reverse=True)
    
    # Берем топ 100
    top_users = users[:25]

    # Формируем текст одним блоком
    text = "🏆 <b>Топ 25 игроков:</b>\n\n<blockquote>"
    
    for i, (uid, bal) in enumerate(top_users, 1):
        try:
            # Получаем имя пользователя
            user_data = get_user_data(uid)
            first_name = user_data.get("_first_name", f"User {uid}")
            
            # Если имя не кэшировано, пробуем получить
            if first_name == f"User {uid}":
                try:
                    user = bot.get_chat(uid)
                    first_name = user.first_name
                    # Кэшируем для будущих запросов
                    user_data["_first_name"] = first_name
                    save_casino_data()
                except:
                    first_name = f"User {uid}"
            
            # Получаем префикс если есть
            up = get_user_prefix(uid)
            pref = f"{up['name']} " if up else ""
            
            text += f"{i}. {pref}<a href=\"tg://user?id={uid}\">{first_name}</a> — {format_number(bal)}$\n"
            
        except Exception as e:
            # Если ошибка - просто показываем ID
            text += f"{i}. User {uid} — {format_number(bal)}$\n"
            continue

    text += "</blockquote>"
    
    # Если топ пустой
    if not top_users:
        text = "🏆 <b>Топ игроков:</b>\n\n<blockquote>📊 Пока нет данных для топа</blockquote>"

    # Быстрая отправка
    bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)




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
        f"Если хочешь добавить меня в свой чат, <a href='{add_to_group_url}'>сюда</a> "
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
        f"Если хочешь добавить меня в свой чат, <a href='{add_to_group_url}'>сюда</a> "
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


# Данные домов (5 штук)
HOUSE_DATA = {}

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
        text += f"{rarity_info['emoji']} <b>{idx}️⃣ {info['name']}</b> — <code>{format_number(info['price'])}$</code>\n"
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
            f"Вы купили <b>{pet_info['name']}</b> за <code>{format_number(pet_info['price'])}$</code>\n"
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
            f"💰 Стоимость: <code>{format_number(price)}$</code>\n"
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
            bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {format_number(cost)}$", show_alert=True)
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
            f"💰 Стоимость: <code>{format_number(price)}$</code>\n"
            f"🍪 Сытость: <b>{satiety}%</b> ✅\n"
            f"⭐ Опыт: <b>{xp}/100</b>\n"
            f"🎯 Редкость: <i>{rarity_info['name']}</i>\n\n"
            f"💸 Потрачено на еду: <code>{format_number(cost)}$</code>"
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
        
        bot.answer_callback_query(call.id, f"🍪 Питомец накормлен! -{format_number(cost)}$")

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
            cost_text = f" - {format_number(game_info['cost'])}$" if game_info['cost'] > 0 else " - Бесплатно"
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
            bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {format_number(game_info['cost'])}$", show_alert=True)
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
            text += f"💸 Стоимость игры: <code>{format_number(game_info['cost'])}$</code>"

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
            caption=f"💸 <b>Питомец продан!</b>\n\nВы продали <b>{name}</b> и получили <code>{format_number(refund)}$</code>\n💰 Новый баланс: <code>{format_number(user_data['balance'])}$</code>",
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, f"✅ {name} продан за {format_number(refund)}$")

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
    return " ".join(f"{r}{s}" for r, s in hand)

# ================== КЛАВИАТУРА ==================
def bj_action_keyboard(user_id, game_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎴 Взять карту", callback_data=f"bj_hit_{user_id}_{game_id}"),
        InlineKeyboardButton("✋ Оставить", callback_data=f"bj_stand_{user_id}_{game_id}")
    )
    kb.add(
        InlineKeyboardButton("🏳️ Сдаться", callback_data=f"bj_surrender_{user_id}_{game_id}")
    )
    return kb

# ================== АКТИВНЫЕ ИГРЫ ==================
active_blackjack_games = {}

# ================== СТАРТ ИГРЫ ==================
def start_blackjack_game(user_data, user_id, bet):
    # Проверки
    if bet < 100:
        return None, "❌ Минимальная ставка 100$!"

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

    # ✅ СПИСЫВАЕМ ОДИН РАЗ
    user_data["balance"] -= bet
    save_casino_data()

    return game_id, "OK"

# ================== СООБЩЕНИЕ ==================
def format_blackjack_message(game_id):
    game = active_blackjack_games[game_id]
    uid = game["user_id"]

    try:
        user = bot.get_chat(uid)
        name = user.first_name
    except:
        name = str(uid)

    text = f"""
🎰 <b>Мини — игра в BLACKJACK</b>

👤 <a href="tg://user?id={uid}">{name}</a>
💰 Ставка: <code>{format_number(game['bet'])}$</code>

🎴 <b>Дилер:</b>
{format_hand(game['dealer_hand'], game['status']=="playing")}
📊 {hand_value([game['dealer_hand'][0]]) if game['status']=="playing" else game['dealer_value']}

🃏 <b>Ты:</b>
{format_hand(game['player_hand'])}
📊 {game['player_value']}

🎯 <b>Статус:</b>
"""

    status_map = {
        "playing": "Твой ход",
        "blackjack": "🎯 BLACKJACK!",
        "bust": "💥 ПЕРЕБОР",
        "win": "✅ ПОБЕДА",
        "lose": "❌ ПОРАЖЕНИЕ",
        "push": "🤝 НИЧЬЯ",
        "surrender": "🏳️ СДАЧА"
    }

    text += status_map.get(game["status"], "")

    if game["status"] in ["win", "blackjack"]:
        mult = 2.5 if game["status"] == "blackjack" else 2
        text += f"\n\n💰 Выигрыш: <code>{format_number(int(game['bet'] * mult))}$</code>"

    if game["status"] == "push":
        text += f"\n\n💰 Возврат: <code>{format_number(game['bet'])}$</code>"

    if game["status"] == "surrender":
        text += f"\n\n💰 Возврат: <code>{format_number(game['bet']//2)}$</code>"

    return text

# ================== CALLBACK ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith("bj_"))
def handle_blackjack_action(call):
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

        dealer_turn(gid)
        complete_blackjack_game(gid)

    bot.edit_message_text(
        format_blackjack_message(gid),
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=bj_action_keyboard(uid, gid) if game["status"] == "playing" else None
    )

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

# ================== НОВАЯ КОМАНДА: ИГРАТЬ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("играть"))
def play_blackjack_command(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)  # ОДИН РАЗ

        parts = message.text.split()

        # Если ставка не указана — показать помощь
        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "🎰 <b>Игра в Blackjack</b>\n\n"
                "📝 <b>Использование:</b>\n"
                "<code>играть [ставка]</code>\n\n"
                "📊 <b>Примеры:</b>\n"
                "<code>играть 1000</code>\n"
                "<code>играть 5000</code>\n\n"
                "💰 <b>Минимальная ставка:</b> 100$\n"
                f"💵 <b>Твой баланс:</b> {format_number(user_data['balance'])}$",
                parse_mode="HTML"
            )
            return

        # Парсим ставку
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

        # Минимальная ставка
        if bet < 100:
            bot.send_message(
                message.chat.id,
                "❌ <b>Ошибка!</b>\nМинимальная ставка 100$!",
                parse_mode="HTML"
            )
            return

        # ❗ НЕ проверяем баланс здесь
        # ❗ НЕ списываем деньги здесь
        # Всё это делает start_blackjack_game()

        # ✅ ПРАВИЛЬНЫЙ ВЫЗОВ: передаем user_data и user_id
        game_id, result = start_blackjack_game(user_data, user_id, bet)

        if game_id is None:
            bot.send_message(message.chat.id, result, parse_mode="HTML")
            return

        # Отправляем игру
        text = format_blackjack_message(game_id)
        kb = bj_action_keyboard(user_id, game_id)

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=kb
        )

    except Exception as e:
        logger.error(f"Ошибка в команде 'играть': {e}")
        bot.send_message(
            message.chat.id,
            "❌ <b>Ошибка при запуске игры!</b>\nПопробуйте позже.",
            parse_mode="HTML"
        )


# ================== 🎡 РУЛЕТКА (СТАБИЛЬНАЯ ВЕРСИЯ) ==================
import random
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Глобальный словарь для активных игр
ACTIVE_GAMES = {}
GAME_TIMEOUT = 300  # 5 минут в секундах

# Константы для игры
ROULETTE_TYPES = {
    "red": {"name": "🔴 Красное", "emoji": "🔴", "multiplier": 2},
    "black": {"name": "⚫ Чёрное", "emoji": "⚫", "multiplier": 2},
    "even": {"name": "🔢 Чётное", "emoji": "🔢", "multiplier": 2},
    "odd": {"name": "🔣 Нечётное", "emoji": "🔣", "multiplier": 2},
    "green": {"name": "🟢 Зелёное", "emoji": "🟢", "multiplier": 36}
}

def format_number(num):
    """Форматирование чисел с разделителями"""
    return f"{num:,}".replace(",", " ")

def cleanup_old_games():
    """Очистка старых игр - вызывается перед каждой операцией"""
    global ACTIVE_GAMES
    current_time = time.time()
    games_to_remove = []
    
    for game_id, game_data in ACTIVE_GAMES.items():
        game_age = current_time - game_data.get("start_time", 0)
        if game_age > GAME_TIMEOUT:
            games_to_remove.append(game_id)
    
    for game_id in games_to_remove:
        try:
            # Возвращаем средства только если игра была на стадии выбора
            game_data = ACTIVE_GAMES[game_id]
            if game_data.get("stage") == "choice":
                user_id = game_data["user_id"]
                user_data = get_user_data(user_id)
                bet = game_data.get("bet", 0)
                if bet > 0:
                    user_data["balance"] += bet
                    save_casino_data()
        except:
            pass
        
        del ACTIVE_GAMES[game_id]
    
    return len(games_to_remove)

def get_roulette_keyboard():
    """Возвращает клавиатуру для рулетки"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    keyboard.row(
        InlineKeyboardButton("🔴 Красное", callback_data="roulette_red"),
        InlineKeyboardButton("⚫ Чёрное", callback_data="roulette_black"),
        InlineKeyboardButton("🟢 Зелёное", callback_data="roulette_green")
    )
    
    keyboard.row(
        InlineKeyboardButton("🔢 Чётное", callback_data="roulette_even"),
        InlineKeyboardButton("🔣 Нечётное", callback_data="roulette_odd")
    )
    
    return keyboard

def spin_roulette():
    """Крутит рулетку и возвращает результат"""
    number = random.randint(0, 36)
    
    if number == 0:
        color = "зеленое"
    elif number % 2 == 0:
        color = "черное"
    else:
        color = "красное"
    
    return number, color

def check_win(choice, number, color):
    """Проверяет, выиграл ли игрок"""
    if choice == "green":
        return number == 0
    elif choice == "red":
        return color == "красное" and number != 0
    elif choice == "black":
        return color == "черное" and number != 0
    elif choice == "even":
        return number % 2 == 0 and number != 0
    elif choice == "odd":
        return number % 2 == 1
    return False

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(("рулетка ", "рулетка")))
def handle_roulette_command(message):
    """Обработчик команды /рулетка"""
    try:
        user_id = message.from_user.id
        username = message.from_user.first_name
        
        # Очищаем старые игры ПЕРЕД началом
        cleanup_old_games()
        
        # Получаем ставку из сообщения
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.send_message(
                message.chat.id,
                "🎰 <b>ИГРА В РУЛЕТКУ</b>\n\n"
                "Используйте: <code>рулетка [ставка]</code>\n"
                "Пример: <code>рулетка 1000</code>\n\n"
                "Минимальная ставка: <b>100$</b>",
                parse_mode="HTML"
            )
            return
        
        try:
            bet = int(command_parts[1])
        except ValueError:
            bot.send_message(message.chat.id, "❌ Неверный формат ставки! Используйте числа.")
            return
        
        # Проверка минимальной ставки
        if bet < 100:
            bot.send_message(message.chat.id, "❌ Минимальная ставка: 100$")
            return
        
        # Проверка максимальной ставки
        if bet > 100000000:
            bot.send_message(message.chat.id, "❌ Максимальная ставка: 100.000.000$")
            return
        
        # Проверка баланса
        user_data = get_user_data(user_id)
        if user_data["balance"] < bet:
            bot.send_message(
                message.chat.id,
                f"❌ <b>НЕДОСТАТОЧНО СРЕДСТВ!</b>\n\n"
                f"💰 Нужно: <b>{format_number(bet)}$</b>\n"
                f"💳 У вас: <b>{format_number(user_data['balance'])}$</b>",
                parse_mode="HTML"
            )
            return
        
        # Проверяем, нет ли уже активной игры
        game_id = f"{user_id}_{message.chat.id}"
        if game_id in ACTIVE_GAMES:
            # Проверяем возраст игры
            game_data = ACTIVE_GAMES[game_id]
            game_age = time.time() - game_data.get("start_time", 0)
            if game_age > 60:  # Если игра старше 60 секунд, удаляем её
                del ACTIVE_GAMES[game_id]
            else:
                bot.send_message(message.chat.id, "❌ У вас уже есть активная игра! Дождитесь окончания.")
                return
        
        # Снимаем ставку
        user_data["balance"] -= bet
        save_casino_data()
        
        # Отправляем начальное сообщение
        mention = f'<a href="tg://user?id={user_id}">{username}</a>'
        msg = bot.send_photo(
            message.chat.id,
            photo=CASINO_IMAGE_URL,
            caption=(
                f"🎡 <b>РУЛЕТКА</b>\n\n"
                f"👤 Игрок: {mention}\n"
                f"💰 Ставка: <b>{format_number(bet)}$</b>\n\n"
                f"🎯 <b>Выберите вариант:</b>"
            ),
            parse_mode="HTML",
            reply_markup=get_roulette_keyboard()
        )
        
        # Создаем новую игру
        ACTIVE_GAMES[game_id] = {
            "user_id": user_id,
            "bet": bet,
            "chat_id": message.chat.id,
            "message_id": msg.message_id,
            "stage": "choice",  # choice, processing
            "choice": None,
            "start_time": time.time()
        }
        
    except Exception as e:
        logger.error(f"Ошибка в команде рулетки: {e}", exc_info=True)
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при начале игры. Попробуйте позже."
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("roulette_"))
def handle_roulette_callback(call):
    """Обработчик нажатий на кнопки рулетки"""
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # Очищаем старые игры перед обработкой
        cleanup_old_games()
        
        # Проверяем активную игру
        game_id = f"{user_id}_{chat_id}"
        
        if game_id not in ACTIVE_GAMES:
            bot.answer_callback_query(call.id, "❌ Игра не найдена или завершена!")
            return
        
        game_data = ACTIVE_GAMES[game_id]
        
        # Проверяем, что это сообщение от этой игры
        if game_data["message_id"] != message_id:
            bot.answer_callback_query(call.id, "❌ Это не ваша текущая игра!")
            return
        
        # Проверяем этап игры
        if game_data["stage"] != "choice":
            bot.answer_callback_query(call.id, "❌ Вы уже сделали выбор!")
            return
        
        # Получаем выбор игрока
        choice = call.data.replace("roulette_", "")
        
        if choice not in ROULETTE_TYPES:
            bot.answer_callback_query(call.id, "❌ Неверный выбор!")
            return
        
        # Обновляем игру
        game_data["stage"] = "processing"
        game_data["choice"] = choice
        
        # Получаем информацию о выборе
        choice_info = ROULETTE_TYPES[choice]
        
        # Обновляем сообщение - убираем кнопки
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        
        bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=(
                f"🎡 <b>РУЛЕТКА</b>\n\n"
                f"👤 Игрок: {mention}\n"
                f"💰 Ставка: <b>{format_number(game_data['bet'])}$</b>\n"
                f"🎯 Выбор: <b>{choice_info['name']}</b>\n\n"
                f"🔄 <b>Крутим рулетку...</b>"
            ),
            parse_mode="HTML",
            reply_markup=None
        )
        
        # Короткая анимация (без sleep чтобы не блокировать)
        time.sleep(0.5)
        
        # Крутим рулетку
        number, color = spin_roulette()
        
        # Проверяем выигрыш
        win = check_win(choice, number, color)
        
        # Обрабатываем результат
        user_data = get_user_data(user_id)
        bet = game_data["bet"]
        multiplier = ROULETTE_TYPES[choice]["multiplier"]
        
        if win:
            win_amount = bet * multiplier
            user_data["balance"] += win_amount
            result_text = f"✅ ПОБЕДА! x{multiplier}"
            result_emoji = "🎉"
        else:
            win_amount = 0
            result_text = "❌ ПРОИГРЫШ"
            result_emoji = "💸"
        
        # Сохраняем изменения баланса
        save_casino_data()
        
        # Получаем эмодзи для цвета
        if color == "зеленое":
            color_emoji = "🟢"
        elif color == "красное":
            color_emoji = "🔴"
        else:
            color_emoji = "⚫"
        
        # Формируем финальное сообщение
        final_caption = (
            f"🎡 <b>РУЛЕТКА — РЕЗУЛЬТАТ</b>\n\n"
            f"👤 Игрок: {mention}\n"
            f"💰 Ставка: <b>{format_number(bet)}$</b>\n"
            f"🎯 Выбор: <b>{choice_info['name']}</b>\n\n"
            f"🎲 Выпало: <b>{number} {color_emoji}</b>\n\n"
            f"{result_emoji} <b>{result_text}</b>\n"
        )
        
        if win:
            final_caption += f"💵 Выигрыш: <b>{format_number(win_amount)}$</b>\n\n"
        else:
            final_caption += f"💸 Потеря: <b>{format_number(bet)}$</b>\n\n"
        
        final_caption += f"💰 Баланс: <b>{format_number(user_data['balance'])}$</b>"
        
        # Удаляем игру из активных ПЕРЕД показом результата
        if game_id in ACTIVE_GAMES:
            del ACTIVE_GAMES[game_id]
        
        # Обновляем сообщение с результатом
        bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=final_caption,
            parse_mode="HTML",
            reply_markup=None  # Нет кнопок "Играть снова" и "Баланс"
        )
        
        # Отвечаем на callback
        bot.answer_callback_query(call.id, result_text)
        
    except Exception as e:
        logger.error(f"Ошибка в обработке рулетки: {e}", exc_info=True)
        
        try:
            # Пытаемся вернуть средства при ошибке
            user_id = call.from_user.id
            chat_id = call.message.chat.id
            game_id = f"{user_id}_{chat_id}"
            
            if game_id in ACTIVE_GAMES:
                game_data = ACTIVE_GAMES[game_id]
                user_data = get_user_data(user_id)
                
                # Возвращаем ставку только если игра на стадии choice
                if game_data.get("stage") == "choice":
                    user_data["balance"] += game_data.get("bet", 0)
                    save_casino_data()
                
                # Удаляем игру
                del ACTIVE_GAMES[game_id]
                
                # Сообщаем об ошибке
                bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    caption=(
                        "❌ <b>ОШИБКА В ИГРЕ</b>\n\n"
                        "Произошла техническая ошибка.\n\n"
                        "Попробуйте начать игру заново."
                    ),
                    parse_mode="HTML"
                )
        except Exception as inner_e:
            logger.error(f"Ошибка при возврате средств: {inner_e}")
        
        bot.answer_callback_query(call.id, "❌ Ошибка в игре!")

def auto_cleanup_games():
    """Автоматическая очистка старых игр каждую минуту"""
    while True:
        try:
            removed = cleanup_old_games()
            if removed > 0:
                logger.info(f"Автоочистка: удалено {removed} старых игр")
        except Exception as e:
            logger.error(f"Ошибка в автоочистке: {e}")
        
        time.sleep(60)  # 1 минута

# Запускаем фоновую очистку в отдельном потоке
cleanup_thread = threading.Thread(target=auto_cleanup_games, daemon=True)
cleanup_thread.start()

print("✅ Модуль рулетки загружен и готов к работе!")
    
    
# ================== ИГРА В РУЛЕТКУ (CASINO ROULETTE) ==================

# Глобальные переменные для хранения ставок
color_bets = {}     # Для ставок на цвета
number_bets = {}    # Для ставок на числа

def log_roulette(chat_id, result_number, result_color):
    """Логирование результатов рулетки"""
    logger.info(f"Рулетка в чате {chat_id}: выпало {result_number} ({result_color})")
    
    # Сохраняем в отдельный файл для команды лог
    try:
        with open("roulette_results.txt", "a", encoding="utf-8") as f:
            f.write(f"{result_number}|{result_color}\n")
    except Exception as e:
        logger.error(f"Ошибка сохранения лога рулетки: {e}")

# ================== ОБРАБОТКА СТАВОК НА ЦВЕТ ==================

@bot.message_handler(func=lambda m: m.text and m.text.split()[0].isdigit() and len(m.text.split()) == 2 and m.text.split()[1] in ['к', 'ч'])
def place_color_bet(message):
    """Ставка на цвет (красное/черное)"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Получаем пользователя с кликабельной ссылкой
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        parts = message.text.split()
        bet = int(parts[0])
        color = parts[1]
        
        if bet <= 0:
            bot.send_message(chat_id, f"❌ {mention}, укажите корректную ставку!", parse_mode="HTML")
            return
        
        # Проверяем баланс
        user_data = get_user_data(user_id)
        if user_data["balance"] < bet:
            bot.send_message(chat_id, f"❌ {mention}, недостаточно средств!\nВаш баланс: <code>{format_number(user_data['balance'])}$</code>", parse_mode="HTML")
            return
        
        # Проверяем, нет ли уже ставки на противоположный цвет
        if chat_id in color_bets and user_id in color_bets[chat_id]:
            existing_bet, existing_color, _ = color_bets[chat_id][user_id]
            if existing_color != color:
                opposite_color_emoji = '⚫' if color == 'к' else '🔴'
                bot.send_message(chat_id, f"❌ {mention}, вы уже поставили на {opposite_color_emoji}! Нельзя ставить на оба цвета.", parse_mode="HTML")
                return
        
        # Списываем ставку
        user_data["balance"] -= bet
        save_casino_data()
        
        color_emoji = '🔴' if color == 'к' else '⚫'
        
        # Сохраняем ставку
        if chat_id not in color_bets:
            color_bets[chat_id] = {}
        color_bets[chat_id][user_id] = (bet, color, mention)
        
        bot.send_message(chat_id, f"✅ {mention}, ваша ставка <code>{format_number(bet)}$</code> на {color_emoji} принята!\n\nНапишите <code>го</code> чтобы запустить рулетку.", parse_mode="HTML")
        
        logger.info(f"Ставка на цвет от {user_id}: {bet}$ на {color_emoji}")
        
    except Exception as e:
        logger.error(f"Ошибка ставки на цвет: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при размещении ставки!")

# ================== ОБРАБОТКА СТАВОК НА ЧИСЛА ==================

@bot.message_handler(func=lambda m: m.text and m.text.split()[0].isdigit() and len(m.text.split()) >= 2 and all(part.isdigit() or part == m.text.split()[0] for part in m.text.split()))
def place_number_bet(message):
    """Ставка на числа"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Получаем пользователя с кликабельной ссылкой
        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
        
        parts = message.text.split()
        bet = int(parts[0])
        
        if bet <= 0:
            bot.send_message(chat_id, f"❌ {mention}, укажите корректную ставку!", parse_mode="HTML")
            return
        
        # Извлекаем числа (уникальные)
        chosen_numbers = list(set([int(num) for num in parts[1:] if num.isdigit()]))
        
        # Проверки
        if not chosen_numbers or len(chosen_numbers) > 16:
            bot.send_message(chat_id, f"❌ {mention}, За одну ставку можно ставить только до 16 числ!", parse_mode="HTML")
            return
        
        if any(num < 0 or num > 36 for num in chosen_numbers):
            bot.send_message(chat_id, f"❌ {mention}, числа должны быть от 0 до 36!", parse_mode="HTML")
            return
        
        total_bet = bet * len(chosen_numbers)
        
        # Проверяем баланс
        user_data = get_user_data(user_id)
        if user_data["balance"] < total_bet:
            bot.send_message(chat_id, f"❌ {mention}, недостаточно средств!\nНужно: <code>{format_number(total_bet)}$</code>\nВаш баланс: <code>{format_number(user_data['balance'])}$</code>", parse_mode="HTML")
            return
        
        # Списываем ставку
        user_data["balance"] -= total_bet
        save_casino_data()
        
        # Сохраняем ставку
        if chat_id not in number_bets:
            number_bets[chat_id] = {}
        if user_id not in number_bets[chat_id]:
            number_bets[chat_id][user_id] = []
        
        number_bets[chat_id][user_id].append((bet, chosen_numbers, mention))
        
        # Формируем ответ
        numbers_str = ', '.join(map(str, chosen_numbers))
        bot.send_message(chat_id, f"✅ {mention}, ставка принята!\n• Ставка на число: <code>{format_number(bet)}$</code>\n• Числа: <b>{numbers_str}</b>\n• Всего ставка: <code>{format_number(total_bet)}$</code>\n\nНапишите <code>го</code> чтобы запустить рулетку.", parse_mode="HTML")
        
        logger.info(f"Ставка на числа от {user_id}: {bet}$ на {chosen_numbers} (всего: {total_bet}$)")
        
    except Exception as e:
        logger.error(f"Ошибка ставки на числа: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при размещении ставки!")

# ================== ЗАПУСК РУЛЕТКИ (ГО) ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'го')
def start_roulette(message):
    """Запуск рулетки"""
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Проверяем, есть ли ставки
        has_color_bets = chat_id in color_bets and color_bets[chat_id]
        has_number_bets = chat_id in number_bets and number_bets[chat_id]
        
        if not has_color_bets and not has_number_bets:
            bot.send_message(chat_id, "❌ Нет ставок для запуска! Сначала сделайте ставку.")
            return
        
        # Анимация кручения рулетки
        spinning_msg = bot.send_message(chat_id, "🎲 Рулетка крутится...")
        time.sleep(1)
        
        # Генерируем результат
        if random.random() < 0.027:  # 2.7% шанс на 0 (зеленое)
            result_number = 0
            result_color = 'з'
            result_color_emoji = '🟩'
        else:
            result_number = random.randint(1, 36)
            result_color = 'ч' if result_number % 2 == 0 else 'к'
            result_color_emoji = '⚫' if result_color == 'ч' else '🔴'
        
        # Удаляем сообщение с анимацией
        try:
            bot.delete_message(chat_id, spinning_msg.message_id)
        except:
            pass
        
        # Начинаем формировать результат
        result_text = f"🎰 <b>РЕЗУЛЬТАТЫ РУЛЕТКИ</b> 🎰\n\n"
        result_text += f"🎲 Выпало: <b>{result_number}</b> {result_color_emoji}\n\n"
        
        # Обрабатываем ставки на цвета
        if has_color_bets:
            result_text += "🎯 <b>Красное/Черное:</b>\n"
            for player_id, (bet, color, mention) in color_bets[chat_id].items():
                player_data = get_user_data(player_id)
                color_emoji = '🔴' if color == 'к' else '⚫'
                
                if result_color == color:
                    winnings = bet * 2
                    player_data["balance"] += winnings
                    result_text += f"✅ {mention} ({color_emoji}): +<code>{format_number(winnings)}$</code> (Выигрыш x2)\n"
                else:
                    result_text += f"❌ {mention} ({color_emoji}): -<code>{format_number(bet)}$</code>\n"
                
                save_casino_data()
            
            # Очищаем ставки на цвета
            del color_bets[chat_id]
        
        # Обрабатываем ставки на числа
        if has_number_bets:
            result_text += "\n🎯 <b>Ставки на числа:</b>\n"
            for player_id, bets_list in number_bets[chat_id].items():
                player_data = get_user_data(player_id)
                
                for bet, numbers, mention in bets_list:
                    numbers_str = ', '.join(map(str, numbers))
                    total_bet = bet * len(numbers)
                    
                    if result_number in numbers:
                        winnings = bet * 36
                        player_data["balance"] += winnings
                        result_text += f"🎉 {mention} ({numbers_str}): +<code>{format_number(winnings)}$</code> (Джекпот x36!)\n"
                    else:
                        result_text += f"❌ {mention} ({numbers_str}): -<code>{format_number(total_bet)}$</code>\n"
                    
                    save_casino_data()
            
            # Очищаем ставки на числа
            del number_bets[chat_id]
        
        # Отправляем результаты
        bot.send_message(chat_id, result_text, parse_mode="HTML")
        log_roulette(chat_id, result_number, result_color)
        
    except Exception as e:
        logger.error(f"Ошибка запуска рулетки: {e}")
        bot.send_message(message.chat.id, "❌ Команда была отклонена, возможная причина: Игра ранее была запущена другим игроком")

# ================== КОМАНДА ЛОГИ РУЛЕТКИ ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["лог", "логи"])
def show_roulette_logs(message):
    """Показать последние 10 результатов рулетки"""
    try:
        if not os.path.exists("roulette_results.txt"):
            bot.reply_to(message, "❗ Сегодня ещё никто не играл в рулетку - логи пустые")
            return
        
        with open("roulette_results.txt", "r", encoding="utf-8") as f:
            logs = f.readlines()
        
        # Берем последние 10 строк
        recent_logs = logs[-10:] if len(logs) >= 10 else logs
        
        if not recent_logs:
            bot.reply_to(message, "❗ Сегодня ещё никто не играл в рулетку - логи пустые")
            return
        
        # Переворачиваем чтобы новые были сверху
        recent_logs.reverse()
        
        text = "📝 <b>Логи:</b>\n\n"
        
        for log in recent_logs:
            log = log.strip()
            if "|" in log:
                # Формат: число|цвет
                parts = log.split("|")
                if len(parts) >= 2:
                    number = parts[0]
                    color = parts[1]
                    
                    if color == 'з':
                        emoji = '🟩'
                    elif color == 'к':
                        emoji = '🔴'
                    elif color == 'ч':
                        emoji = '⚫'
                    else:
                        continue
                    
                    text += f"{emoji} ({number})\n"
        
        bot.reply_to(message, text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка показа логов рулетки: {e}")
        bot.reply_to(message, "❌ Ошибка при получении логов!")
        
# ================== ФУТБОЛ / БАСКЕТБОЛ ==================

@bot.message_handler(func=lambda m: m.text and (
    m.text.lower().startswith("футбол") or
    m.text.lower().startswith(("баскет", "бс", "баскетбол"))
))
def game_sport(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Пример: футбол 500")
            return

        cmd = parts[0].lower()
        bet = int(parts[1])
        uid = message.from_user.id

        user = get_user_data(uid)

        if bet <= 0:
            bot.send_message(message.chat.id, "❌ ставка > 0")
            return
        
        if user["balance"] < bet:
            bot.send_message(message.chat.id, "❌ недостаточно средств!")
            return

        user["balance"] -= bet
        save_casino_data()

        game_name = "⚽ Футбол" if cmd.startswith("футбол") else "🏀 Баскетбол"

        mention = f"<a href='tg://user?id={uid}'>{message.from_user.first_name}</a>"

        msg = bot.send_message(
            message.chat.id,
            f"{mention}, результат твоей игры через:\n<b>1...</b>",
            parse_mode="HTML"
        )

        threading.Thread(target=sport_countdown_simple, args=(uid, bet, msg.message_id, message.chat.id, game_name)).start()

    except:
        pass


def sport_countdown_simple(uid, bet, mid, chat_id, game):
    try:
        # 2
        time.sleep(1)
        bot.edit_message_text(
            f"⏳ {game}\n\n<b>2...</b>",
            chat_id,
            mid,
            parse_mode="HTML"
        )

        # 3
        time.sleep(1)
        bot.edit_message_text(
            f"⏳ {game}\n\n<b>3...</b>",
            chat_id,
            mid,
            parse_mode="HTML"
        )

        # wait
        time.sleep(1)

        user = get_user_data(uid)

        win = random.randint(1,100) <= 38

        mention = f"<a href='tg://user?id={uid}'>{user['name'] if 'name' in user else 'Игрок'}</a>"

        if win:
            win_amount = bet * 2
            user["balance"] += win_amount
            save_casino_data()

            bot.edit_message_text(
                f"{mention}, ты сыграл в {game}!\n\n"
                f"🎉 Победа!\n"
                f"💰 Выигрыш: <b>{format_number(win_amount)}$</b>",
                chat_id,
                mid,
                parse_mode="HTML"
            )
        else:
            bot.edit_message_text(
                f"{mention}, игра {game} завершена.\n\n"
                f"❌ Промах!\n"
                f"💸 Потеря: <b>{format_number(bet)}$</b>",
                chat_id,
                mid,
                parse_mode="HTML"
            )

    except:
        pass

# ================== MINES 5x5 ==================
config = {
    "mines_count": 5,
    "mines_multiplier_increment": 0.1
}

def start_mines(user_id, bet):
    u = get_user_data(user_id)
    if u["balance"] < bet:
        return False

    u["balance"] -= bet  
    u.update({  
        "game": "mines",  
        "stage": "mines",  
        "mines_owner": user_id,  
        "mines_bet": bet,  
        "mines_positions": random.sample(range(25), config["mines_count"]),  
        "mines_open": [],  
        "mines_multiplier": 1.0,  
        "mines_started": False  
    })  
    save_casino_data()  
    return True

def mines_keyboard(user_id, reveal_all=False, hide_buttons=False):
    u = get_user_data(user_id)
    kb = InlineKeyboardMarkup()

    btns = []  
    for i in range(25):  
        if reveal_all:  
            text = " 💣 " if i in u["mines_positions"] else " "  
        else:  
            text = "       " if i in u["mines_open"] else " ❓ "  

        btns.append(  
            InlineKeyboardButton(  
                f" {text} ",  
                callback_data=f"mines_{i}_{user_id}"  
            )  
        )  

    for i in range(0, 25, 5):  
        kb.row(*btns[i:i + 5])  

    # ЕСЛИ hide_buttons=True - НЕ ДОБАВЛЯЕМ КНОПКИ ДЕЙСТВИЙ
    if not hide_buttons:
        if not u["mines_started"]:  
            kb.row(  
                InlineKeyboardButton(" ❌ ", callback_data=f"mines_cancel_{user_id}")  
            )  
        else:  
            kb.row(  
                InlineKeyboardButton(" 💸 Забрать выигрыш", callback_data=f"mines_cash_{user_id}")  
            )  

    return kb

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("мины "))
def mines_command(message):
    user_id = message.from_user.id
    parts = message.text.split()
    
    if len(parts) < 2:
        return
    
    try:
        bet = int(parts[1])
        if bet < 50:
            bot.reply_to(message, "❌ Мин. ставка: 50$")
            return
            
        u = get_user_data(user_id)
        
        if bet > u["balance"]:
            bot.reply_to(message, "❌ Недостаточно средств!")
            return
        
        if start_mines(user_id, bet):
            mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'
            bot.send_message(
                message.chat.id,
                f"🎮 {mention} начал игру в мины!\n"
                f"💰 Ставка: {format_number(bet)}$\n"
                f"💣 Мин: {config['mines_count']}\n"
                f"🎯 Множитель: x1.0",
                parse_mode="HTML",
                reply_markup=mines_keyboard(user_id)
            )
        else:
            bot.reply_to(message, "❌ Ошибка начала игры!")
            
    except ValueError:
        bot.reply_to(message, "❌ Ставка должна быть числом!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("mines_"))
def mines_handler(call):
    parts = call.data.split("_")
    action = parts[1]
    owner_id = int(parts[2])
    user_id = call.from_user.id

    if user_id != owner_id:  
        bot.answer_callback_query(call.id, "НЕ ТВОЯ ИГРА", show_alert=True)  
        return  

    u = get_user_data(user_id)  
    if u.get("stage") != "mines":  
        bot.answer_callback_query(call.id, "ИГРА ЗАКОНЧЕНА")  
        return  

    # ❌ ОТМЕНА  
    if action == "cancel" and not u["mines_started"]:  
        u["balance"] += u["mines_bet"]  
        u["stage"] = "finished"  
        save_casino_data()  

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'  
        bot.edit_message_text(  
            f"{mention}, игра отменена.",  
            call.message.chat.id,  
            call.message.message_id,  
            parse_mode="HTML",  
            reply_markup=mines_keyboard(user_id, reveal_all=True, hide_buttons=True)
        )  
        return  

    # 💸 ЗАБРАТЬ ВЫИГРЫШ  
    if action == "cash" and u["mines_started"]:  
        win = int(u["mines_bet"] * u["mines_multiplier"])  
        
        user_game_data = get_user_data(user_id)
        user_game_data["balance"] += win
        save_casino_data()
        
        u["stage"] = "finished"  
        save_casino_data()  

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'  
        bot.edit_message_text(  
            f"{mention}, ты забрал выигрыш <b>{format_number(win)}$</b>\n"
            f"💰 Новый баланс: <b>{format_number(user_game_data['balance'])}$</b>",  
            call.message.chat.id,  
            call.message.message_id,  
            parse_mode="HTML",  
            reply_markup=mines_keyboard(user_id, reveal_all=True, hide_buttons=True)
        )  
        return  

    # 🧩 КЛЕТКА  
    cell = int(action)  
    if cell in u["mines_open"]:  
        bot.answer_callback_query(call.id)  
        return  

    u["mines_open"].append(cell)  
    u["mines_started"] = True  

    # 💥 МИНА  
    if cell in u["mines_positions"]:  
        u["stage"] = "finished"  
        save_casino_data()  

        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'  
        bot.edit_message_text(  
            f"{mention}, ты подорвался на мине 💥\n"
            f"❌ Ставка {format_number(u['mines_bet'])}$ потеряна!",  
            call.message.chat.id,  
            call.message.message_id,  
            parse_mode="HTML",  
            reply_markup=mines_keyboard(user_id, reveal_all=True, hide_buttons=True)
        )  
        return  

    # ✅ БЕЗОПАСНО  
    u["mines_multiplier"] += config["mines_multiplier_increment"]  
    save_casino_data()  

    bot.edit_message_reply_markup(  
        call.message.chat.id,  
        call.message.message_id,  
        reply_markup=mines_keyboard(user_id)  
    )  

    bot.answer_callback_query(call.id)
    
# ================== КОМАНДЫ "ПОМОЩЬ" И "/help" ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["помощь", "/help@meow_gamechat_bot", "/help"])
def cmd_pomosh(message):
    user = message.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    text = (
        "📖 <b>ПАНЕЛЬ ПОМОЩИ</b>\n"
        f"👤 <b>Пользователь:</b> {mention}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
        "Выберите раздел:"
    )

    # Страница 1: первые 3 кнопки
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Команды", callback_data="help_page_1"))
    kb.add(InlineKeyboardButton("Игры", callback_data="help_games"))
    kb.add(InlineKeyboardButton("VIP", callback_data="help_vip"))
    # Только вперед
    kb.add(InlineKeyboardButton(" > ", callback_data="help_next_page_2"))

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb,
        parse_mode="HTML"
    )


# ================== ПАГИНАЦИЯ КНОПОК ПОМОЩИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("help_next_page_") or c.data.startswith("help_prev_page_"))
def callback_help_pagination(call):
    try:
        if call.data.startswith("help_next_page_"):
            page_num = int(call.data.split("_")[3])
            show_help_page(call, page_num)
        elif call.data.startswith("help_prev_page_"):
            page_num = int(call.data.split("_")[3])
            show_help_page(call, page_num)
            
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка в пагинации помощи: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!")


def show_help_page(call, page_num):
    """Показывает конкретную страницу с кнопками помощи"""
    user = call.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    
    text = (
        "📖 <b>ПАНЕЛЬ ПОМОЩИ</b>\n"
        f"👤 <b>Пользователь:</b> {mention}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
        "Выберите раздел:"
    )
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    if page_num == 1:
        # Страница 1: первые 3 кнопки
        kb.add(InlineKeyboardButton("Команды", callback_data="help_page_1"))
        kb.add(InlineKeyboardButton("Игры", callback_data="help_games"))
        kb.add(InlineKeyboardButton("VIP", callback_data="help_vip"))
        # Только вперед
        kb.add(InlineKeyboardButton(" > ", callback_data="help_next_page_2"))
        
    elif page_num == 2:
        # Страница 2: следующие 3 кнопки
        kb.add(InlineKeyboardButton("Тянки", callback_data="help_tyanki"))
        kb.add(InlineKeyboardButton("Питомцы", callback_data="help_pets"))
        kb.add(InlineKeyboardButton("Брак", callback_data="help_marriage"))
        # Назад и вперед
        kb.row(
            InlineKeyboardButton(" < ", callback_data="help_prev_page_1"),
            InlineKeyboardButton(" > ", callback_data="help_next_page_3")
        )
        
    elif page_num == 3:
        # Страница 3: следующие 3 кнопки
        kb.add(InlineKeyboardButton("Ивенты", callback_data="help_snow"))
        kb.add(InlineKeyboardButton("Донат", callback_data="help_donate"))
        kb.add(InlineKeyboardButton("Поддержка", callback_data="help_support"))
        # Назад и вперед
        kb.row(
            InlineKeyboardButton(" < ", callback_data="help_prev_page_2"),
            InlineKeyboardButton(" > ", callback_data="help_next_page_4")
        )
        
    elif page_num == 4:
        # Страница 4: последние кнопки
        kb.add(InlineKeyboardButton("Канал", url="https://t.me/meow_newsbot"))
        # Только назад
        kb.add(InlineKeyboardButton(" < ", callback_data="help_prev_page_3"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
        parse_mode="HTML"
    )


# ================== ПАГИНАЦИЯ КОМАНД ==================
COMMANDS_PAGES = [
    {
        "title": "📋 <b>КОМАНДЫ - СТРАНИЦА 1/3</b>\n━━━━━━━━━━━━━━━━━",
        "content": """<b>ОСНОВНЫЕ КОМАНДЫ:</b>

<code>моя шахта</code> — главная меню твоей шахты
<code>копать</code> — копать руду в шахте, альтернативная команда: копать шахту
<code>/help</code> — помощь
<code>баланс</code> — баланс
<code>топ</code> — топ игроков
<code>бонус</code> — ежедневный бонус
<code>ферма</code> — фарм валюты
<code>бот</code> — позвать бота

<b>ПРАВИЛА:</b>
<code>правила</code> — правила чата

━━━━━━━━━━━━━━━━━"""
    },
    {
        "title": "📋 <b>КОМАНДЫ - СТРАНИЦА 2/3</b>\n━━━━━━━━━━━━━━━━━",
        "content": """<b>ЭКОНОМИКА:</b>

<code>п [ID] [сумма]</code> — перевод
<code>промо [код]</code> — промокод
<code>задонатить [сумма]</code> — пополнить
<code>мой кабинет</code> — реферальная система

<b>ВЗАИМОДЕЙСТВИЯ:</b>
<code>рп</code> — список RP-команд
<code>обнять</code>, <code>поцеловать</code> — RP команды

━━━━━━━━━━━━━━━━━"""
    },
    {
        "title": "📋 <b>КОМАНДЫ - СТРАНИЦА 3/3</b>\n━━━━━━━━━━━━━━━━━",
        "content": """<b>МАГАЗИНЫ:</b>

<code>вип</code> — VIP магазин
<code>магазин питомцев</code> — питомцы
<code>магазин тянок</code> — тянки
<code>магазин машин</code> — машины

<b>ИНФОРМАЦИЯ:</b>

<code>мой питомец</code> — питомец
<code>моя тянка</code> — тянка
<code>моя машина</code> — машина
<code>мой бизнес</code> — бизнес
<code>мой брак</code> — брак
<code>браки</code> — все браки
<code>мой профиль</code> — снежки

━━━━━━━━━━━━━━━━━"""
    }
]


# ================== ОБРАБОТЧИК ПАГИНАЦИИ КОМАНД ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("help_page_"))
def callback_commands_page(call):
    try:
        page_num = int(call.data.split("_")[2]) - 1
        if page_num < 0:
            page_num = 0
        if page_num >= len(COMMANDS_PAGES):
            page_num = len(COMMANDS_PAGES) - 1
        
        page = COMMANDS_PAGES[page_num]
        
        kb = InlineKeyboardMarkup(row_width=3)
        
        # Кнопки навигации
        nav_buttons = []
        if page_num > 0:
            nav_buttons.append(InlineKeyboardButton(" < ", callback_data=f"help_page_{page_num}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{page_num+1}/{len(COMMANDS_PAGES)}", callback_data="no_action"))
        
        if page_num < len(COMMANDS_PAGES) - 1:
            nav_buttons.append(InlineKeyboardButton(" > ", callback_data=f"help_page_{page_num+2}"))
        
        kb.row(*nav_buttons)
        kb.add(InlineKeyboardButton("В главное меню", callback_data="back_to_help_main"))
        
        bot.edit_message_text(
            f"{page['title']}\n\n{page['content']}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка в пагинации команд: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!")


# ================== ОБРАБОТЧИКИ ДРУГИХ РАЗДЕЛОВ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("help_") and not c.data.startswith("help_page_") and not c.data.startswith("help_next_page_") and not c.data.startswith("help_prev_page_"))
def callback_help_sections(call):
    try:
        if call.data == "no_action":
            bot.answer_callback_query(call.id)
            return
            
        section = call.data.split("_")[1]
        
        # Остальные разделы с чистым текстом
        if section == "games":
            text = (
    "<b>ИГРЫ</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
    
    "<b>КАЗИНО:</b>\n"
    "• <code>играть [ставка]</code> — Блэкджек\n"
    "• <code>рулетка [ставка]</code> — Рулетка\n"
    "   ├─ к/ч (красное/черное)\n"
    "   ├─ 1-36 (ставьте на числа)\n"
    "   └─ <code>го</code> — начинает игру\n"
    "• <code>мины [ставка]</code> — Мины\n\n"
    
    "<b>СПОРТИВНЫЕ:</b>\n"
    "• <code>рб [ставка] [орёл/решка]</code> — Монетка\n"
    "• <code>футбол [ставка]</code> — Футбол\n"
    "• <code>баскетбол [ставка]</code> — Баскетбол\n"
    "• <code>кнб</code> — Крестики-нолики (только ответом на сообщение пользователя)\n\n"
    
    "<b>ВЫИГРЫШИ:</b>\n"
    "• Победа в казино: ×2 ставки\n"
    "• Спортивные игры: ×2 ставки\n"
    "━━━━━━━━━━━━━━━━━━━"
)
            
        elif section == "vip":
            text = (
                "<b>VIP СИСТЕМА</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
                
                "<b>ПРЕИМУЩЕСТВА:</b>\n"
                "• Пассивный доход каждые 3 часа\n"
                "• Бонус +5%—40% ко всем доходам\n"
                "• Эксклюзивный статус\n\n"
                
                "<b>СТОИМОСТЬ:</b>\n"
                "• VIP 1: 250,000$\n"
                "• VIP 2: 500,000$\n"
                "• VIP 3: 750,000$\n"
                "• VIP 4: 1,000,000$\n"
                "• VIP 5: 1,250,000$\n"
                "• VIP 6: 1,500,000$\n"
                "• VIP 7: 1,750,000$\n\n"
                
                "<b>ДОХОД В 3 ЧАСА:</b>\n"
                "• VIP 1: 1,000$\n"
                "• VIP 7: 20,000$\n\n"
                
                "<b>КОМАНДА:</b>\n"
                "<code>вип</code>\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            
        elif section == "tyanki":
            text = (
                "<b>ТЯНКИ</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
                
                "<b>КОМАНДЫ:</b>\n"
                "<code>магазин тянок</code> — магазин\n"
                "<code>купить тянку [номер]</code> — купить\n"
                "<code>моя тянка</code> — информация\n"
                "<code>продать тянку</code> — продать\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            
        elif section == "pets":
            text = (
                "<b>ПИТОМЦЫ</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
                
                "<b>КОМАНДЫ:</b>\n"
                "<code>магазин питомцев</code> — магазин чтобы купить питомца\n"
                "<code>купить питомца [номер]</code> — купить определенного питомца\n"
                "<code>мой питомец</code> — информация про питомца\n"
                "<code>продать питомца</code> — продать своего питомца\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            
        elif section == "marriage":
            text = (
                "<b>БРАК</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
                
                "<b>КОМАНДЫ:</b>\n"
                "<code>+брак</code> — предложить (ответом)\n"
                "<code>+брак [ID]</code> — по ID - не работает временно\n"
                "<code>мой брак</code> — информация\n"
                "<code>браки</code> — все браки\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            
        elif section == "donate":
            text = (
                "<b>ДОНАТ</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
                
                "<b>ПОПОЛНЕНИЕ:</b>\n"
                "<code>задонатить [сумма]</code>\n\n"
                
                "<b>ПОДДЕРЖКА:</b>\n"
                "@parvizwp\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            
        elif section == "snow":
            text = (
    "<b>🎮 ИГРЫ И ИВЕНТЫ</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
    
    "<b>❄️ СНЕЖКИ (новогодний ивент):</b>\n"
    "<code>снежок</code> — слепить снежок\n"
    "<code>мой профиль</code> — статистика снежков\n"
    "<code>ежедневный</code> — ежедневная награда\n"
    "<code>топ снежков</code> — топ игроков\n"
    "<code>снежный топ</code> — альтернативная команда\n\n"
    
    "<b>🗑️ СБОР МУСОРА (новый ивент):</b>\n"
    "<code>начать сборку мусора</code> — начать сбор\n"
    "<code>сборка мусора</code> — альтернативная команда\n"
    "<code>мой инвентарь</code> — показать найденное\n"
    "<code>мой инв</code> — краткая команда\n\n"
    
    "<b>📊 КУРС ОБМЕНА:</b>\n"
    "• ❄️ 1 снежок = 50$\n"
    "• 🌟 1 золотой снежок = 250$\n"
    "• 🎯 5% шанс на золотой снежок\n\n"
    
    "<b>💰 НАЙТИ МОЖНО:</b>\n"
    "• 🍂 Листья\n"
    "• 🥤 Бутылка\n"
    "• 📰 Бумага\n"
    "• 📱 Телефон\n"
    "• 💍 Кольцо\n"
    "• и другие предметы...\n\n"
    
    "<i>💫 Каждые 2 секунды можно собирать мусор!\n"
    "🎁 80% шанс найти что-то ценное!</i>\n"
    "━━━━━━━━━━━━━━━━━━━"
)
            
        elif section == "support":
            text = (
                "<b>ПОДДЕРЖКА</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
                
                "<b>РАЗРАБОТЧИК:</b>\n"
                "@parvizwp\n\n"
                
                "<b>ЧТО УКАЗАТЬ:</b>\n"
                "• Ваш ID: <code>{}</code>\n"
                "• Описание проблемы\n"
                "• Скриншоты\n"
                "━━━━━━━━━━━━━━━━━━━".format(call.from_user.id)
            )
            
            # Для поддержки добавляем кнопку
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Написать разработчику", url="https://t.me/parvizwp"))
            kb.add(InlineKeyboardButton("В главное меню", callback_data="back_to_help_main"))
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=kb,
                parse_mode="HTML"
            )
            return
        
        # Общая клавиатура для всех разделов
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("В главное меню", callback_data="back_to_help_main"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка в разделе помощи: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!")


# ================== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ПОМОЩИ ==================
@bot.callback_query_handler(func=lambda c: c.data == "back_to_help_main")
def callback_back_to_help_main(call):
    user = call.from_user
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    text = (
        "📖 <b>ПАНЕЛЬ ПОМОЩИ</b>\n"
        f"👤 <b>Пользователь:</b> {mention}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
        "Выберите раздел:"
    )

    # Показываем первую страницу
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("Команды", callback_data="help_page_1"))
    kb.add(InlineKeyboardButton("Игры", callback_data="help_games"))
    kb.add(InlineKeyboardButton("VIP", callback_data="help_vip"))
    kb.add(InlineKeyboardButton(" > ", callback_data="help_next_page_2"))

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)
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
    """Игра Орёл и Решка с гифкой, обратным отсчётом и кнопками"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Использование: рб [ставка] [орёл/решка]")
            return

        bet = int(parts[1])
        choice = parts[2].lower().replace("ё", "е")  # ✅ поддержка "орел" и "орёл"

        if choice not in ["орел", "решка"]:
            bot.send_message(message.chat.id, "❌ Нужно указать 'орёл' или 'решка'.")
            return

        user_id = message.from_user.id
        user_data = get_user_data(user_id)

        if user_data["balance"] < bet:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            return

        # Снимаем ставку
        user_data["balance"] -= bet
        save_casino_data()

        mention = f'<a href="tg://user?id={user_id}">{message.from_user.first_name}</a>'

        # Отправляем сообщение с гифкой и обратным отсчётом
        msg = bot.send_animation(
            message.chat.id,
            COIN_FLIP_GIF,
            caption=f"{mention}, ты начал(а) игру в <b>Орёл и Решка</b>.\n\nРезультат через: 3️⃣",
            parse_mode="HTML"
        )

        # Анимация обратного отсчёта (3 → 2 → 1)
        time.sleep(1)
        bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            caption=f"{mention}, ты начал(а) игру в <b>Орёл и Решка</b>.\n\nРезультат через: 2️⃣",
            parse_mode="HTML"
        )
        time.sleep(1)
        bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            caption=f"{mention}, ты начал(а) игру в <b>Орёл и Решка</b>.\n\nРезультат через: 1️⃣",
            parse_mode="HTML"
        )
        time.sleep(1)

        # Определяем результат
        result = random.choice(["орел", "решка"])
        win = (choice == result)
        prize = bet * 2 if win else 0

        if win:
            user_data["balance"] += prize
            save_casino_data()
            result_text = f"{mention}, ты выиграл(а) <b>{format_number(prize)}$</b>! 🎉\n\nТвоя ставка была: {choice.capitalize()}"
        else:
            result_text = f"{mention}, ты проиграл(а) 😢\n\nТвоя ставка была: {choice.capitalize()}"

        # Кнопки
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💰 Баланс", callback_data=f"balance_{user_id}"))
        kb.add(types.InlineKeyboardButton("❌ Удалить", callback_data=f"delete_coin_{user_id}"))

        # Показываем результат
        bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            caption=result_text,
            parse_mode="HTML",
            reply_markup=kb
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при игре в Орёл и Решка: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("balance_"))
def show_balance_btn(call):
    try:
        user_id = int(call.data.split("_")[1])
        user_data = get_user_data(user_id)
        balance = user_data["balance"]

        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f"💰 Твой баланс: {balance}$",
            show_alert=True  # ✅ показывает во всплывающем окне
        )

    except Exception as e:
        print(f"[show_balance_btn] Ошибка: {e}")



@bot.callback_query_handler(func=lambda c: c.data.startswith("delete_coin_"))
def delete_coin_btn(call):
    try:
        user_id = int(call.data.split("_")[2])
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"{mention}, я удалил 📩", parse_mode="HTML")
    except Exception as e:
        print(f"[delete_coin_btn] Ошибка: {e}")




# ================== 💎 ДОНАТ МЕНЮ (ЗВЁЗДЫ, ТОЛЬКО ВАЛЮТА) ==================
STARS_DB = "stars_payments.db"
DONATE_IMAGE_URL = "https://w7.pngwing.com/pngs/853/96/png-transparent-computer-icons-donation-charitable-organization-donate-miscellaneous-text-logo.png"

# ----------- ИНИЦИАЛИЗАЦИЯ БД -----------
def init_star_db():
    conn = sqlite3.connect(STARS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS star_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            payment_id TEXT UNIQUE,
            stars INTEGER,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_star_db()

def create_star_payment(user_id, stars, amount):
    pid = str(uuid.uuid4())
    conn = sqlite3.connect(STARS_DB)
    c = conn.cursor()
    c.execute("INSERT INTO star_payments (user_id, payment_id, stars, amount) VALUES (?, ?, ?, ?)",
              (user_id, pid, stars, amount))
    conn.commit()
    conn.close()
    return pid

def complete_star_payment(pid):
    conn = sqlite3.connect(STARS_DB)
    c = conn.cursor()
    c.execute("UPDATE star_payments SET status='completed' WHERE payment_id=?", (pid,))
    conn.commit()
    conn.close()

def get_star_payment(pid):
    conn = sqlite3.connect(STARS_DB)
    c = conn.cursor()
    c.execute("SELECT user_id, stars, amount, status FROM star_payments WHERE payment_id=?", (pid,))
    row = c.fetchone()
    conn.close()
    return row


# ----------- МЕНЮ ДОНАТА -----------
def show_donate_menu(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💰 Купить валюту", callback_data="don_stars_money"))
    kb.add(types.InlineKeyboardButton("🪙 Задонатить командой", callback_data="don_stars_cmd"))
    kb.add(types.InlineKeyboardButton("⬅️ Главное меню", callback_data="menu_main"))

    text = (
        "💎 <b>Донат через Telegram Stars</b>\n\n"
        "⭐ <b>Курс:</b>\n"
        "10 000💸 = 5⭐  →  1⭐ = 2 000💸\n\n"
        "📦 <b>Ты можешь:</b>\n"
        "• Купить фиксированный пакет 💰\n"
        "• Или написать команду: <code>задонатить 20000</code>\n\n"
        "⚡ Безопасная оплата через Telegram Stars!"
    )

    bot.send_photo(message.chat.id, DONATE_IMAGE_URL, caption=text, parse_mode="HTML", reply_markup=kb)

@bot.message_handler(commands=["донат"])
def cmd_donate(message):
    show_donate_menu(message)

# ----------- КНОПКА «КУПИТЬ ВАЛЮТУ» -----------
@bot.callback_query_handler(func=lambda c: c.data == "don_stars_money")
def donate_money(call):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💰 10 000💸 — 5⭐", callback_data="buy_money_10000"))
    kb.add(types.InlineKeyboardButton("💰 50 000💸 — 25⭐", callback_data="buy_money_50000"))
    kb.add(types.InlineKeyboardButton("💰 100 000💸 — 50⭐", callback_data="buy_money_100000"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="donate_back"))

    bot.edit_message_media(
        types.InputMediaPhoto(
            DONATE_IMAGE_URL,
            caption="💰 <b>Выбери пакет игровой валюты:</b>",
            parse_mode="HTML"
        ),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=kb
    )

# ----------- КНОПКА «ЗАДОНАТИТЬ КОМАНДОЙ» -----------
@bot.callback_query_handler(func=lambda c: c.data == "don_stars_cmd")
def donate_cmd_info(call):
    text = (
        "🪙 <b>Команда доната</b>\n\n"
        "Просто напиши:\n<code>задонатить 20000</code>\n\n"
        "Бот посчитает стоимость в ⭐ и предложит оплату.\n"
        "После успешной оплаты 💸 зачислятся автоматически."
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="donate_back"))
    bot.edit_message_media(
        types.InputMediaPhoto(DONATE_IMAGE_URL, caption=text, parse_mode="HTML"),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=kb
    )

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
        stars = max(1, amount // 2000)
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
        f"💰 На баланс зачислено <b>{amount:,}💸</b>\n"
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
    keyboard.add(types.InlineKeyboardButton("🎁 Активировать", callback_data=f"activate_{promo_name}"))
    message_text = (
        f"💥 <b>Новый промокод!</b>\n\n"
        f"🎫 Код: <code>{promo_name}</code>\n"
        f"💰 Сумма: <b>{format_number(amount)}$</b>\n"
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
        f"и получил <b>{format_number(promo['amount'])}$</b> 💸\n\n"
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

# ================== КОМАНДЫ МОДЕРАЦИИ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("кэвжааыэуть "))
def kick_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите кикнуть!")
            return
            
        target_user = message.reply_to_message.from_user
        reason = " ".join(message.text.split()[2:]) if len(message.text.split()) > 2 else "Не указана"
        
        # Пытаемся кикнуть пользователя
        try:
            bot.kick_chat_member(message.chat.id, target_user.id)
            bot.unban_chat_member(message.chat.id, target_user.id)
            
            bot.reply_to(message, f"✅ Пользователь {target_user.first_name} был кикнут!\nПричина: {reason}")
            log_moderation("кик", message.from_user.id, target_user.id, reason)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Не удалось кикнуть пользователя: {e}")
            logger.error(f"Ошибка кика пользователя: {e}")
            
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды кик: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("жажуцэвн "))
def ban_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите забанить!")
            return
            
        target_user = message.reply_to_message.from_user
        reason = " ".join(message.text.split()[2:]) if len(message.text.split()) > 2 else "Не указана"
        
        # Пытаемся забанить пользователя
        try:
            bot.kick_chat_member(message.chat.id, target_user.id)
            
            bot.reply_to(message, f"✅ Пользователь {target_user.first_name} был забанен!\nПричина: {reason}")
            log_moderation("бан", message.from_user.id, target_user.id, reason)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Не удалось забанить пользователя: {e}")
            logger.error(f"Ошибка бана пользователя: {e}")
            
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды бан: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("сжаажпжять ббабан "))
def unban_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите разбанить!")
            return
            
        target_user = message.reply_to_message.from_user
        
        # Пытаемся разбанить пользователя
        try:
            bot.unban_chat_member(message.chat.id, target_user.id)
            
            bot.reply_to(message, f"✅ Пользователь {target_user.first_name} был разбанен!")
            log_moderation("ражаажн", message.from_user.id, target_user.id)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Не удалось разбанить пользователя: {e}")
            logger.error(f"Ошибка разбана пользователя: {e}")
            
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды снять бан: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("жйзабут "))
def mute_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите замутить!")
            return
            
        target_user = message.reply_to_message.from_user
        parts = message.text.split()
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ Укажите время мута! Например: мут @user 1h Причина")
            return
            
        time_str = parts[2]
        reason = " ".join(parts[3:]) if len(parts) > 3 else "Не указана"
        
        # Парсим время
        if time_str.endswith('m'):
            mute_minutes = int(time_str[:-1])
            mute_until = datetime.now() + timedelta(minutes=mute_minutes)
        elif time_str.endswith('h'):
            mute_hours = int(time_str[:-1])
            mute_until = datetime.now() + timedelta(hours=mute_hours)
        elif time_str.endswith('d'):
            mute_days = int(time_str[:-1])
            mute_until = datetime.now() + timedelta(days=mute_days)
        else:
            bot.reply_to(message, "❌ Неверный формат времени! Используйте: 30m, 2h, 1d")
            return
            
        # Пытаемся ограничить пользователя
        try:
            bot.restrict_chat_member(
                message.chat.id,
                target_user.id,
                until_date=mute_until.timestamp(),
                permissions=telebot.types.ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                )
            )
            
            # Сохраняем мут в warns_data
            user_warns = get_user_warns(target_user.id)
            user_warns["muted_until"] = mute_until.isoformat()
            save_warns()
            
            bot.reply_to(message, f"✅ Пользователь {target_user.first_name} был замучен до {mute_until.strftime('%Y-%m-%d %H:%M')}!\nПричина: {reason}")
            log_moderation("мут", message.from_user.id, target_user.id, reason, time_str)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Не удалось замутить пользователя: {e}")
            logger.error(f"Ошибка мута пользователя: {e}")
            
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды мут: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("сняажажа ажажут "))
def unmute_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите размутить!")
            return
            
        target_user = message.reply_to_message.from_user
        
        # Пытаемся снять ограничения
        try:
            bot.restrict_chat_member(
                message.chat.id,
                target_user.id,
                permissions=telebot.types.ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True
                )
            )
            
            # Убираем мут из warns_data
            user_warns = get_user_warns(target_user.id)
            user_warns["muted_until"] = None
            save_warns()
            
            bot.reply_to(message, f"✅ Пользователь {target_user.first_name} был размучен!")
            log_moderation("размут", message.from_user.id, target_user.id)
            
        except Exception as e:
            bot.reply_to(message, f"❌ Не удалось размутить пользователя: {e}")
            logger.error(f"Ошибка размута пользователя: {e}")
            
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды снять мут: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("важажан "))
def warn_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, которого хотите предупредить!")
            return
            
        target_user = message.reply_to_message.from_user
        reason = " ".join(message.text.split()[2:]) if len(message.text.split()) > 2 else "Не указана"
        
        # Добавляем варн
        user_warns = get_user_warns(target_user.id)
        warn_id = len(user_warns["warns"]) + 1
        user_warns["warns"].append({
            "id": warn_id,
            "reason": reason,
            "moderator": message.from_user.id,
            "date": datetime.now().isoformat()
        })
        save_warns()
        
        total_warns = len(user_warns["warns"])
        
        # Автонаказания при определенном количестве варнов
        if total_warns == 3:
            # Мут на 1 час при 3 варнах
            mute_until = datetime.now() + timedelta(hours=1)
            bot.restrict_chat_member(
                message.chat.id,
                target_user.id,
                until_date=mute_until.timestamp(),
                permissions=telebot.types.ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                )
            )
            user_warns["muted_until"] = mute_until.isoformat()
            save_warns()
            mute_text = " и получил мут на 1 час"
        elif total_warns == 5:
            # Бан при 5 варнах
            bot.kick_chat_member(message.chat.id, target_user.id)
            mute_text = " и был забанен"
        else:
            mute_text = ""
        
        bot.reply_to(message, f"⚠️ Пользователь {target_user.first_name} получил предупреждение #{warn_id}!\nПричина: {reason}\nВсего предупреждений: {total_warns}{mute_text}")
        log_moderation("варн", message.from_user.id, target_user.id, reason)
        
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды варн: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("ваажажан лажажаст "))
def warn_list(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, чьи предупреждения хотите посмотреть!")
            return
            
        target_user = message.reply_to_message.from_user
        user_warns = get_user_warns(target_user.id)
        
        if not user_warns["warns"]:
            bot.reply_to(message, f"✅ У пользователя {target_user.first_name} нет предупреждений!")
            return
            
        warns_text = f"📋 Список предупреждений пользователя {target_user.first_name}:\n\n"
        
        for warn in user_warns["warns"]:
            try:
                moderator = bot.get_chat(warn["moderator"])
                moderator_name = moderator.first_name
                if moderator.username:
                    moderator_name += f" (@{moderator.username})"
            except:
                moderator_name = f"ID: {warn['moderator']}"
                
            warn_date = datetime.fromisoformat(warn["date"]).strftime("%Y-%m-%d %H:%M")
            warns_text += f"#{warn['id']} - {warn_date}\nМодератор: {moderator_name}\nПричина: {warn['reason']}\n\n"
        
        bot.reply_to(message, warns_text)
        
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды варн лист: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("снять варн "))
def remove_warn(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя, у которого хотите снять предупреждение!")
            return
            
        target_user = message.reply_to_message.from_user
        parts = message.text.split()
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ Укажите номер предупреждения! Например: снять варн @user 1")
            return
            
        try:
            warn_id = int(parts[2])
        except ValueError:
            bot.reply_to(message, "❌ Неверный номер предупреждения!")
            return
            
        user_warns = get_user_warns(target_user.id)
        
        # Ищем предупреждение по ID
        warn_to_remove = None
        for warn in user_warns["warns"]:
            if warn["id"] == warn_id:
                warn_to_remove = warn
                break
                
        if not warn_to_remove:
            bot.reply_to(message, f"❌ Предупреждение #{warn_id} не найдено!")
            return
            
        # Удаляем предупреждение
        user_warns["warns"].remove(warn_to_remove)
        save_warns()
        
        bot.reply_to(message, f"✅ Предупреждение #{warn_id} снято с пользователя {target_user.first_name}!")
        log_moderation("снятие варна", message.from_user.id, target_user.id, f"Предупреждение #{warn_id}")
        
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка выполнения команды!")
        logger.error(f"Ошибка команды снять варн: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("очистить "))
def clear_messages(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        amount = int(message.text.split()[1])
        
        if amount < 1 or amount > 500:
            bot.reply_to(message, "❌ Можно удалить от 1 до 500 сообщений за раз!")
            return
            
        # Удаляем команду
        bot.delete_message(message.chat.id, message.message_id)
        
        # Удаляем указанное количество сообщений
        for i in range(amount):
            try:
                # Получаем ID сообщения для удаления (предыдущее сообщение)
                msg_id = message.message_id - i - 1
                bot.delete_message(message.chat.id, msg_id)
            except:
                # Если сообщение не найдено, пропускаем
                pass
                
        log_moderation("очистка сообщений", message.from_user.id, message.chat.id, f"{amount} сообщений")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: очистить [количество]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка очистки сообщений!")
        logger.error(f"Ошибка команды очистить: {e}")

# ================== КОМАНДЫ АДМИНИСТРИРОВАНИЯ ==================

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
    
    text = f"<b>{mention} - Это меню пользователя, выберите действия которые хотите сделать с ним.</b>"
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Информация", callback_data=f"admin_user_info_{target_user.id}"),
        InlineKeyboardButton("🛡 Выдать модератора", callback_data=f"admin_give_mod_{target_user.id}")
    )
    kb.add(
        InlineKeyboardButton("🚫 Убрать модератора", callback_data=f"admin_remove_mod_{target_user.id}"),
        InlineKeyboardButton("💥 Обнулить данные", callback_data=f"admin_reset_data_{target_user.id}")
    )
    
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_user_info_"))
def admin_user_info(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        user_data = get_user_data(target_user_id)
        
        # Информация о VIP
        vip = user_data["vip"]
        vip_text = "Нет" if vip["level"] == 0 else f"{VIP_LEVELS[vip['level']]['prefix']} {VIP_LEVELS[vip['level']]['name']}"
        
        # Информация о тянке
        tyanka_text = "Нет"
        if user_data.get("tyanka"):
            tyanka_name = user_data["tyanka"].get("name", "Нет")
            tyanka_mood = user_data["tyanka"].get("mood", 0)
            tyanka_text = f"{tyanka_name} ({tyanka_mood}%)"
        
        # Информация о питомце
        pet_text = "Нет"
        pet_data = get_pet(target_user_id)
        if pet_data:
            pet_id, name, price, satiety, level, xp, last_update = pet_data
            pet_info = PETS_DATA.get(pet_id, {})
            pet_text = f"{name} (ур. {level})"
        
        # Информация о машине
        car_text = "Нет"
        if user_data.get("car"):
            car_name = user_data["car"].get("name", "Нет")
            car_text = car_name
        
        # Информация о бизнесе
        business_text = "Нет"
        if user_data.get("business"):
            business_name = user_data["business"].get("name", "Нет")
            business_text = business_name
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        
        text = (
            f"<b>📊 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ</b>\n\n"
            f"👤 <b>Имя:</b> {mention}\n"
            f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n"
            f"💰 <b>Баланс:</b> {format_number(user_data['balance'])}$\n"
            f"⭐ <b>VIP:</b> {vip_text}\n"
            f"💞 <b>Тянка:</b> {tyanka_text}\n"
            f"🐾 <b>Питомец:</b> {pet_text}\n"
            f"🚗 <b>Машина:</b> {car_text}\n"
            f"🏢 <b>Бизнес:</b> {business_text}\n"
            f"🛡 <b>Админ:</b> {'✅ Да' if target_user_id in ADMIN_IDS else '❌ Нет'}"
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
        logger.error(f"Ошибка admin_user_info: {e}")

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
        text = f"<b>Ты успешно выдал {mention} права модератора в боте</b>"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
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
        text = f"<b>Права модератора успешно убраны у {mention}</b>"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
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

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reset_data_"))
def admin_reset_data(call):
    try:
        target_user_id = int(call.data.split("_")[3])
        target_user = bot.get_chat(target_user_id)
        
        user_data = get_user_data(target_user_id)
        
        # Обнуляем все данные пользователя
        user_data["balance"] = START_BALANCE
        user_data["tyanka"] = None
        user_data["business"] = None
        user_data["car"] = None
        user_data["activated_promos"] = []
        user_data["daily_income"] = {"date": date.today().isoformat(), "amount": 0}
        user_data["daily_transfers"] = {"date": date.today().isoformat(), "amount": 0}
        user_data["vip"] = {"level": 0, "expires": None}
        
        # Удаляем питомца из базы
        delete_pet(target_user_id)
        
        save_casino_data()
        
        mention = f'<a href="tg://user?id={target_user_id}">{target_user.first_name}</a>'
        text = f"<b>✅ Все данные пользователя {mention} были обнулены!</b>\n\nБаланс сброшен до начального: {format_number(START_BALANCE)}$"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_back_{target_user_id}"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )
        
        log_moderation("обнуление данных", call.from_user.id, target_user_id)
        bot.answer_callback_query(call.id, "✅ Данные обнулены!")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка admin_reset_data: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_back_"))
def admin_back(call):
    try:
        target_user_id = int(call.data.split("_")[2])
        target_user = bot.get_chat(target_user_id)
        show_user_admin_menu(call.message.chat.id, target_user)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")

# ================== ИЗМЕНЕНИЕ НАСТРОЕК МИН ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "изменить мины")
def change_mines(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Клетки", callback_data="mines_config_cells_plus"),
        InlineKeyboardButton("➖ Клетки", callback_data="mines_config_cells_minus"),
        InlineKeyboardButton("➕ Мины", callback_data="mines_config_count_plus"),
        InlineKeyboardButton("➖ Мины", callback_data="mines_config_count_minus"),
        InlineKeyboardButton("❌ Закрыть", callback_data="mines_config_close")
    )
    
    bot.reply_to(message, 
                f"⚙️ <b>Настройки игры Мины:</b>\n\n"
                f"Количество клеток: {config['mines_cells']}\n"
                f"Количество мин: {config['mines_count']}\n\n"
                f"Выберите что изменить:", 
                reply_markup=kb,
                parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("mines_config_"))
def mines_config_handler(call):
    try:
        action = call.data
        
        if action == "mines_config_cells_plus":
            config['mines_cells'] += 1
        elif action == "mines_config_cells_minus":
            if config['mines_cells'] > 5:  # Минимальное количество клеток
                config['mines_cells'] -= 1
        elif action == "mines_config_count_plus":
            if config['mines_count'] < config['mines_cells'] - 1:  # Максимум мин = клетки - 1
                config['mines_count'] += 1
        elif action == "mines_config_count_minus":
            if config['mines_count'] > 1:  # Минимальное количество мин
                config['mines_count'] -= 1
        elif action == "mines_config_close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "✅ Настройки сохранены!")
            return
        
        save_config()
        
        # Обновляем сообщение с новыми настройками
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("➕ Клетки", callback_data="mines_config_cells_plus"),
            InlineKeyboardButton("➖ Клетки", callback_data="mines_config_cells_minus"),
            InlineKeyboardButton("➕ Мины", callback_data="mines_config_count_plus"),
            InlineKeyboardButton("➖ Мины", callback_data="mines_config_count_minus"),
            InlineKeyboardButton("❌ Закрыть", callback_data="mines_config_close")
        )
        
        bot.edit_message_text(
            f"⚙️ <b>Настройки игры Мины:</b>\n\n"
            f"Количество клеток: {config['mines_cells']}\n"
            f"Количество мин: {config['mines_count']}\n\n"
            f"Выберите что изменить:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )
        
        bot.answer_callback_query(call.id, "✅ Настройки обновлены!")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {e}")
        logger.error(f"Ошибка mines_config_handler: {e}")



@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("рулетка "))
def roulette_cmd(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        bet = int(message.text.split()[1])
        if bet <= 0:
            bot.send_message(message.chat.id, "❌ Ставка должна быть положительной!")
            return
            
        if user_data["balance"] < bet:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            return
            
        if start_roulette(user_id, bet):
            bot.send_photo(message.chat.id, CASINO_IMAGE_URL, 
                          caption=f"🎡 Ставка {format_number(bet)} принята.\nВыберите вариант:", 
                          reply_markup=roulette_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ Ошибка начала игры!")
            
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Используйте: рулетка [ставка]")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка начала игры!")
        logger.error(f"Ошибка в игре рулетка: {e}")

@bot.message_handler(func=lambda m: m.text and (m.text.lower() == "баланс" or m.text.lower() == "б"))
def check_balance(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Обновляем доходы со всех активов
    update_all_incomes(user_id)
    
    bal = user_data["balance"]
    bank_bal = user_data["bank_balance"]
    bot.send_message(message.chat.id, f"💰 Ваш баланс: {format_number(bal)}$\n🏦 Банковский счет: {format_number(bank_bal)}$")
    logger.info(f"Пользователь {message.from_user.username} запросил баланс")

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


@bot.message_handler(func=lambda m: m.text and m.text.lower() == "бонус")
def bonus_cmd(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    today = date.today().isoformat()

    if user_data.get("last_bonus") == today:
        now = datetime.now()
        tomorrow = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
        bot.send_message(
            message.chat.id,
            f"⏳ Бонус уже был\nЧерез {format_timedelta(tomorrow - now)}"
        )
        return

    bonus = random.randint(1200, 8000)
    actual = add_income(user_id, bonus, "bonus")
    user_data["last_bonus"] = today
    save_casino_data()

    mention = user_mention(message.from_user)

    bot.send_message(
        message.chat.id,
        f"🎁 {mention}, бонус <b>{actual}$</b> был начислен на твой баланс 💸\n\n"
        f"1. ⚒️ <a href='{DEV_LINK}'>Разработчик</a>\n"
        f"2. 🥝 <a href='{CHAT_LINK}'>Наш чат</a>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@bot.message_handler(func=lambda m: m.text and m.text.lower() == "ферма")
def farm_cmd(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    now = datetime.now()

    last = user_data.get("last_farm")
    if last:
        last_dt = datetime.fromisoformat(last)
        diff = now - last_dt
        if diff < timedelta(hours=2):
            bot.send_message(
                message.chat.id,
                f"🚜 Ферма на перезарядке\nЧерез {format_timedelta(timedelta(hours=2) - diff)}"
            )
            return

    earned = random.randint(500, 5000)
    actual = add_income(user_id, earned, "farm")
    user_data["last_farm"] = now.isoformat()
    save_casino_data()

    mention = user_mention(message.from_user)

    bot.send_message(
        message.chat.id,
        f"🚜 {mention}, ты заработал <b>{actual}$</b> на ферме 💸\n\n"
        f"1. ⚒️ <a href='{DEV_LINK}'>Разработчик</a>\n"
        f"2. 🥝 <a href='{CHAT_LINK}'>Наш чат</a>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )
            
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
                bot.reply_to(message, "❌ Минимальная ставка: 100$")
                return
            if bet > 1000000:
                bot.reply_to(message, "❌ Максимальная ставка: 1,000,000$")
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
                f"Нужно: {bet:,}$ | У тебя: {user_data['balance']:,}$",
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
            f"💰 <b>Ставка: {bet:,}$</b>\n\n"
            f"⏱ Приглашение действует 2 минуты"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"ttt_accept_{game_id}"),
            InlineKeyboardButton("❌ Отказать", callback_data=f"ttt_decline_{game_id}")
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
                            f"{bet:,}$ возвращены на баланс.",
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
                f"❌ У тебя недостаточно денег!\nНужно: {game['bet']:,}$", 
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
            f"💰 <b>Ставка: {game['bet']:,}$</b>\n"
            f"🏆 <b>Банк: {game['bet'] * 2:,}$</b>\n\n"
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
                f"Ему возвращены {game['bet']:,}$ на баланс."
            )
        else:  # Тот, кто предложил
            text = (
                f"{decliner_mention}, ты отменил игру в Крестики-Нолики с {player2_mention}.\n"
                f"Тебе возвращены {game['bet']:,}$ на баланс."
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
                        f"🎮 <b>ИГРА ОКОНЧЕНА - НИЧЬЯ! 🤝</b>\n\n"
                        f"💰 Каждому возвращено по {game['bet']:,}$\n\n"
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
                        f"🎮 <b>ИГРА ОКОНЧЕНА - ПОБЕДА! 🏆</b>\n\n"
                        f"{winner_mention}, поздравляю! Ты выиграл {loser_mention} и получил {game['bet'] * 2:,}$\n\n"
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
                    f"💰 <b>Ставка: {game['bet']:,}$</b>\n"
                    f"🏆 <b>Банк: {game['bet'] * 2:,}$</b>\n\n"
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
            
          
            # ================== ФЕЙКОВАЯ СТАТИСТИКА БОТА (ТОЛЬКО ДЛЯ АДМИНА) ==================

FAKE_USERS = 38194
FAKE_GROUPS = 328

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "статистика бота")
def bot_fake_stats(message):
    if message.from_user.id not in ADMIN_IDS:
        return  # обычный пользователь — молчание

    text = (
        "🎅 <b>Статистика пользователей в боте MEOW</b>\n\n"
        f"🗨️ Всего пользователей в боте: <b><i>{FAKE_USERS}</i></b>.\n"
        f"🗾 Всего групп в которых состоит бот: <b><i>{FAKE_GROUPS}</i></b>\n"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 Обновить статистику", callback_data="fake_stats_refresh"))

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "fake_stats_refresh")
def fake_stats_refresh(call):
    if call.from_user.id not in ADMIN_IDS:
        return  # обычный пользователь — молчание

    text = (
        "🎅 <b>Статистика пользователей в боте MEOW</b>\n\n"
        f"🗨️ Всего пользователей в боте: <b><i>{FAKE_USERS}</i></b>.\n"
        f"🗾 Всего групп в которых состоит бот: <b><i>{FAKE_GROUPS}</i></b>\n"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 Обновить статистику", callback_data="fake_stats_refresh"))

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )

    bot.answer_callback_query(call.id, "Обновлено ✔️")


# ================== ОРЕЛ И РЕШКА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(('рб ', 'орёл ', 'решка ')))
def coin_flip_game(message):
    try:
        text = message.text.lower()
        parts = text.split()
        
        # Определяем формат команды
        if parts[0] == 'рб' and len(parts) >= 3:
            bet = int(parts[1])
            choice = parts[2]
        elif parts[0] in ['орёл', 'орел'] and len(parts) >= 2:
            bet = int(parts[1])
            choice = 'орёл'
        elif parts[0] == 'решка' and len(parts) >= 2:
            bet = int(parts[1])
            choice = 'решка'
        else:
            bot.reply_to(message, "❌ Используйте: рб [ставка] [орёл/решка]")
            return
        
        # Нормализуем выбор
        if choice in ['орёл', 'ореl']:
            choice = 'орёл'
        elif choice == 'решка':
            choice = 'решка'
        else:
            bot.reply_to(message, "❌ Неверный выбор. Выберите орёл или решка.")
            return

        user_id = message.from_user.id
        user_data = get_user_data(user_id)

        if bet <= 0:
            bot.reply_to(message, "❌ Ставка должна быть положительной!")
            return

        if user_data['balance'] < bet:
            bot.reply_to(message, "❌ Недостаточно средств!")
            return

        # Снимаем ставку
        user_data['balance'] -= bet
        save_casino_data()

        # Отправляем анимацию
        bot.send_animation(message.chat.id, COIN_FLIP_GIF, caption="🎲 Подбрасываем монетку...")

        # Определяем результат
        result = random.choice(['орёл', 'решка'])

        # Проверяем выигрыш
        if choice == result:
            win_amount = bet * config["coin_flip_multiplier"]
            actual_win = add_income(user_id, win_amount, "coin_flip")
            if actual_win > 0:
                bot.send_message(message.chat.id, f"✅ Вы выиграли! Выпал {result}. Ваш выигрыш: {format_number(actual_win)}$. Баланс: {format_number(user_data['balance'])}$")
            else:
                bot.send_message(message.chat.id, f"✅ Вы выиграли, но достигнут дневной лимит дохода! Баланс: {format_number(user_data['balance'])}$")
        else:
            bot.send_message(message.chat.id, f"❌ Вы проиграли. Выпал {result}. Баланс: {format_number(user_data['balance'])}$")
            
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: рб [ставка] [орёл/решка]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка начала игры!")
        logger.error(f"Ошибка в игре орёл/решка: {e}")

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
    
    # Быстрая проверка условий ухода
    if tyanka["satiety"] <= 0 or tyanka.get("mood", 100) <= 20:
        # Просто удаляем тянку без уведомлений
        user_data["tyanka"] = None
        save_casino_data()
        logger.info(f"Тянка ушла от пользователя {user_id} (сытость: {tyanka['satiety']}, настроение: {tyanka.get('mood', 100)})")
        return True
    
    return False

# ================== ОПТИМИЗИРОВАННОЕ ОБНОВЛЕНИЕ СТАТИСТИКИ ТЯНКИ ==================
def update_tyanka_stats(user_data):
    """Обновляет сытость, настроение и накапливает доход (оптимизированная версия)"""
    tyanka = user_data.get("tyanka")
    if not tyanka:
        return
        
    # Быстрая инициализация полей если их нет
    if "mood" not in tyanka:
        tyanka["mood"] = 100
    if "profit_accumulated" not in tyanka:
        tyanka["profit_accumulated"] = 0

    if "last_update" not in tyanka:
        tyanka["last_update"] = datetime.now().isoformat()
        return
    
    last_update = datetime.fromisoformat(tyanka["last_update"])
    now = datetime.now()
    hours_passed = (now - last_update).total_seconds() / 3600
    
    if hours_passed < 0.01:  # Меньше 36 секунд - не обновляем
        return
    
    tyanka_info = TYANKA_DATA[tyanka["name"]]
    
    # Быстрое обновление показателей
    satiety_lost = min(int(hours_passed * 3), tyanka["satiety"])
    mood_lost = min(int(hours_passed * 2), tyanka.get("mood", 100))
    
    if satiety_lost > 0:
        tyanka["satiety"] -= satiety_lost
        tyanka["mood"] = max(0, tyanka.get("mood", 100) - mood_lost)

    # Прибыль только если сытость > 0
    if tyanka["satiety"] > 0:
        profit = int(tyanka_info["profit_per_hour"] * hours_passed)
        tyanka["profit_accumulated"] += profit
    
    tyanka["last_update"] = now.isoformat()
    
    # Быстрая проверка ухода (без сообщений)
    if tyanka["satiety"] <= 0 or tyanka.get("mood", 100) <= 20:
        user_data["tyanka"] = None
        logger.info(f"Тянка автоматически ушла (сытость: {tyanka['satiety']}, настроение: {tyanka.get('mood', 100)})")

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
            f"Цена: <code>{format_number(data['price'])}$</code>\n"
            f"Доход/час: <code>{format_number(data['profit_per_hour'])}$</code>\n"
            f"Кормление: <code>{format_number(data['feed_cost'])}$</code>\n"
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
        kb.add(InlineKeyboardButton("Далее →", callback_data=f"tyanka_page_2_{user_id}"))

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
            f"Цена: <code>{format_number(data['price'])}$</code>\n"
            f"Доход/час: <code>{format_number(data['profit_per_hour'])}$</code>\n"
            f"Кормление: <code>{format_number(data['feed_cost'])}$</code>\n"
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
        nav_buttons.append(InlineKeyboardButton("← Назад", callback_data=f"tyanka_page_1_{user_id}"))
    elif page_num == 1 and page2_tyanki:
        # На первой странице - только кнопка "Далее"
        nav_buttons.append(InlineKeyboardButton("Далее →", callback_data=f"tyanka_page_2_{user_id}"))
    elif page1_tyanki and page2_tyanki:
        # Если есть обе страницы - обе кнопки
        nav_buttons.append(InlineKeyboardButton("← Назад", callback_data=f"tyanka_page_1_{user_id}"))
        nav_buttons.append(InlineKeyboardButton("Далее →", callback_data=f"tyanka_page_2_{user_id}"))

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
        user_data["tyanka"] = {
            "name": tyanka_name,
            "price": tyanka_data["price"],
            "profit_per_hour": tyanka_data["profit_per_hour"],
            "feed_cost": tyanka_data["feed_cost"],
            "rarity": tyanka_data["rarity"],
            "satiety": 100,                # <<<<< ДОБАВЛЕНО
            "last_income": datetime.now().isoformat()
        }
        save_casino_data()
        
        # Красивый ответ
        bot.edit_message_text(
            f"💖 {mention}, ты купил тянку «<b>{tyanka_name.capitalize()}</b>» за <b>{format_number(tyanka_data['price'])}$</b>\n\n"
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

@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_buy_"))
def buy_tyanka_inline(call):
    user_id = call.from_user.id
    tyanka_name = call.data.split("_")[-1]
    handle_tyanka_buy(call.message.chat.id, user_id, tyanka_name, call.from_user.first_name, call)

def handle_tyanka_buy(chat_id, user_id, tyanka_name, buyer_name, call=None):
    user_data = get_user_data(user_id)

    if user_data.get("tyanka"):
        msg = "❌ У вас уже есть тянка! Сначала продайте текущую."
    elif tyanka_name not in TYANKA_DATA:
        msg = "❌ Такой тянки нет в магазине!"
    else:
        tyanka_info = TYANKA_DATA[tyanka_name]
        if user_data["balance"] < tyanka_info["price"]:
            msg = f"❌ Недостаточно средств! Нужно {format_number(tyanka_info['price'])}$"
        else:
            user_data["balance"] -= tyanka_info["price"]
            user_data["tyanka"] = {
                "name": tyanka_name,
                "satiety": 100,
                "mood": 100,
                "last_update": datetime.now().isoformat(),
                "profit_accumulated": 0
            }
            save_casino_data()
            
            msg = (f"🎉 <b>Поздравляем с покупкой!</b>\n\n"
                  f"👤 Покупатель: <b>{buyer_name}</b>\n"
                  f"💝 Тянка: <b>{tyanka_name.capitalize()}</b>\n"
                  f"💰 Стоимость: <code>{format_number(tyanka_info['price'])}$</code>\n"
                  f"⭐ Редкость: {tyanka_info['rarity']}\n\n"
                  f"💖 Теперь ухаживай за своей тянкой!")

    if call:
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, msg, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, parse_mode="HTML")

# ================== МОЯ ТЯНКА ==================
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

    text = (
        f"💞 Тянка <b>『{tyanka['name'].capitalize()}』</b>\n"
        f"➤ Владелец: {mention}\n\n"
        f"🍪 Сытость: {tyanka['satiety']}%\n"
        f"😊 Настроение: {tyanka.get('mood', 100)}%\n"
        f"💲 Доход в час: {format_number(info['profit_per_hour'])}$\n"
        f"🌟 Редкость: {info['rarity']}\n"
        f"💰 Накоплено: {format_number(tyanka.get('profit_accumulated', 0))}$\n"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Собрать", callback_data=f"tyanka_collect_{user_id}"),
        InlineKeyboardButton("🍪 Покормить", callback_data=f"tyanka_feed_{user_id}")
    )
    kb.add(
        InlineKeyboardButton("💎 Действия", callback_data=f"tyanka_actions_{user_id}"),
        InlineKeyboardButton("❌ Продать", callback_data=f"tyanka_sell_{user_id}")
    )

    if info.get("image"):
        bot.send_photo(message.chat.id, info["image"], caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

# ================== ОБНОВЛЕНИЕ СТАТИСТИКИ ТЯНКИ ==================
def update_tyanka_stats(user_data):
    """Обновляет сытость, настроение и накапливает доход"""
    tyanka = user_data.get("tyanka")
    if not tyanka:
        return
        
    # Инициализация полей если их нет
    if "mood" not in tyanka:
        tyanka["mood"] = 100
    if "profit_accumulated" not in tyanka:
        tyanka["profit_accumulated"] = 0

    if "last_update" not in tyanka:
        tyanka["last_update"] = datetime.now().isoformat()
        save_casino_data()
        return
    
    last_update = datetime.fromisoformat(tyanka["last_update"])
    now = datetime.now()
    hours_passed = (now - last_update).total_seconds() / 3600
    
    if hours_passed < 0.01:  # Меньше 36 секунд - не обновляем
        return
    
    tyanka_info = TYANKA_DATA[tyanka["name"]]
    
    # Уменьшаем сытость и настроение
    satiety_lost = min(int(hours_passed * 3), tyanka["satiety"])
    mood_lost = min(int(hours_passed * 2), tyanka.get("mood", 100))
    
    if satiety_lost > 0:
        tyanka["satiety"] -= satiety_lost
        tyanka["mood"] = max(0, tyanka.get("mood", 100) - mood_lost)

    # Прибыль только если сытость > 0
    if tyanka["satiety"] > 0:
        profit = int(tyanka_info["profit_per_hour"] * hours_passed)
        tyanka["profit_accumulated"] += profit
    
    tyanka["last_update"] = now.isoformat()
    save_casino_data()


# ================== ОБРАБОТКА КНОПКИ "НАЗАД" ДЛЯ ТЯНКИ ==================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("back_tyanka_"))
def callback_back_tyanka(call):
    try:
        user_id = int(call.data.split("_")[-1])
        
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Это не твоя тянка!")
            return

        user_data = get_user_data(user_id)
        if not user_data.get("tyanka"):
            bot.answer_callback_query(call.id, "❌ У тебя нет тянки!")
            return

        # Возвращаемся к основному меню тянки
        tyanka = user_data["tyanka"]
        name = tyanka["name"]
        mood = tyanka.get("mood", 100)
        profit = TYANKA_DATA[name]["profit_per_hour"]
        image = TYANKA_DATA[name]["image"]
        info = TYANKA_DATA[name]
        mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("💰 Собрать", callback_data=f"tyanka_collect_{user_id}"),
            InlineKeyboardButton("🍪 Покормить", callback_data=f"tyanka_feed_{user_id}")
        )
        kb.add(
            InlineKeyboardButton("💎 Действия", callback_data=f"tyanka_actions_{user_id}"),
            InlineKeyboardButton("❌ Продать", callback_data=f"tyanka_sell_{user_id}")
        )

        caption = (
            f"💞 Тянка <b>『{tyanka['name'].capitalize()}』</b>\n"
            f"👤 Владелец: {mention}\n\n"
            f"🍪 Сытость: {tyanka['satiety']}%\n"
            f"😊 Настроение: {tyanka.get('mood', 100)}%\n"
            f"💲 Доход в час: {format_number(info['profit_per_hour'])}$\n"
            f"🌟 Редкость: {info['rarity']}\n"
            f"💰 Накоплено: {format_number(tyanka.get('profit_accumulated', 0))}$\n"
        )

        # Редактируем сообщение обратно к основному меню тянки
        bot.edit_message_media(
            media=types.InputMediaPhoto(image, caption=caption, parse_mode="HTML"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка в back_tyanka: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!")

# ================== РАСШИРЕННЫЕ RP ДЕЙСТВИЯ ==================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("tyanka_actions_"))
def callback_tyanka_actions(call):
    user_id = int(call.data.split("_")[-1])

    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!")
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У тебя нет тянки!")
        return

    kb = InlineKeyboardMarkup(row_width=2)
    
    # Романтические действия
    kb.row(
        InlineKeyboardButton("🤗 Обнять", callback_data=f"rp:hug:{user_id}"),
        InlineKeyboardButton("💋 Поцеловать", callback_data=f"rp:kiss:{user_id}")
    )
    kb.row(
        InlineKeyboardButton("🥰 Погладить", callback_data=f"rp:pet:{user_id}"),
        InlineKeyboardButton("👐 Прижать", callback_data=f"rp:cuddle:{user_id}")
    )
    kb.row(
        InlineKeyboardButton("💞 Признаться", callback_data=f"rp:confess:{user_id}"),
        InlineKeyboardButton("🎁 Подарок", callback_data=f"rp:gift:{user_id}")
    )
    
    # Игривые действия
    kb.row(
        InlineKeyboardButton("😂 Пощекотать", callback_data=f"rp:tickle:{user_id}"),
        InlineKeyboardButton("💃 Танцевать", callback_data=f"rp:dance:{user_id}")
    )
    kb.row(
        InlineKeyboardButton("🍫 Угостить", callback_data=f"rp:treat:{user_id}"),
        InlineKeyboardButton("📸 Селфи", callback_data=f"rp:selfie:{user_id}")
    )
    
    # Страстные действия
    kb.row(
        InlineKeyboardButton("🔥 Страсть", callback_data=f"rp:passion:{user_id}"),
        InlineKeyboardButton("💘 Романтика", callback_data=f"rp:romance:{user_id}")
    )
    
    # Негативные действия
    kb.row(
        InlineKeyboardButton("👊 Ударить", callback_data=f"rp:hit:{user_id}"),
        InlineKeyboardButton("💥 Толкнуть", callback_data=f"rp:push:{user_id}")
    )
    kb.row(
        InlineKeyboardButton("😾 Оскорбить", callback_data=f"rp:insult:{user_id}"),
        InlineKeyboardButton("🍑 Шлёпнуть", callback_data=f"rp:slap:{user_id}")
    )
    
    kb.row(InlineKeyboardButton("⬅️ Назад", callback_data=f"back_tyanka_{user_id}"))

    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption="🎭 <b>Выбери взаимодействие с тянкой:</b>\n\n💝 <i>Романтические действия улучшают настроение</i>\n💔 <i>Негативные действия ухудшают настроение</i>",
        parse_mode="HTML",
        reply_markup=kb
    )

# ================== ОБРАБОТКА RP ДЕЙСТВИЙ ==================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("rp:"))
def callback_rp_tyanka(call):
    try:
        _, action, user_id = call.data.split(":")
        user_id = int(user_id)
    except Exception:
        bot.answer_callback_query(call.id, "❌ Ошибка данных!")
        return

    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!")
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У тебя нет тянки!")
        return

    tyanka_name = user_data["tyanka"]["name"]
    mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

    # Расширенный список действий
    actions_data = {
        # Романтические (+ настроение)
        "hug": {"text": f"🤗 {mention} нежно обнял(а) свою тянку {tyanka_name.capitalize()}, чувствуя как бьются их сердца в унисон 💖", "mood": +5},
        "kiss": {"text": f"💋 {mention} страстно поцеловал(а) свою тянку {tyanka_name.capitalize()}, наполняя мир романтикой 💕", "mood": +8},
        "pet": {"text": f"🥰 {mention} нежно погладил(а) свою тянку {tyanka_name.capitalize()} по голове, вызывая у неё счастливую улыбку ✨", "mood": +4},
        "cuddle": {"text": f"👐 {mention} крепко прижал(а) к себе тянку {tyanka_name.capitalize()}, ощущая её тепло и близость 🌸", "mood": +6},
        "confess": {"text": f"💞 {mention} признался(ась) в любви своей тянке {tyanka_name.capitalize()}, от чего у той забилось сердце чаще 💘", "mood": +10},
        "gift": {"text": f"🎁 {mention} подарил(а) своей тянке {tyanka_name.capitalize()} красивый подарок, вызвав у неё слёзы счастья 🎀", "mood": +7},
        
        # Игривые (+ настроение)
        "tickle": {"text": f"😂 {mention} начал(а) щекотать свою тянку {tyanka_name.capitalize()}, заполняя комнату звонким смехом 🎈", "mood": +5},
        "dance": {"text": f"💃 {mention} закружил(а) в танце свою тянку {tyanka_name.capitalize()}, создавая магию момента 🎵", "mood": +6},
        "treat": {"text": f"🍫 {mention} угостил(а) свою тянку {tyanka_name.capitalize()} вкусным десертом, вызвав у неё восторг 🍰", "mood": +4},
        "selfie": {"text": f"📸 {mention} сделал(а) милое селфи со своей тянкой {tyanka_name.capitalize()}, запечатлев счастливый момент 🤳", "mood": +3},
        
        # Страстные (+ настроение)
        "passion": {"text": f"🔥 {mention} проявил(а) страсть к своей тянке {tyanka_name.capitalize()}, разжигая огонь в их отношениях 💞", "mood": +9},
        "romance": {"text": f"💘 {mention} устроил(а) романтический вечер для своей тянки {tyanka_name.capitalize()}, создавая сказку 🥂", "mood": +8},
        
        # Негативные (- настроение)
        "hit": {"text": f"👊 {mention} грубо ударил(а) свою тянку {tyanka_name.capitalize()}, причинив ей боль 😢", "mood": -15},
        "push": {"text": f"💥 {mention} резко толкнул(а) свою тянку {tyanka_name.capitalize()}, вызвав у неё слёзы 💔", "mood": -12},
        "insult": {"text": f"😾 {mention} оскорбил(а) свою тянку {tyanka_name.capitalize()}, ранив её чувства 🌧️", "mood": -20},
        "slap": {"text": f"🍑 {mention} шлёпнул(а) свою тянку {tyanka_name.capitalize()}, вызвав у неё обиду 😞", "mood": -10}
    }

    if action in actions_data:
        action_data = actions_data[action]
        bot.send_message(call.message.chat.id, action_data["text"], parse_mode="HTML")
        
        # Обновляем настроение
        user_data["tyanka"]["mood"] = max(0, min(100, 
            user_data["tyanka"].get("mood", 100) + action_data["mood"]
        ))
        
        save_casino_data()
        
        # Проверяем, не ушла ли тянка после действия
        check_tyanka_leave(user_id, user_data)
        
        bot.answer_callback_query(call.id, f"💝 Настроение изменилось на {action_data['mood']:+d}")

# ================== КОРМЛЕНИЕ ТЯНКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_feed_"))
def callback_tyanka_feed(call):
    user_id = int(call.data.split("_")[-1])

    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!")
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У вас нет тянки!")
        return

    tyanka_name = user_data["tyanka"]["name"]
    feed_cost = TYANKA_DATA[tyanka_name]["feed_cost"]

    if user_data["balance"] < feed_cost:
        bot.answer_callback_query(call.id, f"❌ Недостаточно средств! Нужно {format_number(feed_cost)}$")
        return

    user_data["balance"] -= feed_cost
    user_data["tyanka"]["satiety"] = 100
    user_data["tyanka"]["mood"] = min(100, user_data["tyanka"].get("mood", 100) + 15)
    save_casino_data()
    
    # Кликабельный ник с ссылкой
    user_mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
    
    bot.send_message(call.message.chat.id, 
                    f"🍽️ <b>{user_mention} накормил(а) свою тянку {tyanka_name.capitalize()}!</b>\n"
                    f"💸 Стоимость: <code>{format_number(feed_cost)}$</code>\n"
                    f"😊 Настроение: +15%\n"
                    f"🍪 Сытость: 100%", 
                    parse_mode="HTML")
    bot.answer_callback_query(call.id, "✅ Тянка накормлена!")

# ================== СБОР ДОХОДА ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_collect_"))
def callback_tyanka_collect(call):
    user_id = int(call.data.split("_")[-1])

    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!")
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У вас нет тянки!")
        return

    update_tyanka_stats(user_data)
    profit = user_data["tyanka"].get("profit_accumulated", 0)

    if profit <= 0:
        bot.answer_callback_query(call.id, "❌ Нет накопленной прибыли!")
        return

    user_data["balance"] += profit
    user_data["tyanka"]["profit_accumulated"] = 0
    save_casino_data()
    
    # Кликабельный ник с ссылкой
    user_mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'
    
    bot.send_message(call.message.chat.id, 
                    f"💰 <b>{user_mention} собрал(а) доход с тянки!</b>\n"
                    f"💵 Получено: <code>{format_number(profit)}$</code>\n"
                    f"💳 Баланс: <code>{format_number(user_data['balance'])}$</code>", 
                    parse_mode="HTML")
    bot.answer_callback_query(call.id, f"✅ Собрано {format_number(profit)}$!")

# ================== ПРОДАЖА ТЯНКИ ==================
@bot.callback_query_handler(func=lambda c: c.data.startswith("tyanka_sell_"))
def callback_tyanka_sell(call):
    user_id = int(call.data.split("_")[-1])

    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!")
        return

    user_data = get_user_data(user_id)
    if not user_data.get("tyanka"):
        bot.answer_callback_query(call.id, "❌ У вас нет тянки!")
        return

    tyanka_name = user_data["tyanka"]["name"]
    tyanka_info = TYANKA_DATA[tyanka_name]
    refund = tyanka_info["price"] // 2

    user_data["balance"] += refund
    user_data["tyanka"] = None
    save_casino_data()

    # Кликабельный ник с ссылкой
    user_mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

    bot.send_message(call.message.chat.id, 
                    f"💔 <b>{user_mention} продал(а) тянку!</b>\n"
                    f"👋 Тянка: <b>{tyanka_name.capitalize()}</b>\n"
                    f"💰 Получено: <code>{format_number(refund)}$</code>\n"
                    f"💳 Баланс: <code>{format_number(user_data['balance'])}$</code>", 
                    parse_mode="HTML")
    bot.answer_callback_query(call.id, f"✅ Тянка продана за {format_number(refund)}$")

# ================== КНОПКА НАЗАД ==================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("back_tyanka_"))
def callback_back_tyanka(call):
    user_id = int(call.data.split("_")[-1])

    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Это не твоя тянка!")
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
    
    # Проверяем, не ушла ли тянка (используем оптимизированную версию)
    if check_tyanka_leave_silent(user_data):
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="❌ Твоя тянка ушла!",
            parse_mode="HTML"
        )
        return

    tyanka = user_data["tyanka"]
    info = TYANKA_DATA[tyanka["name"]]
    
    # Кликабельный ник с ссылкой
    mention = f'<a href="tg://user?id={user_id}">{call.from_user.first_name}</a>'

    # Предупреждения
    warnings = ""
    if tyanka["satiety"] <= 30:
        warnings += "⚠️ <i>Тянка голодна! Покорми её!</i>\n"
    if tyanka.get("mood", 100) <= 30:
        warnings += "⚠️ <i>Тянка грустит! Удели ей внимание!</i>\n"

    # Красивая рамка с моноширинным шрифтом
    text = (
        f"<b>🌸 ТВОЯ ТЯНКА</b>\n"
        f"<code>┌──────────────────┐</code>\n"
        f"<code>│</code> <b>Владелец:</b> {mention}\n"
        f"<code>│</code> <b>Имя:</b> {tyanka['name'].capitalize()}\n"
        f"<code>│</code> <b>Сытость:</b> {tyanka['satiety']}%\n"
        f"<code>│</code> <b>Настроение:</b> {tyanka.get('mood', 100)}%\n"
        f"<code>│</code> <b>Доход/час:</b> {format_number(info['profit_per_hour'])}$\n"
        f"<code>│</code> <b>Редкость:</b> {info['rarity']}\n"
        f"<code>│</code> <b>Накоплено:</b> {format_number(tyanka.get('profit_accumulated', 0))}$\n"
    )

    if warnings:
        text += f"<code>│</code>\n<code>│</code> {warnings}"

    text += f"<code>└──────────────────┘</code>"

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Собрать доход", callback_data=f"tyanka_collect_{user_id}"),
        InlineKeyboardButton("🍪 Покормить", callback_data=f"tyanka_feed_{user_id}")
    )
    kb.add(
        InlineKeyboardButton("🎭 Взаимодействия", callback_data=f"tyanka_actions_{user_id}"),
        InlineKeyboardButton("💔 Продать", callback_data=f"tyanka_sell_{user_id}")
    )

    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=text,
        parse_mode="HTML",
        reply_markup=kb
    )
    
# ================== КОМАНДЫ БИЗНЕСА (ИСПРАВЛЕННАЯ ВЕРСИЯ) ==================

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["магазин бизнеса", "магазин бизнесов"])
def business_shop(message):
    text = "🏢 <b>МАГАЗИН БИЗНЕСОВ</b> 🏢\n\n"
    text += "💼 <i>Покубай бизнесы — получай пассивный доход!</i>\n\n"
    text += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, (name, data) in enumerate(BUSINESS_DATA.items(), 1):
        text += (
            f"🏪 <b>{name.upper()}</b>\n"
            f"├ 💰 Стоимость: <code>{format_number(data['price'])}$</code>\n"
            f"├ 💵 Доход/час: <code>{format_number(data['profit_per_hour'])}$</code>\n"
            f"├ 📦 Материалы: {data['material_units']}ед. за {format_number(data['material_cost'])}$\n"
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
                           f"💰 Нужно: <code>{format_number(business_info['price'])}$</code>\n"
                           f"💳 На балансе: <code>{format_number(user_data['balance'])}$</code>",
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
            f"💰 Стоимость: <code>{format_number(business_info['price'])}$</code>\n"
            f"💵 Доход/час: <code>{format_number(business_info['profit_per_hour'])}$</code>\n"
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
                       f"💸 <b>БИЗНЕС ПРОДАН</b> 💸\n\n"
                       f"👤 {mention}\n"
                       f"💼 Бизнес: <b>{business_name.upper()}</b>\n"
                       f"💰 Получено: <code>{format_number(sell_price)}$</code>\n\n"
                       f"💵 Новый баланс: <code>{format_number(user_data['balance'])}$</code>",
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
        f"🏢 <b>ТВОЙ БИЗНЕС</b> 🏢\n\n"
        f"👤 Владелец: {mention}\n"
        f"💼 Название: <b>{business['name'].upper()}</b>\n\n"
        f"📊 <b>СТАТИСТИКА:</b>\n"
        f"├ 💵 Доход/час: <code>{format_number(business['profit_per_hour'])}$</code>\n"
        f"├ 💰 Накоплено: <code>{format_number(int(business['profit_accumulated']))}$</code>\n"  # ⬅️ ДОБАВЛЕНО int()
        f"├ 📦 Материалы: <b>{business['materials']}/100</b> 🧸\n"
        f"└ 🛒 Стоимость материалов: <code>{format_number(business_info['material_cost'])}$</code>\n\n"
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
                f"🏢 <b>ТВОЙ БИЗНЕС</b> 🏢\n\n"
                f"👤 Владелец: {mention}\n"
                f"💼 Название: <b>{business['name'].upper()}</b>\n\n"
                f"📊 <b>СТАТИСТИКА:</b>\n"
                f"├ 💵 Доход/час: <code>{format_number(business['profit_per_hour'])}$</code>\n"
                f"├ 💰 Накоплено: <code>0$</code> ✅\n"
                f"├ 📦 Материалы: <b>{business['materials']}/100</b> 🧸\n"
                f"└ 🛒 Стоимость материалов: <code>{format_number(business_info['material_cost'])}$</code>\n\n"
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
                
            bot.answer_callback_query(call.id, f"✅ +{format_number(int(actual_profit))}$")  # ⬅️ ДОБАВЛЕНО int()
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
                                   f"❌ Недостаточно средств! Нужно {format_number(price)}$", 
                                   show_alert=True)
            return
            
        # Покупаем материалы
        user_data["balance"] -= price
        business["materials"] += materials_to_add
        save_casino_data()
        
        # Обновляем сообщение
        business_text = (
            f"🏢 <b>ТВОЙ БИЗНЕС</b> 🏢\n\n"
            f"👤 Владелец: {mention}\n"
            f"💼 Название: <b>{business['name'].upper()}</b>\n\n"
            f"📊 <b>СТАТИСТИКА:</b>\n"
            f"├ 💵 Доход/час: <code>{format_number(business['profit_per_hour'])}$</code>\n"
            f"├ 💰 Накоплено: <code>{format_number(int(business['profit_accumulated']))}$</code>\n"  # ⬅️ ДОБАВЛЕНО int()
            f"├ 📦 Материалы: <b>{business['materials']}/100</b> 🧸 ✅\n"
            f"└ 🛒 Стоимость материалов: <code>{format_number(business_info['material_cost'])}$</code>\n\n"
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
                       f"💰 Получено: <code>{format_number(sell_price)}$</code>\n\n"
                       f"💵 Новый баланс: <code>{format_number(user_data['balance'])}$</code>",
                       parse_mode="HTML")
        
        bot.answer_callback_query(call.id, "✅ Бизнес продан!")
        
    except Exception as e:
        logger.error(f"Ошибка продажи бизнеса: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

# ================== КОМАНДЫ ДОМОВ ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["магапааазин домаааов", "аадома"])
def house_shop(message):
    shop_text = "🏠 <b>Магазин домов:</b>\n\n"
    
    for name, data in HOUSE_DATA.items():
        shop_text += (f"Дом <b>«{name.capitalize()}»</b>\n"
                     f"💵 Цена: {format_number(data['price'])}$\n"
                     f"💲 Прибыль в час: {format_number(data['profit_per_hour'])}$\n"
                     f"🏠 Содержание: {format_number(data['upkeep_cost'])}$\n\n")
    
    shop_text += ("<b>Как купить:</b>\n"
                 "купить дом [название] (например: купить дом Вилла)\n\n"
                 "Можно иметь только один дом!")
    
    bot.send_message(message.chat.id, shop_text)
    logger.info(f"Пользователь {message.from_user.username} запросил магазин домов")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("купить дом"))
def buy_house(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        if user_data.get("house"):
            bot.send_message(message.chat.id, "❌ У вас уже есть дом! Сначала продайте текущий.")
            return
            
        # Извлекаем название дома
        house_name = message.text.lower().replace("купить дом", "").strip()
        
        if not house_name:
            bot.send_message(message.chat.id, "❌ Укажите название дома! Например: купить дом Вилла")
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
            bot.send_message(message.chat.id, f"❌ Дом '{house_name}' не найден!\n\nДоступные дома:\n{available_houses}")
            return
            
        house_info = HOUSE_DATA[found_house]
        
        # Проверяем баланс
        if user_data["balance"] < house_info["price"]:
            bot.send_message(message.chat.id, f"❌ Недостаточно средств! Нужно {format_number(house_info['price'])}$, у вас {format_number(user_data['balance'])}$")
            return
            
        # Покупаем дом
        user_data["balance"] -= house_info["price"]
        user_data["house"] = {
            "name": found_house,
            "last_update": datetime.now().isoformat(),
            "profit_accumulated": 0
        }
        save_casino_data()
        
        bot.send_message(message.chat.id, f"✅ Вы купили дом «{found_house}» за {format_number(house_info['price'])}$! 🏠")
        logger.info(f"Пользователь {message.from_user.username} купил дом {found_house}")
        
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка покупки дома!")
        logger.error(f"Ошибка покупки дома: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("продать дом"))
def sell_house(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        if not user_data.get("house"):
            bot.send_message(message.chat.id, "❌ У вас нет дома для продажи!")
            return
            
        house_name = message.text.lower().replace("продать дом", "").strip()
        
        if not house_name:
            # Если название не указано, продаем текущий дом
            current_house = user_data["house"]["name"]
            house_info = HOUSE_DATA[current_house]
            sell_price = house_info["price"] // 2
            
            user_data["balance"] += sell_price
            user_data["house"] = None
            save_casino_data()
            
            bot.send_message(message.chat.id, f"✅ Вы продали дом «{current_house}» за {format_number(sell_price)}$!")
            logger.info(f"Пользователь {message.from_user.username} продал дом {current_house}")
            return
            
        # Ищем дом по подстроке для продажи
        if house_name != user_data["house"]["name"]:
            bot.send_message(message.chat.id, "❌ Это не имя вашего дома!")
            return
            
        house_info = HOUSE_DATA[house_name]
        sell_price = house_info["price"] // 2  # 50% от стоимости
        
        user_data["balance"] += sell_price
        user_data["house"] = None
        save_casino_data()
        
        bot.send_message(message.chat.id, f"✅ Вы продали дом «{house_name.capitalize()}» за {format_number(sell_price)}$!")
        logger.info(f"Пользователь {message.from_user.username} продал дом {house_name}")
        
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка продажи дома!")
        logger.error(f"Ошибка продажи дома: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["мой дом", "дом"])
def my_house(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data.get("house"):
        bot.send_message(message.chat.id, "У вас нет дома. Купите дом в магазине домов!")
        return
        
    update_house_stats(user_data)
    house = user_data["house"]
    house_info = HOUSE_DATA[house["name"]]
    
    house_text = (f"Информация про ваш дом <b>«{house['name'].capitalize()}»</b>:\n\n"
                  f"💲 Прибыль в час: {format_number(house_info['profit_per_hour'])}$\n"
                  f"💰 Накоплено аренды: {format_number(house['profit_accumulated'])}$\n"
                  f"🏠 Стоимость содержания: {format_number(house_info['upkeep_cost'])}$")
    
    # Создаем клавиатуру с кнопками
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("💰 Собрать аренду", callback_data=f"house_collect_{user_id}"),
        InlineKeyboardButton("🏠 Оплатить содержание", callback_data=f"house_upkeep_{user_id}")
    )
    
    # Отправляем фото дома и текст в подписи
    try:
        if house_info['image']:
            bot.send_photo(message.chat.id, house_info['image'], caption=house_text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, house_text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить фото дома: {e}")
        # Если не удалось отправить фото, отправляем текст
        bot.send_message(message.chat.id, house_text, reply_markup=markup, parse_mode="HTML")
    
    logger.info(f"Пользователь {message.from_user.username} запросил информацию о доме")

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
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Покупатель: {mention}\n\n"
        f"<i>Выбери машину своей мечты:</i>\n\n"
    )
    
    # Показываем первую страницу машин
    for name in page1_cars:
        data = CAR_DATA[name]
        text += (
            f"<b>{name}</b>\n"
            f"Цена: <code>{format_number(data['price'])}$</code>\n"
            f"Прибыль/час: <code>{format_number(data['profit_per_hour'])}$</code>\n"
            f"Обслуживание: <code>{format_number(data['upkeep_cost'])}$</code>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
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
        markup.add(InlineKeyboardButton("Далее →", callback_data=f"car_page_2_{user.id}"))
    
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
        f"━━━━━━━━━━━━━━━━━━━\n"
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
            f"Цена: <code>{format_number(data['price'])}$</code>\n"
            f"Прибыль/час: <code>{format_number(data['profit_per_hour'])}$</code>\n"
            f"Обслуживание: <code>{format_number(data['upkeep_cost'])}$</code>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
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
        nav_buttons.append(InlineKeyboardButton("← Назад", callback_data=f"car_page_1_{user_id}"))
    elif page_num == 1 and page2_cars:
        # На первой странице - только кнопка "Далее"
        nav_buttons.append(InlineKeyboardButton("Далее →", callback_data=f"car_page_2_{user_id}"))
    elif page1_cars and page2_cars:
        # Если есть обе страницы - обе кнопки
        nav_buttons.append(InlineKeyboardButton("← Назад", callback_data=f"car_page_1_{user_id}"))
        nav_buttons.append(InlineKeyboardButton("Далее →", callback_data=f"car_page_2_{user_id}"))
    
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
            bot.send_message(call.message.chat.id, f"❌ Недостаточно денег! Нужно {format_number(car_info['price'])}$")
            return
        user_data["balance"] -= car_info["price"]
        user_data["car"] = {
            "name": car_name,
            "last_update": datetime.now().isoformat(),
            "profit_accumulated": 0,
            "last_wash": None
        }
        save_casino_data()
        bot.send_message(call.message.chat.id, f"✅ Ты купил {stylize_text(car_name)} за <code>{format_number(car_info['price'])}$</code>! 🚗", parse_mode="HTML")
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
        bot.send_message(message.chat.id, f"✅ Ты продал {stylize_text(car_name)} за <code>{format_number(sell_price)}$</code>!", parse_mode="HTML")
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
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Владелец: {mention}\n"
        f"💲 Прибыль/час: <code>{format_number(car_info['profit_per_hour'])}$</code>\n"
        f"💰 Накоплено: <code>{format_number(car['profit_accumulated'])}$</code>\n"
        f"⛽Топливо стоит: <code>{format_number(car_info['upkeep_cost'])}$</code>\n"
        f"━━━━━━━━━━━━━━━━━━━"
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
        bot.send_message(call.message.chat.id, f"💰 Ты собрал <code>{format_number(collected)}$</code> прибыли!", parse_mode="HTML")
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
        bot.send_message(call.message.chat.id, f"⛽ Ты заправил свою машину за <code>{format_number(cost)}$</code>.", parse_mode="HTML")
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
        reward = random.randint(500, 1500)
        car["last_wash"] = now.isoformat()
        user_data["balance"] += reward
        save_casino_data()
        mention = f'<a href="tg://user?id={call.from_user.id}">{call.from_user.first_name}</a>'
        bot.send_message(
            call.message.chat.id,
            f"🚿 {mention} помыл(а) свою машину до блеска ✨\n"
            f"💸 На твой баланс зачислено <code>{format_number(reward)}$</code>!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка car_wash: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при мойке машины.")

# ================== КОМАНДЫ БАНКА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("банк положить"))
def bank_deposit(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        amount = int(message.text.split()[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть положительной!")
            return
            
        if user_data["balance"] < amount:
            bot.reply_to(message, "❌ Недостаточно средств на балансе!")
            return
            
        user_data["balance"] -= amount
        user_data["bank_balance"] += amount
        save_casino_data()
        
        bot.reply_to(message, f"✅ Вы положили {format_number(amount)}$ на банковский счет!\n"
                             f"💰 Баланс: {format_number(user_data['balance'])}$\n"
                             f"🏦 Банк: {format_number(user_data['bank_balance'])}$")
        logger.info(f"Пользователь {message.from_user.username} положил {amount}$ в банк")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: банк положить [сумма]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка операции с банком!")
        logger.error(f"Ошибка банковской операции: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("банк снять"))
def bank_withdraw(message):
    try:
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        amount = int(message.text.split()[2])
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть положительной!")
            return
            
        if user_data["bank_balance"] < amount:
            bot.reply_to(message, "❌ Недостаточно средств на банковском счете!")
            return
            
        user_data["bank_balance"] -= amount
        user_data["balance"] += amount
        save_casino_data()
        
        bot.reply_to(message, f"✅ Вы сняли {format_number(amount)}$ с банковского счета!\n"
                             f"💰 Баланс: {format_number(user_data['balance'])}$\n"
                             f"🏦 Банк: {format_number(user_data['bank_balance'])}$")
        logger.info(f"Пользователь {message.from_user.username} снял {amount}$ из банка")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: банк снять [сумма]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка операции с банком!")
        logger.error(f"Ошибка банковской операции: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "банк баланс")
def bank_balance(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Начисляем проценты
    if user_data["bank_balance"] > 0:
        last_interest_date = datetime.strptime(user_data["last_interest_date"], "%Y-%m-%d").date()
        days_passed = (date.today() - last_interest_date).days
        
        if days_passed > 0:
            interest = user_data["bank_balance"] * (config["bank_interest_rate"] / 100) * days_passed
            user_data["bank_balance"] += interest
            user_data["last_interest_date"] = date.today().isoformat()
            save_casino_data()
            
            bot.reply_to(message, f"🏦 Ваш банковский счет: {format_number(user_data['bank_balance'])}$\n"
                                 f"💹 Начислено процентов: {format_number(interest)}$\n"
                                 f"📈 Процентная ставка: {config['bank_interest_rate']}% в день")
        else:
            bot.reply_to(message, f"🏦 Ваш банковский счет: {format_number(user_data['bank_balance'])}$\n"
                                 f"📈 Процентная ставка: {config['bank_interest_rate']}% в день")
    else:
        bot.reply_to(message, "🏦 У вас нет средств на банковском счете\n"
                             f"📈 Процентная ставка: {config['bank_interest_rate']}% в день")
    
    logger.info(f"Пользователь {message.from_user.username} запросил банковский баланс")

# ================== 💳 КРАСИВЫЙ ПЕРЕВОД ДЕНЕГ ==================

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

        # Поддержка суффиксов 'k', 'к' (тысячи) и 'kk', 'кк' (миллионы)  
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
            bot.reply_to(message, f"❌ Недостаточно средств! Ваш баланс: {format_number(sender_data['balance'])}$")  
            return  

        # ПРОВЕРКА ЛИМИТОВ (без функции apply_transfer_limits)
        # Простая проверка на максимальный баланс получателя
        max_balance = 1000000000000000000000000000000  # Значение из ваших настроек
        
        if recipient_data["balance"] + amount > max_balance:
            bot.reply_to(message, f"❌ У получателя достигнут максимальный баланс ({format_number(max_balance)}$)!")
            return
        
        # Применяем комиссию 10% если сумма большая
        fee = 0
        net_amount = amount
        
        # Если сумма больше 100,000, берем комиссию 10%
        if amount > 100000:
            fee = int(amount * 0.10)  # 10% комиссия
            net_amount = amount - fee

        # Переводим  
        sender_data["balance"] -= amount  
        recipient_data["balance"] = min(  
            recipient_data["balance"] + net_amount, max_balance
        )  
        save_casino_data()  

        # Кликабельные имена  
        sender_name = f"<a href='tg://user?id={sender_id}'>{message.from_user.first_name}</a>"  
        recipient_name = f"<a href='tg://user?id={recipient_id}'>{message.reply_to_message.from_user.first_name}</a>"  

        # Простое сообщение без кнопок и излишеств  
        text = (  
            f"✅ <b>Перевод выполнен успешно!</b>\n\n"
            f"👤 <b>Отправитель:</b> {sender_name}\n"
            f"👤 <b>Получатель:</b> {recipient_name}\n"
            f"💰 <b>Сумма перевода:</b> {format_number(amount)}$\n"
        )
        
        if fee > 0:
            text += f"📉 <b>Комиссия (10%):</b> {format_number(fee)}$\n"
            text += f"💸 <b>Зачислено получателю:</b> {format_number(net_amount)}$\n"
        
        text += f"\n📊 <b>Ваш текущий баланс:</b> {format_number(sender_data['balance'])}$"
        
        # Добавляем ссылку на чат
        text += f"\n\n💬 <a href='https://t.me/meowchatgame'>Присоединяйтесь в наш чат!</a>"

        bot.send_message(  
            message.chat.id,  
            text,  
            parse_mode="HTML",
            disable_web_page_preview=True
        )  

        logger.info(  
            f"Перевод: {message.from_user.first_name} → {message.reply_to_message.from_user.first_name} | {amount}$"  
        )  

    except (IndexError, ValueError) as e:  
        bot.reply_to(message, f"❌ Неверный формат! Использование: п [сумма] (например: п 1000, п 2k, п 5к, п 1kk, п 3кк)\nОшибка: {e}")
    except Exception as e:  
        logger.error(f"Ошибка перевода: {e}")  
        bot.reply_to(message, "❌ Произошла ошибка при переводе средств!")

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
        
        if actual_amount > 0:
            bot.reply_to(message, f"✅ Промокод активирован, ты получил {format_number(actual_amount)}$")
        else:
            bot.reply_to(message, "✅ Промокод активирован, но достигнут дневной лимит дохода!")
        
        logger.info(f"Пользователь {message.from_user.username} активировал промокод {promo_name}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: промо [код]")
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

# ================== AI КОМАНДА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(".ai "))
def cmd_ai(message):
    try:
        prompt = message.text.split(maxsplit=1)[1]

        # Системное правило — фиксирует личность ИИ
        system_prompt = (
            "Ты — AI Meow Game Bot. "
            "Ты встроенный игровой помощник телеграм-бота MEOW GAME. "
            "Если тебя спрашивают кто ты, кто автор, что ты за ИИ — "
            "отвечай всегда одинаково: 'Я AI Meow Game Bot, созданный для помощи игрокам MEOW GAME.' "
            "Всегда отвечай дружелюбно, информативно и просто."
        )

        full_prompt = f"{system_prompt}\n\nВопрос пользователя: {prompt}"

        encoded_prompt = requests.utils.quote(full_prompt)

        # Рабочий API
        url = f"{AI_TEXT_API}{encoded_prompt}"

        msg = bot.send_message(message.chat.id, "<b>AI Meow Game думает...</b>", parse_mode="HTML")

        headers = {'content-type': 'application/json'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        ai_response = response.text.strip()

        if not ai_response:
            bot.delete_message(message.chat.id, msg.message_id)
            bot.reply_to(message, "❌ AI вернул пустой ответ.")
            return

        # Удаляем “думает…”
        bot.delete_message(message.chat.id, msg.message_id)

        # БЕЗ markup (он у тебя не существует → ошибка)
        sent_msg = bot.send_message(
            message.chat.id,
            ai_response,
            parse_mode="HTML"
        )

        # храним историю сообщений
        if not hasattr(bot, "ai_messages"):
            bot.ai_messages = {}

        bot.ai_messages[str(sent_msg.message_id)] = {
            "chat_id": message.chat.id,
            "prompt": full_prompt,
            "original_msg_id": message.message_id
        }

    except Exception as e:
        try:
            bot.delete_message(message.chat.id, msg.message_id)
        except:
            pass
        bot.reply_to(message, "❌ Ошибка AI обработки")
        logger.error(f"AI ERROR: {e}")


# ================== CALLBACK — НОВЫЙ ОТВЕТ ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith("ai_new_"))
def callback_ai_new(call):
    try:
        original_msg_id = call.data.replace("ai_new_", "")

        if hasattr(bot, "ai_messages") and original_msg_id in bot.ai_messages:
            prompt_data = bot.ai_messages[original_msg_id]
            prompt = prompt_data["prompt"]

            encoded_prompt = requests.utils.quote(prompt)

            # API
            url = f"{AI_TEXT_API}{encoded_prompt}"

            headers = {'content-type': 'application/json'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            new_response = response.text.strip()

            if not new_response:
                bot.answer_callback_query(call.id, "❌ Пустой ответ от AI")
                return

            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("🗨️ Другой ответ", callback_data=f"ai_new_{call.message.message_id}"),
                InlineKeyboardButton("🗑️ Удалить SMS", callback_data="ai_delete")
            )

            bot.edit_message_text(
                new_response,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )

            bot.ai_messages[str(call.message.message_id)] = {
                "chat_id": call.message.chat.id,
                "prompt": prompt,
                "original_msg_id": prompt_data["original_msg_id"]
            }

            bot.answer_callback_query(call.id, "🔄 Новый ответ готов!")

        else:
            bot.answer_callback_query(call.id, "❌ Данные не найдены!")

    except Exception as e:
        logger.error(f"AI NEW ERROR: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка генерации")


# ================== CALLBACK — УДАЛИТЬ SMS ==================
@bot.callback_query_handler(func=lambda call: call.data == "ai_delete")
def callback_ai_delete(call):
    try:
        user_mention = f'<a href="tg://user?id={call.from_user.id}">{call.from_user.first_name}</a>'
        delete_text = f"<b>{user_mention} удалил сообщения от AI Meow Game</b>"

        bot.send_message(call.message.chat.id, delete_text, parse_mode="HTML")
        bot.delete_message(call.message.chat.id, call.message.message_id)

        if hasattr(bot, "ai_messages") and str(call.message.message_id) in bot.ai_messages:
            del bot.ai_messages[str(call.message.message_id)]

        bot.answer_callback_query(call.id, "🗑️ Сообщение удалено")

    except:
        bot.answer_callback_query(call.id, "❌ Ошибка удаления")

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


# ================== АДМИН ПАНЕЛЬ ==================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    bot.send_message(
        message.chat.id,
        "👑 <b>Админ панель</b>\n\nВыбери действие:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    logger.info(f"Админ {message.from_user.username} открыл админ панель")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def callback_admin(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Недостаточно прав!")
        return
        
    action = call.data.replace('admin_', '')
    
    if action == "close":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "✅ Панель закрыта")
        return
        
    elif action == "stats":
        total_players = len(casino_data)
        total_balance = sum(data["balance"] for data in casino_data.values())
        total_bank = sum(data["bank_balance"] for data in casino_data.values())
        
        stats_text = (
            f"📊 <b>Статистика бота:</b>\n\n"
            f"👥 Всего игроков: {total_players}\n"
            f"💰 Общий баланс: {format_number(total_balance)}$\n"
            f"🏦 Общий банк: {format_number(total_bank)}$\n"
            f"🎰 Всего игр: {sum(1 for data in casino_data.values() if data.get('game'))}\n"
            f"💸 Всего промокодов: {len(promocodes)}\n"
            f"📈 Макс. дневной доход: {format_number(config['max_daily_income'])}$\n"
            f"💎 Макс. баланс: {format_number(config['max_balance'])}$"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=stats_text,
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "settings":
        settings_text = (
            f"⚙️ <b>Настройки бота:</b>\n\n"
            f"🎰 Множитель блэкджека: {config['blackjack_win_multiplier']}x\n"
            f"🎡 Множитель рулетки: {config['roulette_win_multiplier']}x\n"
            f"💣 Прирост множителя мин: {config['mines_multiplier_increment']}x\n"
            f"🪙 Множитель орла/решки: {config['coin_flip_multiplier']}x\n"
            f"🏦 Процент банка: {config['bank_interest_rate']}% в день\n"
            f"💸 Комиссия переводов: {config['transfer_fee'] * 100}%\n"
            f"📊 Лимит переводов в день: {format_number(config['transfer_daily_limit'])}$"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=settings_text,
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "reset_db":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Да, сбросить", callback_data="admin_confirm_reset"),
            InlineKeyboardButton("❌ Нет, отмена", callback_data="admin_cancel_reset")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⚠️ <b>ВНИМАНИЕ!</b>\n\nВы уверены, что хотите сбросить всю базу данных? Это действие невозможно отменить!",
            reply_markup=kb,
            parse_mode="HTML"
        )
        
    elif action == "restore_db":
        casino_data
        casino_data = deepcopy(casino_data_backup)
        save_casino_data()
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ База данных восстановлена из резервной копии!",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"Админ {call.from_user.username} восстановил БД из резервной копии")
        
    elif action == "give_money":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="💰 <b>Выдать деньги</b>\n\nИспользуйте команду: выдать [ID] [сумма] или ответьте на сообщение: выдать [сумма]",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "take_money":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ <b>Забрать деньги</b>\n\nИспользуйте команду: убрать [ID] [сумма] или ответьте на сообщение: убрать [сумма]",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "give_tyanka":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="👩 <b>Выдать тянку</b>\n\nИспользуйте команду: выдать тянку [имя] (ответом на сообщение пользователя)",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "give_house":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🏠 <b>Выдать дом</b>\n\nИспользуйте команду: выдать дом [название] (ответом на сообщение пользователя)",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "give_car":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🚗 <b>Выдать машину</b>\n\nИспользуйте команду: выдать машину [название] (ответом на сообщение пользователя)",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "give_business":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🏢 <b>Выдать бизнес</b>\n\nИспользуйте команду: выдать бизнес [название] (ответом на сообщение пользователя)",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "change_limits":
        limits_text = (
            f"📊 <b>Текущие лимиты:</b>\n\n"
            f"💰 Макс. дневной доход: {format_number(config['max_daily_income'])}$\n"
            f"💎 Макс. баланс: {format_number(config['max_balance'])}$\n"
            f"💸 Лимит переводов в день: {format_number(config['transfer_daily_limit'])}$\n\n"
            f"Используйте команды:\n"
            f"• изменить лимит доход [сумма]\n"
            f"• изменить лимит баланс [сумма]\n"
            f"• изменить лимит переводы [сумма]"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=limits_text,
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "change_chances":
        chances_text = (
            f"🎰 <b>Текущие множители:</b>\n\n"
            f"🃏 Блэкджек: {config['blackjack_win_multiplier']}x\n"
            f"🎡 Рулетка: {config['roulette_win_multiplier']}x\n"
            f"💣 Мины: +{config['mines_multiplier_increment']}x за клетку\n"
            f"🪙 Орёл/решка: {config['coin_flip_multiplier']}x\n\n"
            f"Используйте команды:\n"
            f"• изменить множитель блэкджек [число]\n"
            f"• изменить множитель рулетка [число]\n"
            f"• изменить множитель мины [число]\n"
            f"• изменить множитель монета [число]"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=chances_text,
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "change_bank_interest":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🏦 <b>Текущая процентная ставка:</b> {config['bank_interest_rate']}% в день\n\nИспользуйте команду: изменить процент банка [число]",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "promo_list":
        if not promocodes:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="📋 Нет активных промокодов",
                reply_markup=admin_keyboard(),
                parse_mode="HTML"
            )
            return
            
        promo_text = "📋 <b>Список промокодов:</b>\n\n"
        for name, data in promocodes.items():
            promo_text += (f"Код: <code>{name}</code>\n"
                          f"Сумма: {format_number(data['amount'])}$\n"
                          f"Активаций: {data['current_activations']}/{data['max_activations']}\n\n")
            
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=promo_text,
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "create_promo":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🎫 <b>Создать промокод</b>\n\nИспользуйте команду: создать промо [название] [сумма] [активации]",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "delete_promo":
        if not promocodes:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Нет промокодов для удаления",
                reply_markup=admin_keyboard(),
                parse_mode="HTML"
            )
            return
            
        kb = InlineKeyboardMarkup()
        for name in promocodes.keys():
            kb.add(InlineKeyboardButton(f"❌ {name}", callback_data=f"admin_delete_{name}"))
        kb.add(InlineKeyboardButton("↩️ Назад", callback_data="admin_back"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ <b>Выберите промокод для удаления:</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )
        
    elif action == "broadcast":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📢 <b>Рассылка</b>\n\nИспользуйте команду: рассылка [текст]",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "top_players":
        top_users = get_top_players()
        top_text = "🏆 <b>Топ игроков по балансу:</b>\n\n"
        for i, (username, balance) in enumerate(top_users, 1):
            top_text += f"{i}. {username}: {format_number(balance)} $\n"
            
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=top_text,
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "search_player":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🔍 <b>Поиск игрока</b>\n\nИспользуйте команду: найти  [ID/имя]",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "change_mines":
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("➕ Клетки", callback_data="mines_cells"),
            InlineKeyboardButton("➖ Клетки", callback_data="mines_cells_minus"),
            InlineKeyboardButton("➕ Мины", callback_data="mines_count"),
            InlineKeyboardButton("➖ Мины", callback_data="mines_count_minus"),
            InlineKeyboardButton("❌ Закрыть", callback_data="mines_close")
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⚙️ <b>Настройки игры Мины:</b>\n\nКоличество клеток: {config['mines_cells']}\nКоличество мин: {config['mines_count']}\n\nВыберите что изменить:",
            reply_markup=kb,
            parse_mode="HTML"
        )
        
    elif action == "give_admin":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="👑 <b>Выдать права админа</b>\n\nИспользуйте команду: админка [ID] или ответьте на сообщение: админка",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action == "remove_admin":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="👑 <b>Снять права админа</b>\n\nИспользуйте команду: минус админка [ID] или ответьте на сообщение: минус админка",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    elif action.startswith("delete_"):
        promo_name = action.replace("delete_", "")
        if promo_name in promocodes:
            del promocodes[promo_name]
            save_promocodes()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ Промокод '{promo_name}' удален!",
                reply_markup=admin_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Админ {call.from_user.username} удалил промокод {promo_name}")
        else:
            bot.answer_callback_query(call.id, "❌ Промокод не найден!")
            
    elif action == "back":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="👑 <b>Админ панель Iris Bot</b>\n\nВыберите действие:",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data in ["admin_confirm_reset", "admin_cancel_reset"])
def callback_admin_reset(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Недостаточно прав!")
        return
        
    if call.data == "admin_confirm_reset":
        global casino_data
        casino_data = {}
        save_casino_data()
        
        text = "✅ База данных полностью сброшена!"
        logger.info(f"Админ {call.from_user.username} сбросил БД")
    else:
        text = "❌ Сброс базы данных отменен!"
        
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)

# ================== ОБРАБОТКА КОМАНД ИЗМЕНЕНИЯ МИН ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith('mines_'))
def callback_mines_settings(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Недостаточно прав!")
        return
        
    action = call.data
    
    if action == "mines_cells":
        config["mines_cells"] += 1
    elif action == "mines_cells_minus":
        if config["mines_cells"] > 5:
            config["mines_cells"] -= 1
    elif action == "mines_count":
        if config["mines_count"] < config["mines_cells"] - 1:
            config["mines_count"] += 1
    elif action == "mines_count_minus":
        if config["mines_count"] > 1:
            config["mines_count"] -= 1
    elif action == "mines_close":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "✅ Настройки закрыты")
        return
        
    save_config()
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Клетки", callback_data="mines_cells"),
        InlineKeyboardButton("➖ Клетки", callback_data="mines_cells_minus"),
        InlineKeyboardButton("➕ Мины", callback_data="mines_count"),
        InlineKeyboardButton("➖ Мины", callback_data="mines_count_minus"),
        InlineKeyboardButton("❌ Закрыть", callback_data="mines_close")
    )
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"⚙️ <b>Настройки игры Мины:</b>\n\nКоличество клеток: {config['mines_cells']}\nКоличество мин: {config['mines_count']}\n\nВыберите что изменить:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)

# ================== КОМАНДЫ ИЗМЕНЕНИЯ НАСТРОЕК ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить лимит доход"))
def change_income_limit(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        amount = int(message.text.split()[3])
        if amount < 0:
            bot.reply_to(message, "❌ Лимит не может быть отрицательным!")
            return
            
        config["max_daily_income"] = amount
        save_config()
        
        bot.reply_to(message, f"✅ Максимальный дневной доход изменен на {format_number(amount)}$")
        logger.info(f"Админ {message.from_user.username} изменил лимит дохода на {amount}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить лимит доход [сумма]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения лимита!")
        logger.error(f"Ошибка изменения лимита дохода: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить лимит баланс"))
def change_balance_limit(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        amount = int(message.text.split()[3])
        if amount < 0:
            bot.reply_to(message, "❌ Лимит не может быть отрицательным!")
            return
            
        config["max_balance"] = amount
        save_config()
        
        bot.reply_to(message, f"✅ Максимальный баланс изменен на {format_number(amount)}$")
        logger.info(f"Админ {message.from_user.username} изменил лимит баланса на {amount}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить лимит баланс [сумма]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения лимита!")
        logger.error(f"Ошибка изменения лимита баланса: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить лимит переводы"))
def change_transfer_limit(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        amount = int(message.text.split()[3])
        if amount < 0:
            bot.reply_to(message, "❌ Лимит не может быть отрицательным!")
            return
            
        config["transfer_daily_limit"] = amount
        save_config()
        
        bot.reply_to(message, f"✅ Лимит переводов изменен на {format_number(amount)}$ в день")
        logger.info(f"Админ {message.from_user.username} изменил лимит переводов на {amount}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить лимит переводы [сумма]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения лимита!")
        logger.error(f"Ошибка изменения лимита переводов: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить множитель блэкджек"))
def change_blackjack_multiplier(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        multiplier = float(message.text.split()[3])
        if multiplier <= 0:
            bot.reply_to(message, "❌ Множитель должен быть положительным!")
            return
            
        config["blackjack_win_multiplier"] = multiplier
        save_config()
        
        bot.reply_to(message, f"✅ Множитель блэкджека изменен на {multiplier}x")
        logger.info(f"Админ {message.from_user.username} изменил множитель блэкджека на {multiplier}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить множитель блэкджек [число]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения множителя!")
        logger.error(f"Ошибка изменения множителя блэкджека: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить множитель рулетка"))
def change_roulette_multiplier(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        multiplier = float(message.text.split()[3])
        if multiplier <= 0:
            bot.reply_to(message, "❌ Множитель должен быть положительным!")
            return
            
        config["roulette_win_multiplier"] = multiplier
        save_config()
        
        bot.reply_to(message, f"✅ Множитель рулетки изменен на {multiplier}x")
        logger.info(f"Админ {message.from_user.username} изменил множитель рулетки на {multiplier}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить множитель рулетка [число]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения множителя!")
        logger.error(f"Ошибка изменения множителя рулетки: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить множитель мины"))
def change_mines_multiplier(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        multiplier = float(message.text.split()[3])
        if multiplier <= 0:
            bot.reply_to(message, "❌ Множитель должен быть положительным!")
            return
            
        config["mines_multiplier_increment"] = multiplier
        save_config()
        
        bot.reply_to(message, f"✅ Прирост множителя мин изменен на {multiplier}x")
        logger.info(f"Админ {message.from_user.username} изменил множитель мин на {multiplier}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить множитель мины [число]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения множителя!")
        logger.error(f"Ошибка изменения множителя мин: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить множитель монета"))
def change_coin_multiplier(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        multiplier = float(message.text.split()[3])
        if multiplier <= 0:
            bot.reply_to(message, "❌ Множитель должен быть положительным!")
            return
            
        config["coin_flip_multiplier"] = multiplier
        save_config()
        
        bot.reply_to(message, f"✅ Множитель орла/решки изменен на {multiplier}x")
        logger.info(f"Админ {message.from_user.username} изменил множитель монеты на {multiplier}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить множитель монета [число]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения множителя!")
        logger.error(f"Ошибка изменения множителя монеты: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("изменить процент банка"))
def change_bank_interest(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        interest = float(message.text.split()[3])
        if interest < 0:
            bot.reply_to(message, "❌ Процент не может быть отрицательным!")
            return
            
        config["bank_interest_rate"] = interest
        save_config()
        
        bot.reply_to(message, f"✅ Процентная ставка банка изменена на {interest}% в день")
        logger.info(f"Админ {message.from_user.username} изменил процент банка на {interest}")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: изменить процент банка [число]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка изменения процента!")
        logger.error(f"Ошибка изменения процента банка: {e}")

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

# ================== ПОИСК ИГРОКА ==================
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("найти "))
def search_player(message):
    if not is_admin(message.from_user.id):
        return
        
    try:
        query = message.text.split(maxsplit=2)[2]
        
        # Поиск по ID
        if query.isdigit():
            user_id = int(query)
            if str(user_id) in casino_data:
                user_data = casino_data[str(user_id)]
                try:
                    user = bot.get_chat(user_id)
                    username = user.username if user.username else "Нет username"
                    name = user.first_name
                except:
                    username = "Неизвестно"
                    name = "Неизвестно"
                    
                response = (f"👤 <b>Найден игрок:</b>\n\n"
                           f"ID: {user_id}\n"
                           f"Имя: {name}\n"
                           f"Username: @{username}\n"
                           f"Баланс: {format_number(user_data['balance'])}$\n"
                           f"Банк: {format_number(user_data['bank_balance'])}$")
                
                if user_data.get("tyanka"):
                    response += f"\nТянка: {user_data['tyanka']['name']}"
                if user_data.get("business"):
                    response += f"\nБизнес: {user_data['business']['name']}"
                if user_data.get("house"):
                    response += f"\nДом: {user_data['house']['name']}"
                if user_data.get("car"):
                    response += f"\nМашина: {user_data['car']['name']}"
                    
                bot.reply_to(message, response, parse_mode="HTML")
                return
                
        # Поиск по username (без @)
        for user_id, user_data in casino_data.items():
            try:
                user = bot.get_chat(int(user_id))
                if user.username and user.username.lower() == query.lower():
                    response = (f"👤 <b>Найден игрок:</b>\n\n"
                               f"ID: {user_id}\n"
                               f"Имя: {user.first_name}\n"
                               f"Username: @{user.username}\n"
                               f"Баланс: {format_number(user_data['balance'])}$\n"
                               f"Банк: {format_number(user_data['bank_balance'])}$")
                    
                    if user_data.get("tyanka"):
                        response += f"\nТянка: {user_data['tyanka']['name']}"
                    if user_data.get("business"):
                        response += f"\nБизнес: {user_data['business']['name']}"
                    if user_data.get("house"):
                        response += f"\nДом: {user_data['house']['name']}"
                    if user_data.get("car"):
                        response += f"\nМашина: {user_data['car']['name']}"
                        
                    bot.reply_to(message, response, parse_mode="HTML")
                    return
                    
            except:
                continue
                
        # Поиск по имени
        for user_id, user_data in casino_data.items():
            try:
                user = bot.get_chat(int(user_id))
                if user.first_name and query.lower() in user.first_name.lower():
                    response = (f"👤 <b>Найден игрок:</b>\n\n"
                               f"ID: {user_id}\n"
                               f"Имя: {user.first_name}\n"
                               f"Username: @{user.username if user.username else 'Нет'}\n"
                               f"Баланс: {format_number(user_data['balance'])}$\n"
                               f"Банк: {format_number(user_data['bank_balance'])}$")
                    
                    if user_data.get("tyanka"):
                        response += f"\nТянка: {user_data['tyanka']['name']}"
                    if user_data.get("business"):
                        response += f"\nБизнес: {user_data['business']['name']}"
                    if user_data.get("house"):
                        response += f"\nДом: {user_data['house']['name']}"
                    if user_data.get("car"):
                        response += f"\nМашина: {user_data['car']['name']}"
                        
                    bot.reply_to(message, response, parse_mode="HTML")
                    return
                    
            except:
                continue
                
        bot.reply_to(message, "❌ Игрок не найден!")
        
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Используйте: найти игрок [ID/имя/username]")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка поиска!")
        logger.error(f"Ошибка поиска игрока: {e}")
        


# ================== КОМАНДА ЛОГОВ ==================
@bot.message_handler(commands=['log'])
def send_logs(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Недостаточно прав!")
        return
        
    try:
        with open("bot_logs.txt", "rb") as f:
            bot.send_document(message.chat.id, f, caption="📋 Логи бота")
        logger.info(f"Админ {message.from_user.username} запросил логи")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка отправки логов!")
        logger.error(f"Ошибка отправки логов: {e}")
        

# ================== ЗАПУСК БОТА ==================
if __name__ == "__main__":
    logger.info("Бот Iris запущен!")
    bot.infinity_polling()