# 🚀 Deployment Web App

Гайд по развёртыванию Telegram Mini App на Netlify, Vercel или GitHub Pages.

## 🎯 Опция 1: Netlify (РЕКОМЕНДУЕТСЯ)

### 1. Подготовка

```bash
# Убедитесь, что у вас есть:
# - GitHub аккаунт
# - web-app папка с index.html, style.css, app.js
```

### 2. Создание Netlify сайта

**Способ A: Через GitHub (рекомендуется)**

1. Коммитьте `web-app/` в репо:
```bash
git add web-app/
git commit -m "Add Web App files"
git push origin main
```

2. Зайдите на [netlify.com](https://netlify.com)

3. Нажмите "Add new site" → "Import an existing project"

4. Выберите GitHub → авторизуйтесь → выберите `barber`

5. Настройки деплоя:
   - **Build command:** (оставьте пусто - это статический сайт)
   - **Publish directory:** `web-app`
   - **Branch to deploy:** `main`

6. Нажмите "Deploy site"

**Способ B: Через drag-and-drop**

1. Скачайте `web-app/` папку локально

2. На netlify.com перетащите папку в "Deploy manually"

3. Готово! Вы получите URL: `https://[random-name].netlify.app`

### 3. Кастомное доменное имя (опционально)

```
Netlify Dashboard → Settings → Domain settings → Add custom domain
```

---

## 🎯 Опция 2: Vercel

### 1. Установка Vercel CLI

```bash
npm install -g vercel
```

### 2. Деплой

```bash
cd web-app
vercel --prod
```

3. Следуйте инструкциям

---

## 🎯 Опция 3: GitHub Pages

### 1. Создайте ветку gh-pages

```bash
git checkout --orphan gh-pages
git rm -rf .
cp -r web-app/* .
git add .
git commit -m "Deploy Web App to GitHub Pages"
git push origin gh-pages
```

### 2. Настройте GitHub Pages

Settings → Pages → Source: `gh-pages` → Save

URL: `https://rgo358.github.io/barber`

---

## 🔗 Интеграция с Telegram Bot

### 1. Обновите URL в salon_bot.py

```python
WEBAPP_URL = "https://ваш-домен.netlify.app"  # или ваш URL

# В функции start_booking:
keyboard.append([InlineKeyboardButton(
    "🎨 Забронировать (новый интерфейс)",
    web_app=WebAppInfo(url=WEBAPP_URL)
)])
```

### 2. Тестирование локально

```bash
python3 salon_bot.py
```

Откройте Telegram, нажмите `/start` → "🎨 Забронировать"

---

## 🔒 Безопасность

### 1. Переменные окружения

Создайте `web-app/.env`:
```
REACT_APP_BOT_API=https://ваш-домен.herokuapp.com/api
```

### 2. CORS (если используете API)

Если backend на другом домене, добавьте в Flask:

```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### 3. Валидация данных

Всегда валидируйте на backend:

```python
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.json
    
    # Валидация
    if not data.get('service') or not data.get('master'):
        return jsonify({'error': 'Invalid data'}), 400
    
    # Сохранение
    booking_id = save_booking(data)
    return jsonify({'id': booking_id}), 201
```

---

## 📊 Мониторинг

### Netlify Analytics

- Netlify Dashboard → Analytics
- Просмотр трафика, геолокация, браузеры

### Логи Telegram Bot

```bash
./safe-commit.sh status
# или
tail -f auto-commit.log
```

---

## 🐛 Troubleshooting

### Web App не загружается

1. Проверьте URL в `salon_bot.py`
2. Откройте DevTools (F12) в браузере
3. Проверьте консоль на ошибки
4. Убедитесь, что Telegram Web App SDK загружается

### sendData не работает

```javascript
// Убедитесь, что используете это правильно:
if (window.Telegram && window.Telegram.WebApp) {
    Telegram.WebApp.sendData(JSON.stringify(data));
}
```

### API возвращает 404

1. Проверьте URL в `app.js`
2. Убедитесь, что Flask запущен
3. Проверьте CORS настройки

---

## ✅ Чек-лист для Production

- [ ] Web App работает в Telegram
- [ ] Календарь отображает правильные даты
- [ ] sendData отправляет данные в бот
- [ ] API обрабатывает бронирования
- [ ] Логи сохраняются
- [ ] Тестировано на мобильных устройствах
- [ ] Доменное имя настроено (опционально)
- [ ] HTTPS работает (автоматически на Netlify/Vercel)

---

## 📝 Примеры Deployments

### Netlify (Quickstart)

```
1. netlify.com → "Add new site" → GitHub
2. Выберите barber
3. Publish: web-app
4. Deploy!
```

### Vercel (Quickstart)

```
1. vercel.com → Import Project → GitHub
2. Выберите barber
3. Deploy!
```

### GitHub Pages (Quickstart)

```
git checkout --orphan gh-pages
cp -r web-app/* .
git add . && git commit -m "Deploy"
git push origin gh-pages
```

---

## 🎯 Следующие шаги

1. **Выберите хостинг** (рекомендуем Netlify)
2. **Разверните Web App**
3. **Скопируйте URL** в `salon_bot.py`
4. **Протестируйте** в Telegram
5. **Отследите аналитику** в Netlify Dashboard

---

**Версия:** 1.0  
**Статус:** Production Ready ✅  
**Последнее обновление:** 2025-11-14
