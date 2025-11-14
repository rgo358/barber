# 🔌 REST API для Web App

Документация API endpoints для синхронизации Web App ↔ Telegram Bot.

## 📡 Base URL

```
http://localhost:5000  (локально)
https://ваш-домен.herokuapp.com  (production)
```

## 📋 Endpoints

### 1️⃣ POST /api/bookings

**Создать новое бронирование**

**Request:**
```bash
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "service": "Мужская стрижка",
    "master": "Дмитрий",
    "date": "2025-11-20",
    "time": "14:30",
    "userId": 123456,
    "userName": "Иван",
    "price": 0
  }'
```

**Response (201):**
```json
{
  "id": "123456_20251120_143000",
  "service": "Мужская стрижка",
  "master": "Дмитрий",
  "date": "2025-11-20",
  "time": "14:30",
  "status": "confirmed",
  "created_at": "2025-11-14T22:00:00Z"
}
```

---

### 2️⃣ GET /api/bookings

**Получить бронирования пользователя**

**Request:**
```bash
curl -X GET "http://localhost:5000/api/bookings?user_id=123456"
```

**Response (200):**
```json
[
  {
    "id": "123456_20251120_143000",
    "service": "Мужская стрижка",
    "master": "Дмитрий",
    "date": "2025-11-20",
    "time": "14:30",
    "status": "confirmed"
  },
  {
    "id": "123456_20251121_160000",
    "service": "Окрашивание",
    "master": "Александр",
    "date": "2025-11-21",
    "time": "16:00",
    "status": "confirmed"
  }
]
```

---

### 3️⃣ POST /api/available-times

**Получить доступные временные слоты**

**Request:**
```bash
curl -X POST http://localhost:5000/api/available-times \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-11-20",
    "master": "Дмитрий"
  }'
```

**Response (200):**
```json
{
  "date": "2025-11-20",
  "master": "Дмитрий",
  "available_times": [
    "08:00", "08:30", "09:00", "09:30", "10:00",
    "10:30", "11:00", "11:30", "14:00", "14:30",
    "15:00", "15:30", "16:00", "16:30", "17:00"
  ]
}
```

---

### 4️⃣ GET /api/admin/stats

**Статистика для админа**

**Request:**
```bash
curl -X GET "http://localhost:5000/api/admin/stats?admin_id=5892547881"
```

**Response (200):**
```json
{
  "total_bookings": 24,
  "today_bookings": 5,
  "total_revenue": 12500,
  "masters": {
    "Дмитрий": {
      "bookings": 8,
      "revenue": 4000,
      "rating": 5.0
    },
    "Александр": {
      "bookings": 9,
      "revenue": 4500,
      "rating": 4.9
    }
  }
}
```

---

### 5️⃣ POST /api/cancel-booking

**Отменить бронирование**

**Request:**
```bash
curl -X POST http://localhost:5000/api/cancel-booking \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "123456_20251120_143000",
    "user_id": 123456
  }'
```

**Response (200):**
```json
{
  "id": "123456_20251120_143000",
  "status": "cancelled",
  "message": "Бронирование отменено"
}
```

---

### 6️⃣ POST /api/reschedule-booking

**Перенести бронирование**

**Request:**
```bash
curl -X POST http://localhost:5000/api/reschedule-booking \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "123456_20251120_143000",
    "user_id": 123456,
    "new_date": "2025-11-21",
    "new_time": "15:00"
  }'
```

**Response (200):**
```json
{
  "id": "123456_20251120_143000",
  "status": "rescheduled",
  "old_date": "2025-11-20",
  "old_time": "14:30",
  "new_date": "2025-11-21",
  "new_time": "15:00"
}
```

---

## 🔐 Ошибки

### 400 Bad Request

```json
{
  "error": "Invalid request",
  "details": "Service must be provided"
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Admin ID not valid"
}
```

### 404 Not Found

```json
{
  "error": "Booking not found",
  "id": "123456_20251120_143000"
}
```

### 409 Conflict

```json
{
  "error": "Time slot already booked",
  "date": "2025-11-20",
  "time": "14:30",
  "master": "Дмитрий"
}
```

### 500 Server Error

```json
{
  "error": "Internal server error",
  "details": "Database connection failed"
}
```

---

## 🔄 Webhooks (опционально)

### Уведомления о новых бронированиях

**Если хотите получать уведомления:**

```python
# Настройте в salon_bot.py:
WEBHOOK_URL = "https://your-webhook-handler.com/booking"

# Бот отправит POST на этот URL:
{
  "event": "booking_created",
  "booking": {...},
  "timestamp": "2025-11-14T22:00:00Z"
}
```

---

## 📊 Rate Limiting

Нет ограничений для локального использования.

Для production рекомендуется:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/bookings', methods=['POST'])
@limiter.limit("10 per minute")
def create_booking():
    ...
```

---

## 🧪 Тестирование с cURL

### Быстрый тест

```bash
# Проверить, что API работает
curl -X GET http://localhost:5000/api/admin/stats?admin_id=5892547881 | jq .

# Создать бронирование
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "service": "Мужская стрижка",
    "master": "Дмитрий",
    "date": "2025-11-20",
    "time": "14:30",
    "userId": 123456,
    "userName": "Иван"
  }' | jq .
```

### Тест в Python

```python
import requests

# POST запрос
response = requests.post(
    'http://localhost:5000/api/bookings',
    json={
        'service': 'Мужская стрижка',
        'master': 'Дмитрий',
        'date': '2025-11-20',
        'time': '14:30',
        'userId': 123456,
        'userName': 'Иван'
    }
)

print(response.json())
```

---

## 🚀 Запуск локально

```bash
# 1. Установите зависимости
pip install flask flask-cors

# 2. Запустите Flask сервер
python3 salon_bot.py

# 3. Тестируйте endpoints
curl http://localhost:5000/api/admin/stats?admin_id=5892547881
```

---

## 📚 Документы

- [DEPLOYMENT.md](DEPLOYMENT.md) - развёртывание Web App
- [GIT-WORKFLOW.md](GIT-WORKFLOW.md) - процесс коммитов
- [CONTRIBUTING.md](CONTRIBUTING.md) - правила разработки

---

**Версия:** 1.0  
**Статус:** Production Ready ✅
