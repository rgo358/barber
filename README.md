# 🛎️ Barber — Telegram Bot for Salon Booking

Автоматизированная система записи клиентов в парикмахерскую через Telegram.

## 🎯 Возможности

- 📱 **Запись через Telegram** — простой и удобный интерфейс
- 👨‍💼 **Управление мастерами** — расписание, статистика, заработки
- 📅 **Визуальный календарь** — выбор даты с иконками доступности
- 💰 **Аналитика** — популярность услуг, мастеров, время пик
- ⏰ **Умные напоминания** — уведомления за 24 часа до записи
- 🔧 **Полная кастомизация** — услуги, цены, рабочее время в `CONFIG`

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- Telegram bot token (получить от [@BotFather](https://t.me/botfather))

### Установка

```bash
pip install python-telegram-bot apscheduler pytz
```

### Запуск

```bash
python salon_bot.py
```

Бот начнёт работать и выведет:
```
✅ БОТ УСПЕШНО ЗАПУЩЕН!
📱 КОМАНДЫ: /start, /mybookings, /admin, /master
```

## ⚙️ Конфигурация

Отредактируйте `CONFIG` в начале `salon_bot.py`:

```python
CONFIG = {
    "token": "YOUR_TELEGRAM_TOKEN",     # Токен бота от BotFather
    "admin_id": 123456789,               # Ваш Telegram ID (админ)
    "masters": {                         # Мастера (имя → Telegram ID)
        "Анна": 111111111,
        "Мария": 222222222,
    },
    "salon_info": {
        "phone": "+7 (999) 123-45-67",
        "address": "ул. Центральная, 123",
        "working_hours": {
            "start": "09:00",
            "end": "21:00",
            "lunch": "13:00-14:00"
        }
    },
    "services": {                        # Услуги (имя → цена)
        "стрижка": 1000,
        "бритье": 500,
        "окрашивание": 2000,
    }
}
```

## 👥 Команды для пользователей

| Команда | Описание |
|---------|----------|
| `/start` | Начать запись на услугу |
| `/mybookings` | Мои записи (отмена, перенос) |
| `/admin` | Статистика салона (только админ) |
| `/master` | Расписание на сегодня (только мастер) |

## 🔍 Архитектура

```
salon_bot.py
├── CONFIG                    # Конфигурация (единый источник истины)
├── VisualCalendar           # Визуальный календарь с emoji
├── SmartReminderSystem       # Напоминания (APScheduler)
├── Handlers                  # Обработчики команд и кнопок
│   ├── start_booking()       # Выбор услуги
│   ├── handle_service()      # Выбор мастера
│   ├── handle_master()       # Выбор даты
│   ├── handle_calendar()     # Календарь
│   ├── handle_time()         # Выбор времени
│   ├── handle_confirmation() # Подтверждение
│   ├── my_bookings()         # Мои записи
│   ├── admin_panel()         # Админ-панель
│   └── master_panel()        # Панель мастера
└── SalonBotSystem           # Инициализация и запуск

Data Models (in-memory):
├── bookings              # {id: {service, master, date, time, user, status}}
├── client_data           # {user_id: {service, master, date, time}}
├── user_sessions         # {user_id: current_state}
├── master_stats          # {master: {bookings, revenue, rating}}
├── master_schedules      # {master: {working_days, vacations}}
└── analytics_data        # {service_popularity, master_popularity, ...}
```

## 🛠️ Разработка

### Добавить новую услугу

1. Добавьте в `CONFIG["services"]`:
```python
"услуга": 1500,
```

2. Добавьте паттерн в `service_patterns` для нечёткого поиска:
```python
'услуга': r'(услуг|сервис)',
```

### Добавить мастера

1. Добавьте в `CONFIG["masters"]`:
```python
"Имя": 987654321,  # Telegram ID
```

2. Инициализация остального автоматическая.

### Добавить выходной/отпуск мастера

```python
master_schedules["Анна"]["vacations"].append("2025-11-20")
```

## 📊 Точки расширения

- **Сохранение данных**: Замените in-memory модели на JSON/БД в `main()`
- **Платежи**: Интегрируйте Stripe/YooKassa в `handle_confirmation()`
- **Уведомления**: Подключите SMS/Email в `SmartReminderSystem`
- **Импорт**: Добавьте `/upload_schedule` для загрузки расписания

## ⚠️ Ограничения

- 📍 **In-memory storage** — данные теряются при перезагрузке
- 🔐 **Токены в коде** — для production используйте `.env`
- 📈 **Масштабируемость** — для >1000 пользователей добавьте БД

## 📝 Лицензия

MIT

## 📞 Контакты

Вопросы и улучшения → GitHub Issues