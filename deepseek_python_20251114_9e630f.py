#!/usr/bin/env python3
"""
🤖 УМНЫЙ ТЕЛЕГРАМ БОТ ДЛЯ ПАРИКМАХЕРСКОЙ
Полная система автоматизации записи клиентов
"""

print("🔄 Загружаю систему салона красоты...")

import datetime
import asyncio
import json
import re
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler

try:
    import nest_asyncio
    nest_asyncio.apply()
    print("✅ Адаптер для Colab активирован")
except:
    print("⚠️  Режим Colab не активирован")

CONFIG = {
    "token": "8281147294:AAEzOek15AiCN0ayZ79KAJjHYlScO-u5NhU",
    "admin_id": 5892547881,
    "masters": {"Анна": 5892547881, "Мария": 5892547881, "Иван": 5892547881},
    "salon_info": {
        "phone": "+7 (999) 123-45-67",
        "address": "ул. Центральная, 123",
        "working_hours": {"start": "09:00", "end": "21:00", "lunch": "13:00-14:00"}
    },
    "services": {
        "стрижка": 1000, "бритье": 500, "окрашивание": 2000, 
        "укладка": 300, "стрижка+борода": 1200, "детская стрижка": 700
    }
}

bookings = {}
client_data = {}
user_sessions = {}
master_stats = {master: {"bookings": 0, "revenue": 0, "rating": 5.0} for master in CONFIG["masters"]}
master_schedules = {master: {"working_days": [0,1,2,3,4,5], "vacations": []} for master in CONFIG["masters"]}
analytics_data = {'service_popularity': Counter(), 'master_popularity': Counter(), 'time_preferences': Counter(), 'client_retention': {}}

service_patterns = {
    'стрижка': r'(стрижк|подстрич|пострич|волос)',
    'бритье': r'(брит|бород|ус)',
    'окрашивание': r'(окраш|цвет|краск)',
    'укладка': r'(укладк|улож)'
}

print("✅ Система инициализирована!")

class VisualCalendar:
    def create_visual_calendar(self, year=None, month=None):
        today = datetime.date.today()
        year = year or today.year
        month = month or today.month
        
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        keyboard = [[InlineKeyboardButton(f"📅 {month_names[month-1]} {year}", callback_data="header")]]
        keyboard.append([InlineKeyboardButton(day, callback_data="header") for day in ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]])
        
        first_day = datetime.date(year, month, 1)
        last_day = datetime.date(year, month+1, 1) - datetime.timedelta(days=1) if month < 12 else datetime.date(year+1, 1, 1) - datetime.timedelta(days=1)
        
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
            button = InlineKeyboardButton(f"{emoji}{current_date.day}", callback_data=f"date_{date_str}")
            current_row.append(button)
            current_date += datetime.timedelta(days=1)
        
        if current_row:
            while len(current_row) < 7:
                current_row.append(InlineKeyboardButton(" ", callback_data="empty"))
            keyboard.append(current_row)
        
        nav_row = []
        if month > 1 or year > today.year:
            prev_month = month-1 if month>1 else 12
            prev_year = year if month>1 else year-1
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f"nav_{prev_year}_{prev_month}"))
        
        nav_row.append(InlineKeyboardButton("🗓️ Сегодня", callback_data="nav_today"))
        
        if month < 12 or year < today.year+1:
            next_month = month+1 if month<12 else 1
            next_year = year if month<12 else year+1
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f"nav_{next_year}_{next_month}"))
        
        keyboard.append(nav_row)
        return InlineKeyboardMarkup(keyboard)
    
    def is_date_available(self, date_str):
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if date_obj.weekday() == 6: return False
        
        for master in CONFIG["masters"]:
            if any(vacation["start"] <= date_str <= vacation["end"] for vacation in master_schedules[master]["vacations"]):
                continue
            available_times = self.generate_available_times(date_str, master)
            if available_times: return True
        return False
    
    def generate_available_times(self, date_str, master):
        times = []
        start = datetime.datetime.strptime("09:00", "%H:%M")
        end = datetime.datetime.strptime("21:00", "%H:%M")
        lunch_start = datetime.datetime.strptime("13:00", "%H:%M")
        lunch_end = datetime.datetime.strptime("14:00", "%H:%M")
        
        current = start
        while current < end:
            if lunch_start <= current < lunch_end:
                current = lunch_end
                continue
            time_str = current.strftime("%H:%M")
            is_booked = any(b['date']==date_str and b['time']==time_str and b['master']==master and b['status']=='confirmed' for b in bookings.values())
            if not is_booked: times.append(time_str)
            current += datetime.timedelta(minutes=30)
        return times

