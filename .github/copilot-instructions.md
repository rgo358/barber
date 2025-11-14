<!--
Auto-generated guidance for AI coding agents working in this repository.
Project: Telegram Bot for Salon Booking System (Python async)
Keep this concise and actionable.
-->

# Copilot / AI Agent Instructions for `barber`

## Project Overview

**Salon Booking Telegram Bot** — автоматизация записи клиентов в парикмахерскую через Telegram.
- **Language**: Python 3.8+
- **Framework**: `python-telegram-bot` (async)
- **Architecture**: Event-driven, config-based, stateless handlers
- **Entry points**: `deepseek_python_20251114_9e630f.py` (main), `untitled15.py` (optimized), `Untitled15.ipynb` (Colab)

## Core Components & Architecture

### 1. **CONFIG Dictionary** (single source of truth)
```python
CONFIG = {
    "token": "...",  # Telegram bot token
    "admin_id": int,  # Admin user ID
    "masters": {"name": user_id, ...},  # Master → user mapping
    "salon_info": {"phone", "address", "working_hours"},
    "services": {"service_name": price, ...}  # Pricing
}
```
**Rule**: Never hardcode credentials; all config must be editable from `CONFIG` dict.

### 2. **Data Models** (in-memory, no persistence layer)
- `bookings`: `{booking_id: {service, master, date, time, user_id, user_name, status}}`
- `client_data`: Session state per user (service, master, date, time selections)
- `user_sessions`: Track user workflow state (multi-step forms)
- `master_stats`: `{master: {bookings, revenue, rating}}`
- `master_schedules`: `{master: {working_days, vacations}}`
- `analytics_data`: `{service_popularity, master_popularity, time_preferences}`

**Note**: Data is volatile (lost on restart). For persistence, add JSON/DB layer to `main()`.

### 3. **Visual Calendar Class**
`VisualCalendar.create_visual_calendar()` → generates inline keyboard with emoji indicators:
- 🔴 unavailable, 🟢 today, ⚪ available
- Handles month navigation, date selection callbacks
- Used in `handle_calendar()` flow

**Patterns**:
- All dates stored as `YYYY-MM-DD` strings
- Callback data format: `date_YYYY-MM-DD`, `nav_YYYY_MM`, `nav_today`

### 4. **Smart Reminder System Class**
`SmartReminderSystem` → background scheduler (APScheduler) sending reminders 24h before bookings.
- Uses `BackgroundScheduler`, `CronTrigger`
- Called from `run_bot()`, manages async tasks
- Respects salon `working_hours`

### 5. **Message Handlers** (async functions)
Each handler is a step in the booking flow:
1. `start_booking()` → service selection (inline buttons)
2. `handle_service()` → filters masters by service pattern
3. `handle_master()` → shows master details + calendar button
4. `handle_calendar()` → visual month + date selection
5. `handle_time()` → available time slots (default 09:00-21:00)
6. `handle_confirmation()` → final check, saves booking
7. `my_bookings()` → list user's bookings + management options
8. `handle_booking_management()` → cancel/reschedule
9. `admin_panel()` → salon stats, master list
10. `master_panel()` → master's today schedule + revenue

**Key pattern**: All use `callback_data` for state routing (e.g., `service_стрижка`, `master_Анна`, `confirm_BOOKING_ID`).

### 6. **SalonBotSystem Class**
Manages bot lifecycle:
- `setup_handlers()` → registers all `CommandHandler` + `CallbackQueryHandler` with regex patterns
- `run_bot()` → spawns `SmartReminderSystem`, polls Telegram API
- `run_with_restart()` → exponential backoff (max 50 restarts)

## Critical Workflows

### Starting the Bot
```bash
python salon_bot.py
```
- Initializes `SalonBotSystem()`, calls `asyncio.run(main())`
- Supports Colab fallback (nest_asyncio)
- Outputs: "✅ БОТ УСПЕШНО ЗАПУЩЕН!" + command list

### Client Booking Flow
```
/start → [service buttons] → [master buttons] → [calendar] → [time slots] → /confirm
```

### Admin/Master Commands
- `/admin` — salon analytics (revenue, masters, popular services)
- `/master` — today's schedule + earnings

## Developer Workflows

### Adding a New Service
1. Update `CONFIG["services"]` with name and price
2. Add regex pattern to `service_patterns` for fuzzy matching
3. Test in `handle_service()` button display

### Adding a New Master
1. Add to `CONFIG["masters"]` with Telegram user ID
2. Add pattern to `master_patterns` (optional fuzzy matching)
3. Initialize `master_stats` + `master_schedules` auto-entries

### Modifying Booking Logic
- Edit `handle_confirmation()` to save to DB (currently in-memory only)
- Extend `master_schedules[master]["vacations"]` for blocked dates
- Add time slot filtering in `handle_time()`

## Code Patterns & Conventions

1. **Emoji logging**: Status messages use emojis (`✅`, `❌`, `⏰`, etc.)
2. **Regex patterns**: Use raw strings for service/master matching (`r'...'`)
3. **Callback format**: `pattern_param1_param2` (e.g., `date_2025-11-14`)
4. **Error handling**: Try-catch in `run_with_restart()`, `print()` for logging (no logger)
5. **Async/await**: All handlers must be `async def`, use `await update.message.reply_text()`
6. **Config-first**: Hardcoded values discouraged; use `CONFIG` dict

## Integration Points & Dependencies

- **python-telegram-bot**: Async Telegram API wrapper
- **APScheduler**: Background scheduling for reminders + cron jobs
- **nest_asyncio**: Colab compatibility (optional import)
- **No DB layer**: Data lives in RAM (design limitation)

## What NOT to Do

- ❌ Do not persist data without updating `CONFIG` or adding a DB layer first
- ❌ Do not hardcode user IDs or tokens outside `CONFIG`
- ❌ Do not use synchronous Telegram calls (all must be `async`)
- ❌ Do not remove emoji logging (part of user experience)
- ❌ Do not modify callback routing without testing button flows end-to-end

## Testing & Local Development

1. **Requires Telegram bot token** (get from BotFather)
2. **Set admin_id + master IDs** to your Telegram user ID for testing
3. **Commands to test**:
   - `/start` → full booking flow
   - `/mybookings` → your bookings
   - `/admin` → stats (if admin_id matches)
   - `/master` → today's schedule (if master_id matches)

4. **Restart strategy**: Max 50 attempts, exponential backoff (2^n seconds, capped at 300s)

## Key Files

- `salon_bot.py` — production/main version (446 lines) — **ENTRY POINT**
- `README.md` — full documentation with setup, config, commands, and architecture
- `.github/copilot-instructions.md` — this file

---

**For new features**: Ask the human *scope* (feature name, user benefit, impact on CONFIG/handlers). Then propose minimal changes to `CONFIG`, data models, or new handler step. Test with full booking flow before committing.

**For debugging**: Check `user_sessions[user_id]` state, `bookings` dict for booking status, `master_stats` for anomalies. Use print statements (emoji-prefixed) to trace async handler execution.
