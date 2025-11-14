#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 УМНЫЙ ТЕЛЕГРАМ БОТ ДЛЯ ПАРИКМАХЕРСКОЙ "ЧАРОДЕЙКА"
Полная оптимизированная система автоматизации записи клиентов
Мужской зал - профессиональные барберы
"""

# БЛОК 1 - ЯДРО СИСТЕМЫ БЕЗ ТОРМОЗОВ
print("🔄 Загружаю систему салона красоты ЧАРОДЕЙКА...")

import datetime
import asyncio
import json
import pytz
import re
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    import nest_asyncio
    nest_asyncio.apply()
    print("✅ Адаптер для Colab активирован")
except ImportError:
    print("⚠️  Режим Colab не активирован")

# ОПТИМИЗИРОВАННАЯ КОНФИГУРАЦИЯ - САЛОН "ЧАРОДЕЙКА"
CONFIG = {
    "token": "8281147294:AAEzOek15AiCN0ayZ79KAJjHYlScO-u5NhU",
    "admin_id": 5892547881,
    "salon_name": "Чародейка",
    "salon_type": "Салон-парикмахерская",
    "masters": {
        "Дмитрий": 5892547881,
        "Александр": 5892547881,
        "Игорь": 5892547881
    },
    "salon_info": {
        # Обновлённые данные (из присланного текста/фото)
        "phone": "",
        "address": "Азовская улица, 4, 1 этаж, Черёмушки м-н, Армавир, Краснодарский край, 352930",
        "city": "Армавир, Краснодарский край",
        "coordinates": {},
        "working_hours": {
            "start": "08:00",
            "end": "18:00",
            "lunch": ["12:00", "13:00"],
            "closed_days": []  # Ежедневно: Пн-Вс 08:00-18:00
        },
        "website": "https://yandex.ru/maps/org/charodeyka/1049163937/",
        "description": "Салон-парикмахерская. Работает ежедневно с 08:00 до 18:00."
    },
    "services": {
        "Женская стрижка": 0,
        "Мужская стрижка": 0,
        "Детская стрижка": 0,
        "Стрижка бороды": 0,
        "Сложное окрашивание": 0,
        "Свадебные и вечерние причёски": 0
    },
    "payments": ["Наличные", "Перевод с карты"]
}

# ОПТИМИЗИРОВАННЫЕ ХРАНИЛИЩА
bookings = {}
client_data = {}
user_sessions = {}
master_stats = {master: {"bookings": 0, "revenue": 0, "rating": 5.0} for master in CONFIG["masters"]}
master_schedules = {master: {"working_days": [0,1,2,3,4,5], "vacations": []} for master in CONFIG["masters"]}
analytics_data = {'service_popularity': Counter(), 'master_popularity': Counter(), 'time_preferences': Counter()}

# БЫСТРЫЕ ПАТТЕРНЫ ВМЕСТО AI
service_patterns = {
    'стрижка': r'(стрижк|подстрич|волос)',
    'бритьё': r'(брит|бород|ус)',
    'оформление': r'(оформ|борода)',
    'окраска': r'(окраш|цвет|краск)',
    'vip': r'(vip|люкс|премиум)'
}
master_patterns = {
    'Дмитрий': r'(дмитри|дима|дима)',
    'Александр': r'(алекс|саша|сашка)',
    'Игорь': r'(игор|го)'
}

print("✅ ЯДРО СИСТЕМЫ ЧАРОДЕЙКА ЗАГРУЖЕНО БЕЗ ТОРМОЗОВ!")

# БЛОК 2 - ВИЗУАЛЬНЫЙ КАЛЕНДАРЬ И УМНОЕ РАСПИСАНИЕ
class UltraCalendar:
    """Визуальный календарь с emoji-индикаторами и навигацией"""
    
    def create_visual_calendar(self, year=None, month=None):
        today = datetime.date.today()
        year = year or today.year
        month = month or today.month

        # ЗАГОЛОВОК
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        keyboard = [[InlineKeyboardButton(f"📅 {month_names[month-1]} {year}", callback_data="header")]]

        # ДНИ НЕДЕЛИ
        keyboard.append([InlineKeyboardButton(day, callback_data="header")
                        for day in ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]])

        # ДАТЫ
        first_day = datetime.date(year, month, 1)
        last_day = datetime.date(year, month+1, 1) - datetime.timedelta(days=1) if month < 12 \
                   else datetime.date(year+1, 1, 1) - datetime.timedelta(days=1)

        current_row = []
        for _ in range(first_day.weekday()):
            current_row.append(InlineKeyboardButton(" ", callback_data="empty"))

        current_date = first_day
        while current_date <= last_day:
            if len(current_row) == 7:
                keyboard.append(current_row)
                current_row = []

            date_str = current_date.strftime("%Y-%m-%d")
            is_available = self.is_date_available(date_str)
            is_today = current_date == today

            emoji = "🔴" if not is_available else "🟢" if is_today else "⚪"
            btn = InlineKeyboardButton(f"{emoji}{current_date.day}", callback_data=f"date_{date_str}")
            current_row.append(btn)
            current_date += datetime.timedelta(days=1)

        if current_row:
            while len(current_row) < 7:
                current_row.append(InlineKeyboardButton(" ", callback_data="empty"))
            keyboard.append(current_row)

        # НАВИГАЦИЯ
        nav_row = []
        if month > 1 or year > today.year:
            prev_month = month-1 if month > 1 else 12
            prev_year = year if month > 1 else year-1
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f"nav_{prev_year}_{prev_month}"))

        nav_row.append(InlineKeyboardButton("🗓️ Сегодня", callback_data="nav_today"))

        if month < 12 or year < today.year+1:
            next_month = month+1 if month < 12 else 1
            next_year = year if month < 12 else year+1
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f"nav_{next_year}_{next_month}"))

        keyboard.append(nav_row)
        return InlineKeyboardMarkup(keyboard)

    def is_date_available(self, date_str):
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if date_obj.weekday() in CONFIG["salon_info"]["working_hours"].get("closed_days", []):
            return False

        for master in CONFIG["masters"]:
            # ПРОВЕРКА ОТПУСКА
            if any(v["start"] <= date_str <= v["end"] for v in master_schedules[master]["vacations"]):
                continue

            # ПРОВЕРКА СВОБОДНЫХ СЛОТОВ
            available_times = self.generate_available_times(date_str, master)
            if available_times:
                return True
        return False

    def generate_available_times(self, date_str, master):
        times = []
        start = datetime.datetime.strptime(CONFIG["salon_info"]["working_hours"]["start"], "%H:%M")
        end = datetime.datetime.strptime(CONFIG["salon_info"]["working_hours"]["end"], "%H:%M")
        
        lunch_config = CONFIG["salon_info"]["working_hours"]["lunch"]
        if isinstance(lunch_config, str):
            lunch = lunch_config.split("-")
        else:
            lunch = lunch_config
        
        lunch_start = datetime.datetime.strptime(lunch[0], "%H:%M")
        lunch_end = datetime.datetime.strptime(lunch[1], "%H:%M")

        current = start
        while current < end:
            if lunch_start <= current < lunch_end:
                current = lunch_end
                continue

            time_str = current.strftime("%H:%M")
            is_booked = any(b['date'] == date_str and b['time'] == time_str and
                           b['master'] == master and b['status'] == 'confirmed'
                           for b in bookings.values())
            if not is_booked:
                times.append(time_str)
            current += datetime.timedelta(minutes=30)
        return times


class SmartScheduler:
    """Умное управление расписанием и отпусками"""
    
    def set_master_vacation(self, master, start_date, end_date):
        master_schedules[master]["vacations"].append({"start": start_date, "end": end_date})
        self.cancel_vacation_bookings(master, start_date, end_date)

    def cancel_vacation_bookings(self, master, start_date, end_date):
        cancelled = []
        for bid, booking in bookings.items():
            if (booking["master"] == master and booking["status"] == "confirmed" and
                start_date <= booking["date"] <= end_date):
                bookings[bid]["status"] = "cancelled"
                cancelled.append(bid)
        return cancelled


ultra_calendar = UltraCalendar()
smart_scheduler = SmartScheduler()
print("✅ ВИЗУАЛЬНЫЙ КАЛЕНДАРЬ И РАСПИСАНИЕ ГОТОВЫ!")

# БЛОК 3 - ПОЛНЫЙ ФУНКЦИОНАЛ БОТ-А
async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор услуги - с Web App"""
    from telegram import WebAppInfo
    
    text = f"💈 {CONFIG['salon_name']} - {CONFIG['salon_type']}\n\n✂️ ВЫБЕРИТЕ УСЛУГУ:"
    keyboard = [[InlineKeyboardButton(f"✂️ {service} - {price}₽", callback_data=f"service_{service}")]
                for service, price in CONFIG["services"].items()]
    
    # 🎨 НОВОЕ: Web App кнопка для красивого интерфейса
    keyboard.append([InlineKeyboardButton(
        "🎨 Забронировать (новый интерфейс)",
        web_app=WebAppInfo(url="https://charodeyka-booking.netlify.app")
    )])
    
    keyboard.append([InlineKeyboardButton("ℹ️ О САЛОНЕ", callback_data="about")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о салоне"""
    query = update.callback_query
    await query.answer()
    
    info_text = (f"💈 {CONFIG['salon_name']}\n"
                f"🏷️ {CONFIG['salon_type']}\n\n"
                f"📍 Адрес: {CONFIG['salon_info']['address']}\n"
                f"📱 Телефон: {CONFIG['salon_info']['phone']}\n"
                f"⏰ Режим: {CONFIG['salon_info']['working_hours']['start']}-{CONFIG['salon_info']['working_hours']['end']}\n"
                f"🍽️ Обед: {'-'.join(CONFIG['salon_info']['working_hours']['lunch']) if isinstance(CONFIG['salon_info']['working_hours']['lunch'], list) else CONFIG['salon_info']['working_hours']['lunch']}\n\n"
                f"👨‍💼 МАСТЕРА:\n")
    
    for master in CONFIG["masters"].keys():
        info_text += f"  • {master}\n"
    
    info_text += f"\n📍 Яндекс Карты: https://yandex.ru/maps/org/charodeyka/1049163937/"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_services")]]
    await query.edit_message_text(info_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора услуги"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_services":
        await start_booking(update, context)
        return
    
    service = query.data.replace("service_", "")
    user_sessions[query.from_user.id] = {"service": service}

    keyboard = [[InlineKeyboardButton(f"👨‍💼 {master}", callback_data=f"master_{master}")]
                for master in CONFIG["masters"]]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_services")])

    await query.edit_message_text(f"✂️ УСЛУГА: {service}\n\n👨‍💼 ВЫБЕРИТЕ МАСТЕРА:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_master(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора мастера"""
    query = update.callback_query
    await query.answer()

    if query.data == "back_services":
        await start_booking(update, context)
        return

    master = query.data.replace("master_", "")
    user_id = query.from_user.id
    user_sessions[user_id]["master"] = master

    await query.edit_message_text(
        f"✂️ {user_sessions[user_id]['service']}\n👨‍💼 МАСТЕР: {master}\n\n📅 ВЫБЕРИТЕ ДАТУ:",
        reply_markup=ultra_calendar.create_visual_calendar()
    )


async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка календаря и навигации"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("nav_"):
        if query.data == "nav_today":
            new_calendar = ultra_calendar.create_visual_calendar()
        else:
            parts = query.data.replace("nav_", "").split("_")
            new_calendar = ultra_calendar.create_visual_calendar(int(parts[0]), int(parts[1]))
        await query.edit_message_reply_markup(reply_markup=new_calendar)
        return

    if not query.data.startswith("date_"):
        return

    date_str = query.data.replace("date_", "")
    user_id = query.from_user.id
    user_sessions[user_id]["date"] = date_str
    master = user_sessions[user_id]["master"]

    times = ultra_calendar.generate_available_times(date_str, master)
    keyboard = []
    row = []
    for time_str in times:
        row.append(InlineKeyboardButton(f"🕒 {time_str}", callback_data=f"time_{time_str}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_calendar")])

    date_display = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    await query.edit_message_text(
        f"✂️ {user_sessions[user_id]['service']}\n👨‍💼 {master}\n📅 {date_display}\n\n⏰ ВЫБЕРИТЕ ВРЕМЯ:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора времени"""
    query = update.callback_query
    await query.answer()

    if query.data == "back_calendar":
        user_id = query.from_user.id
        session = user_sessions.get(user_id, {})
        await query.edit_message_text(
            f"✂️ {session.get('service','')}\n👨‍💼 {session.get('master','')}\n\n📅 ВЫБЕРИТЕ ДАТУ:",
            reply_markup=ultra_calendar.create_visual_calendar()
        )
        return

    time_str = query.data.replace("time_", "")
    user_id = query.from_user.id
    user_sessions[user_id]["time"] = time_str
    session = user_sessions[user_id]

    date_display = datetime.datetime.strptime(session["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
    price = CONFIG["services"].get(session["service"], 0) or 0
    price_display = f"{price}₽" if price > 0 else "по запросу"

    confirm_text = (f"✅ ПОДТВЕРЖДЕНИЕ ЗАПИСИ:\n\n"
                   f"💈 {CONFIG['salon_name']}\n"
                   f"✂️ {session['service']}\n"
                   f"👨‍💼 {session['master']}\n"
                   f"📅 {date_display}\n"
                   f"⏰ {time_str}\n"
                   f"💰 {price_display}\n\n"
                   f"ВСЁ ВЕРНО?")

    keyboard = [[
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Отменить", callback_data="confirm_no")
    ]]
    await query.edit_message_text(confirm_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальное подтверждение записи"""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_yes":
        user_id = query.from_user.id
        session = user_sessions[user_id]

        # СОЗДАЁМ ЗАПИСЬ
        booking_id = f"{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        price = CONFIG["services"].get(session["service"], 0) or 0

        bookings[booking_id] = {
            "id": booking_id, "user_id": user_id, "user_name": query.from_user.first_name,
            "service": session["service"], "master": session["master"], "date": session["date"],
            "time": session["time"], "price": price, "status": "confirmed",
            "created_at": datetime.datetime.now().isoformat()
        }

        # ОБНОВЛЯЕМ СТАТИСТИКУ
        master_stats[session["master"]]["bookings"] += 1
        master_stats[session["master"]]["revenue"] += price
        analytics_data['service_popularity'][session["service"]] += 1
        analytics_data['master_popularity'][session["master"]] += 1
        analytics_data['time_preferences'][session["time"]] += 1

        # СОБИРАЕМ ДАННЫЕ КЛИЕНТА
        if user_id not in client_data:
            client_data[user_id] = {"name": query.from_user.first_name,
                                   "username": query.from_user.username, "bookings_count": 0}
        client_data[user_id]["bookings_count"] += 1

        date_display = datetime.datetime.strptime(session["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        await query.edit_message_text(
            f"🎉 ЗАПИСЬ ПОДТВЕРЖДЕНА!\n\n"
            f"💈 {CONFIG['salon_name']}\n"
            f"✂️ {session['service']}\n"
            f"👨‍💼 {session['master']}\n"
            f"📅 {date_display}\n"
            f"⏰ {session['time']}\n"
            f"💰 {price}₽\n\n"
            f"📍 {CONFIG['salon_info']['address']}\n"
            f"📞 {CONFIG['salon_info']['phone']}"
        )

    else:
        await query.edit_message_text("❌ ЗАПИСЬ ОТМЕНЕНА")
        if query.from_user.id in user_sessions:
            del user_sessions[query.from_user.id]


async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мои записи"""
    user_id = update.effective_user.id
    user_bookings = [b for b in bookings.values() if b["user_id"] == user_id and b["status"] == "confirmed"]

    if not user_bookings:
        await update.message.reply_text("📭 НЕТ АКТИВНЫХ ЗАПИСЕЙ")
        return

    for booking in user_bookings:
        date_display = datetime.datetime.strptime(booking["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        text = (f"💈 {CONFIG['salon_name']}\n"
               f"✂️ {booking['service']}\n"
               f"👨‍💼 {booking['master']}\n"
               f"📅 {date_display}\n"
               f"⏰ {booking['time']}\n"
               f"💰 {booking['price']}₽")

        keyboard = [[
            InlineKeyboardButton("🔄 Перенести", callback_data=f"reschedule_{booking['id']}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{booking['id']}")
        ]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление записями (отмена, перенос)"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("cancel_"):
        booking_id = query.data.replace("cancel_", "")
        bookings[booking_id]["status"] = "cancelled"
        await query.edit_message_text("✅ ЗАПИСЬ ОТМЕНЕНА")

    elif query.data.startswith("reschedule_"):
        booking_id = query.data.replace("reschedule_", "")
        user_sessions[query.from_user.id] = {"reschedule_id": booking_id, **bookings[booking_id]}
        await query.edit_message_text("🔄 ВЫБЕРИТЕ НОВУЮ ДАТУ:",
                                     reply_markup=ultra_calendar.create_visual_calendar())


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-панель со статистикой"""
    if update.effective_user.id != CONFIG["admin_id"]:
        await update.message.reply_text("⛔ ДОСТУП ЗАПРЕЩЕН")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")
    today_bookings = [b for b in bookings.values() if b["date"] == today and b["status"] == "confirmed"]
    week_revenue = sum(b["price"] for b in bookings.values() if b["status"] == "confirmed")

    text = (f"👑 АДМИН ПАНЕЛЬ - {CONFIG['salon_name']}\n\n"
           f"📊 СЕГОДНЯ: {len(today_bookings)} записей\n"
           f"💰 ОБЩАЯ ВЫРУЧКА: {week_revenue}₽\n"
           f"👥 КЛИЕНТОВ: {len(client_data)}\n\n"
           f"👨‍💼 СТАТИСТИКА МАСТЕРОВ:\n")

    for master, stats in master_stats.items():
        text += f"  {master}: {stats['bookings']} записей, {stats['revenue']}₽, ★{stats['rating']}\n"

    # АНАЛИТИКА УСЛУГ
    popular_service = analytics_data['service_popularity'].most_common(1)
    if popular_service:
        text += f"\n🔥 ПОПУЛЯРНАЯ УСЛУГА: {popular_service[0][0]} ({popular_service[0][1]} раз)"

    await update.message.reply_text(text)


async def master_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Панель мастера"""
    user_id = update.effective_user.id
    master_name = next((name for name, mid in CONFIG["masters"].items() if mid == user_id), None)
    if not master_name:
        await update.message.reply_text("⛔ ВЫ НЕ МАСТЕР")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")
    my_bookings = [b for b in bookings.values() if b["master"] == master_name and
                   b["date"] == today and b["status"] == "confirmed"]

    text = f"👨‍💼 ПАНЕЛЬ {master_name}\n💈 {CONFIG['salon_name']}\n\n📅 СЕГОДНЯ:\n"
    
    if not my_bookings:
        text += "Записей нет 😴"
    else:
        for booking in sorted(my_bookings, key=lambda x: x["time"]):
            text += f"⏰ {booking['time']} - {booking['service']} ({booking['user_name']})\n"

        text += f"\n💰 ВЫРУЧКА СЕГОДНЯ: {sum(b['price'] for b in my_bookings)}₽"

    text += f"\n📊 ОБЩАЯ ВЫРУЧКА: {master_stats[master_name]['revenue']}₽"
    await update.message.reply_text(text)


print("✅ ВЕСЬ ФУНКЦИОНАЛ РЕАЛИЗОВАН!")

# БЛОК 4 - ИСПРАВЛЕННЫЙ ЗАПУСК ДЛЯ COLAB
class RealReminderSystem:
    """Система умных напоминаний с health-check"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.setup_daily_tasks()

    def setup_daily_tasks(self):
        # ЕЖЕДНЕВНЫЕ НАПОМИНАНИЯ В 8 УТРА
        self.scheduler.add_job(self.schedule_reminders, 'cron', hour=8, minute=0)
        # ПРОВЕРКА ЗДОРОВЬЯ КАЖДЫЙ ЧАС
        self.scheduler.add_job(self.health_check, 'cron', hour='*', minute=0)

    def schedule_reminders(self):
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_bookings = [b for b in bookings.values() if b["date"] == tomorrow and b["status"] == "confirmed"]

        for booking in tomorrow_bookings:
            reminder_time = self.calculate_reminder_time(booking["time"], hours_before=3)
            try:
                self.scheduler.add_job(
                    self.send_reminder, 'date', run_date=reminder_time,
                    args=[booking['id'], '3_hours'], id=f"reminder_{booking['id']}_3h"
                )
            except:
                pass

    def calculate_reminder_time(self, booking_time, hours_before):
        booking_dt = datetime.datetime.strptime(booking_time, "%H:%M")
        reminder_dt = booking_dt - datetime.timedelta(hours=hours_before)
        return datetime.datetime.now().replace(hour=reminder_dt.hour, minute=reminder_dt.minute) + datetime.timedelta(days=1)

    async def send_reminder(self, booking_id, reminder_type):
        try:
            if booking_id not in bookings:
                return
            booking = bookings[booking_id]
            app = Application.builder().token(CONFIG["token"]).build()

            message = (f"🔔 НАПОМИНАНИЕ О ЗАПИСИ!\n\n"
                      f"💈 {CONFIG['salon_name']}\n"
                      f"✂️ {booking['service']}\n"
                      f"👨‍💼 {booking['master']}\n"
                      f"⏰ {booking['time']}\n"
                      f"📍 {CONFIG['salon_info']['address']}\n"
                      f"📞 {CONFIG['salon_info']['phone']}")

            await app.bot.send_message(chat_id=booking['user_id'], text=message)
            print(f"✅ Напоминание отправлено {booking['user_name']}")
        except Exception as e:
            print(f"❌ Ошибка напоминания: {e}")

    def health_check(self):
        print(f"❤️ Проверка здоровья ЧАРОДЕЙКА: {datetime.datetime.now()}")
        active = len([b for b in bookings.values() if b["status"] == "confirmed"])
        print(f"📊 Активных записей: {active}")


class AutoRestartBot:
    """Автоматизированный запуск и перезапуск бота с exponential backoff"""
    
    def __init__(self):
        self.restart_count = 0
        self.max_restarts = 50

    async def setup_handlers(self, app):
        app.add_handler(CommandHandler("start", start_booking))
        app.add_handler(CommandHandler("mybookings", my_bookings))
        app.add_handler(CommandHandler("admin", admin_panel))
        app.add_handler(CommandHandler("master", master_panel))

        app.add_handler(CallbackQueryHandler(handle_about, pattern="^about$"))
        app.add_handler(CallbackQueryHandler(handle_service, pattern="^(service_|back_to_services|back_services)"))
        app.add_handler(CallbackQueryHandler(handle_master, pattern="^(master_|back_services)"))
        app.add_handler(CallbackQueryHandler(handle_calendar, pattern="^(date_|nav_|back_calendar)"))
        app.add_handler(CallbackQueryHandler(handle_time, pattern="^time_"))
        app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm_"))
        app.add_handler(CallbackQueryHandler(handle_management, pattern="^(cancel_|reschedule_)"))

    async def run_bot(self):
        """Запуск бота"""
        try:
            print("🔄 Создаю приложение бота...")
            app = Application.builder().token(CONFIG["token"]).build()
            await self.setup_handlers(app)

            # ЗАПУСКАЕМ НАПОМИНАНИЯ
            reminder_system = RealReminderSystem()

            print("🎉 БОТ ЗАПУЩЕН!")
            print(f"💈 САЛОН: {CONFIG['salon_name']} ({CONFIG['salon_type']})")
            print(f"📞 ТЕЛЕФОН: {CONFIG['salon_info']['phone']}")
            print(f"📍 АДРЕС: {CONFIG['salon_info']['address']}")
            print("\n📱 КОМАНДЫ: /start - запись, /mybookings - управление, /admin - админка, /master - мастер")
            print("⏹️  Для остановки нажмите Ctrl+C")

            # ЗАПУСКАЕМ ПОЛЛИНГ
            await app.run_polling()

        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return False
        return True

    async def run_forever(self):
        """Бесконечный перезапуск с exponential backoff"""
        while self.restart_count < self.max_restarts:
            success = await self.run_bot()

            if not success:
                self.restart_count += 1
                if self.restart_count < self.max_restarts:
                    wait_time = min(2 ** self.restart_count, 300)
                    print(f"⏳ Перезапуск через {wait_time} сек... (попытка {self.restart_count + 1}/{self.max_restarts})")
                    await asyncio.sleep(wait_time)
                else:
                    print("🚨 Достигнут лимит перезапусков")
                    break
            else:
                break


# ФИНАЛЬНЫЙ ЗАПУСК
async def main():
    bot = AutoRestartBot()
    await bot.run_forever()


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК СИСТЕМЫ УПРАВЛЕНИЯ САЛОНОМ ЧАРОДЕЙКА")
    print("=" * 60)
    try:
        asyncio.run(main())
    except RuntimeError:
        print("🔧 Адаптивный запуск для Google Colab...")
        try:
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        except Exception as e:
            print(f"❌ Ошибка: {e}")

import json
from datetime import datetime

DATA_FILE = "charodeyka_data.json"

def load_data():
    """Загрузить данные из файла"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "bookings": {},
            "master_schedules": {},
            "analytics": {}
        }

def save_data(data):
    """Сохранить данные в файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# API ЭНДПОИНТЫ
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/bookings', methods=['POST', 'GET'])
def handle_bookings():
    if request.method == 'POST':
        # СОЗДАНИЕ НОВОЙ ЗАПИСИ
        data = request.json
        booking_id = f"{data['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        bookings[booking_id] = {**data, "id": booking_id, "status": "confirmed"}
        return jsonify(bookings[booking_id]), 201

    elif request.method == 'GET':
        # ПОЛУЧЕНИЕ СПИСКА ЗАПИСЕЙ
        user_id = request.args.get('user_id')
        user_bookings = [b for b in bookings.values() if b["user_id"] == user_id]
        return jsonify(user_bookings), 200

@app.route('/admin/stats', methods=['GET'])
def get_admin_stats():
    if request.args.get('admin_id') != str(CONFIG["admin_id"]):
        return jsonify({"error": "Доступ запрещён"}), 403

    return jsonify({
        "total_bookings": len(bookings),
        "total_revenue": sum(b["price"] for b in bookings.values()),
        "master_stats": master_stats
    }), 200

@app.route('/master/stats', methods=['GET'])
def get_master_stats():
    user_id = request.args.get('user_id')
    master_name = next((name for name, mid in CONFIG["masters"].items() if mid == int(user_id)), None)
    if not master_name:
        return jsonify({"error": "Доступ запрещён"}), 403

    today = datetime.date.today().strftime("%Y-%m-%d")
    my_bookings = [b for b in bookings.values() if b["master"] == master_name and
                   b["date"] == today and b["status"] == "confirmed"]

    return jsonify({
        "today_bookings": len(my_bookings),
        "today_revenue": sum(b["price"] for b in my_bookings),
        "total_revenue": master_stats[master_name]["revenue"]
    }), 200

# ВЕБ АПП
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/style.css')
def style():
    return app.send_static_file('style.css')

@app.route('/app.js')
def script():
    return app.send_static_file('app.js')


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