calendar_system = VisualCalendar()

class SmartReminderSystem:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.setup_daily_tasks()
        print("✅ Система напоминаний активирована")
    
    def setup_daily_tasks(self):
        self.scheduler.add_job(self.schedule_daily_reminders, 'cron', hour=8, minute=0)
        self.scheduler.add_job(self.health_check, 'cron', hour='*', minute=0)
    
    def schedule_daily_reminders(self):
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_bookings = [b for b in bookings.values() if b["date"] == tomorrow and b["status"] == "confirmed"]
        
        print(f"🔔 Планирую {len(tomorrow_bookings)} напоминаний на завтра")
        
        for booking in tomorrow_bookings:
            reminder_time = self.calculate_reminder_time(booking["time"], hours_before=3)
            self.scheduler.add_job(
                self.send_reminder, 'date', run_date=reminder_time, 
                args=[booking['id'], '3_hours'], id=f"reminder_{booking['id']}_3h"
            )
    
    def calculate_reminder_time(self, booking_time, hours_before):
        booking_dt = datetime.datetime.strptime(booking_time, "%H:%M")
        reminder_dt = booking_dt - datetime.timedelta(hours=hours_before)
        return datetime.datetime.now().replace(hour=reminder_dt.hour, minute=reminder_dt.minute) + datetime.timedelta(days=1)
    
    async def send_reminder(self, booking_id, reminder_type):
        try:
            if booking_id not in bookings: return
            booking = bookings[booking_id]
            app = Application.builder().token(CONFIG["token"]).build()
            
            message = (f"🔔 НАПОМИНАНИЕ О ЗАПИСИ!\n\n⏰ {booking['time']} - {booking['service']}\n"
                      f"👨‍💼 {booking['master']}\n📍 {CONFIG['salon_info']['address']}\n📞 {CONFIG['salon_info']['phone']}")
            
            await app.bot.send_message(chat_id=booking['user_id'], text=message)
            print(f"✅ Напоминание отправлено {booking['user_name']}")
        except Exception as e:
            print(f"❌ Ошибка напоминания: {e}")
    
    def health_check(self):
        active_bookings = len([b for b in bookings.values() if b["status"] == "confirmed"])
        print(f"❤️ Проверка здоровья: {datetime.datetime.now().strftime('%H:%M:%S')}")
        print(f"📊 Активных записей: {active_bookings}")

async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"✂️ {service} - {price}₽", callback_data=f"service_{service}")] for service, price in CONFIG["services"].items()]
    await update.message.reply_text("✂️ ВЫБЕРИТЕ УСЛУГУ:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = query.data.replace("service_", "")
    user_id = query.from_user.id
    user_sessions[user_id] = {"service": service}
    
    keyboard = [[InlineKeyboardButton(f"👨‍💼 {master}", callback_data=f"master_{master}")] for master in CONFIG["masters"]]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_services")])
    await query.edit_message_text(f"✂️ УСЛУГА: {service}\n\nВЫБЕРИТЕ МАСТЕРА:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_master(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_services":
        await start_booking(update, context)
        return
    master = query.data.replace("master_", "")
    user_id = query.from_user.id
    user_sessions[user_id]["master"] = master
    await query.edit_message_text(f"✂️ {user_sessions[user_id]['service']}\n👨‍💼 МАСТЕР: {master}\n\nВЫБЕРИТЕ ДАТУ:", reply_markup=calendar_system.create_visual_calendar())

async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("nav_"):
        if query.data == "nav_today":
            new_calendar = calendar_system.create_visual_calendar()
        else:
            parts = query.data.replace("nav_", "").split("_")
            new_calendar = calendar_system.create_visual_calendar(int(parts[0]), int(parts[1]))
        await query.edit_message_reply_markup(reply_markup=new_calendar)
        return
    
    if not query.data.startswith("date_"): return
    date_str = query.data.replace("date_", "")
    user_id = query.from_user.id
    user_sessions[user_id]["date"] = date_str
    master = user_sessions[user_id]["master"]
    
    times = calendar_system.generate_available_times(date_str, master)
    keyboard = []
    row = []
    for i, time_str in enumerate(times):
        row.append(InlineKeyboardButton(f"🕒 {time_str}", callback_data=f"time_{time_str}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_calendar")])
    
    date_display = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    await query.edit_message_text(f"✂️ {user_sessions[user_id]['service']}\n👨‍💼 {master}\n📅 {date_display}\n\nВЫБЕРИТЕ ВРЕМЯ:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_calendar":
        user_id = query.from_user.id
        session = user_sessions.get(user_id, {})
        await query.edit_message_text(f"✂️ {session.get('service','')}\n👨‍💼 {session.get('master','')}\n\nВЫБЕРИТЕ ДАТУ:", reply_markup=calendar_system.create_visual_calendar())
        return
    
    time_str = query.data.replace("time_", "")
    user_id = query.from_user.id
    user_sessions[user_id]["time"] = time_str
    session = user_sessions[user_id]
    
    date_display = datetime.datetime.strptime(session["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
    price = CONFIG["services"][session["service"]]
    
    confirm_text = f"✅ ПОДТВЕРЖДЕНИЕ ЗАПИСИ:\n\n✂️ {session['service']}\n👨‍💼 {session['master']}\n📅 {date_display}\n⏰ {time_str}\n💰 {price}₽\n\nВСЁ ВЕРНО?"
    keyboard = [[InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"), InlineKeyboardButton("❌ Отменить", callback_data="confirm_no")]]
    await query.edit_message_text(confirm_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_yes":
        user_id = query.from_user.id
        session = user_sessions[user_id]
        booking_id = f"{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        price = CONFIG["services"][session["service"]]
        
        bookings[booking_id] = {
            "id": booking_id, "user_id": user_id, "user_name": query.from_user.first_name,
            "service": session["service"], "master": session["master"], "date": session["date"], 
            "time": session["time"], "price": price, "status": "confirmed",
            "created_at": datetime.datetime.now().isoformat()
        }
        
        master_stats[session["master"]]["bookings"] += 1
        master_stats[session["master"]]["revenue"] += price
        analytics_data['service_popularity'][session["service"]] += 1
        analytics_data['master_popularity'][session["master"]] += 1
        analytics_data['time_preferences'][session["time"]] += 1
        
        if user_id not in client_data:
            client_data[user_id] = {"name": query.from_user.first_name, "username": query.from_user.username, "bookings_count": 0}
        client_data[user_id]["bookings_count"] += 1
        
        client_hash = hash(user_id) % 1000000
        if client_hash not in analytics_data['client_retention']:
            analytics_data['client_retention'][client_hash] = 1
        else:
            analytics_data['client_retention'][client_hash] += 1
        
        date_display = datetime.datetime.strptime(session["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        await query.edit_message_text(f"🎉 ЗАПИСЬ ПОДТВЕРЖДЕНА!\n\n✅ {session['service']}\n👨‍💼 {session['master']}\n📅 {date_display}\n⏰ {session['time']}\n💰 {price}₽\n\n📞 {CONFIG['salon_info']['phone']}\n📍 {CONFIG['salon_info']['address']}")
        
        try:
            app = Application.builder().token(CONFIG["token"]).build()
            await app.bot.send_message(chat_id=CONFIG["admin_id"], text=f"🔔 НОВАЯ ЗАПИСЬ!\n{query.from_user.first_name}\n{session['service']}\n{session['master']}\n{date_display} {session['time']}")
        except: pass
        
    else:
        await query.edit_message_text("❌ ЗАПИСЬ ОТМЕНЕНА")
        if query.from_user.id in user_sessions:
            del user_sessions[query.from_user.id]

async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_bookings = [b for b in bookings.values() if b["user_id"] == user_id and b["status"] == "confirmed"]
    
    if not user_bookings:
        await update.message.reply_text("📭 У вас нет активных записей")
        return
    
    for booking in user_bookings:
        date_display = datetime.datetime.strptime(booking["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        text = f"✂️ {booking['service']}\n👨‍💼 {booking['master']}\n📅 {date_display}\n⏰ {booking['time']}\n💰 {booking['price']}₽"
        keyboard = [[InlineKeyboardButton("🔄 Перенести", callback_data=f"reschedule_{booking['id']}"), InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{booking['id']}")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_booking_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("cancel_"):
        booking_id = query.data.replace("cancel_", "")
        bookings[booking_id]["status"] = "cancelled"
        await query.edit_message_text("✅ ЗАПИСЬ ОТМЕНЕНА")
    elif query.data.startswith("reschedule_"):
        booking_id = query.data.replace("reschedule_", "")
        user_sessions[query.from_user.id] = {"reschedule_id": booking_id, **bookings[booking_id]}
        await query.edit_message_text("🔄 ВЫБЕРИТЕ НОВУЮ ДАТУ:", reply_markup=calendar_system.create_visual_calendar())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CONFIG["admin_id"]:
        await update.message.reply_text("⛔ ДОСТУП ЗАПРЕЩЕН")
        return
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    today_bookings = [b for b in bookings.values() if b["date"] == today and b["status"] == "confirmed"]
    week_bookings = [b for b in bookings.values() if b["status"] == "confirmed"]
    
    daily_revenue = sum(b["price"] for b in today_bookings)
    weekly_revenue = sum(b["price"] for b in week_bookings)
    total_clients = len(client_data)
    popular_service = analytics_data['service_popularity'].most_common(1)
    popular_service_text = f"{popular_service[0][0]} ({popular_service[0][1]} раз)" if popular_service else "нет данных"
    
    text = f"👑 ПАНЕЛЬ АДМИНИСТРАТОРА\n\n📊 СЕГОДНЯ ({datetime.date.today().strftime('%d.%m.%Y')}):\n• Записей: {len(today_bookings)}\n• Выручка: {daily_revenue}₽\n• Свободных окон: {18 - len(today_bookings)}\n\n📈 НЕДЕЛЯ:\n• Выручка: {weekly_revenue}₽\n• Уникальных клиентов: {total_clients}\n• Популярная услуга: {popular_service_text}\n\n👨‍💼 МАСТЕРА:\n"
    
    for master, stats in master_stats.items():
        text += f"• {master}: {stats['bookings']} зап., {stats['revenue']}₽, ★{stats['rating']}\n"
    
    returning_clients = sum(1 for count in analytics_data['client_retention'].values() if count > 1)
    if returning_clients > 0:
        retention_rate = (returning_clients / len(analytics_data['client_retention'])) * 100
        text += f"\n📈 Лояльность клиентов: {retention_rate:.1f}%"
    
    await update.message.reply_text(text)

async def master_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    master_name = next((name for name, mid in CONFIG["masters"].items() if mid == user_id), None)
    if not master_name: return
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    my_bookings = [b for b in bookings.values() if b["master"] == master_name and b["date"] == today and b["status"] == "confirmed"]
    
    text = f"👨‍💼 ПАНЕЛЬ МАСТЕРА {master_name}\n\n📅 СЕГОДНЯ:\n"
    for booking in sorted(my_bookings, key=lambda x: x["time"]):
        text += f"⏰ {booking['time']} - {booking['service']} ({booking['user_name']})\n"
    
    text += f"\n💰 ВЫРУЧКА: {master_stats[master_name]['revenue']}₽"
    await update.message.reply_text(text)

class SalonBotSystem:
    def __init__(self):
        self.app = None
        self.restart_count = 0
        self.max_restarts = 50
    
    async def setup_handlers(self):
        self.app = Application.builder().token(CONFIG["token"]).build()
        self.app.add_handler(CommandHandler("start", start_booking))
        self.app.add_handler(CommandHandler("mybookings", my_bookings))
        self.app.add_handler(CommandHandler("admin", admin_panel))
        self.app.add_handler(CommandHandler("master", master_panel))
        self.app.add_handler(CallbackQueryHandler(handle_service, pattern="^service_"))
        self.app.add_handler(CallbackQueryHandler(handle_master, pattern="^(master_|back_services)"))
        self.app.add_handler(CallbackQueryHandler(handle_calendar, pattern="^(date_|nav_|back_calendar)"))
        self.app.add_handler(CallbackQueryHandler(handle_time, pattern="^time_"))
        self.app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm_"))
        self.app.add_handler(CallbackQueryHandler(handle_booking_management, pattern="^(cancel_|reschedule_)"))
        print("✅ Все обработчики настроены!")
    
    async def run_bot(self):
        try:
            await self.setup_handlers()
            reminder_system = SmartReminderSystem()
            print("🎉 БОТ УСПЕШНО ЗАПУЩЕН!")
            print("📱 КОМАНДЫ: /start, /mybookings, /admin, /master")
            print("⏹️  Для остановки нажмите Ctrl+C")
            await self.app.run_polling()
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            return False
    
    async def run_with_restart(self):
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

async def main():
    system = SalonBotSystem()
    await system.run_with_restart()

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК СИСТЕМЫ УПРАВЛЕНИЯ САЛОНОМ КРАСОТЫ")
    print("=" * 60)
    try:
        asyncio.run(main())
    except RuntimeError:
        print("🔧 Адаптивный запуск для Google Colab...")
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        print("✅ Система запущена в фоновом режиме!")