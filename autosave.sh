#!/bin/bash
# 🚀 КОНТРОЛЛЕР АВТОМАТИЧЕСКОГО СОХРАНЕНИЯ

REPO_PATH="/workspaces/barber"
SCRIPT="$REPO_PATH/auto-commit.sh"
PID_FILE="$REPO_PATH/.auto-commit.pid"

# ФУНКЦИИ
start_autosave() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "⚠️  Автосохранение уже запущено (PID: $OLD_PID)"
            return 1
        fi
    fi
    
    # ДЕЛАЕМ СКРИПТ ИСПОЛНЯЕМЫМ
    chmod +x "$SCRIPT"
    
    # ЗАПУСКАЕМ В ФОНЕ И СОХРАНЯЕМ PID
    nohup "$SCRIPT" > /dev/null 2>&1 &
    NEW_PID=$!
    echo "$NEW_PID" > "$PID_FILE"
    
    echo "✅ Автосохранение запущено (PID: $NEW_PID)"
    echo "📝 Логи: $REPO_PATH/auto-commit.log"
    echo "⏹️  Остановить: ./autosave.sh stop"
}

stop_autosave() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Файл PID не найден - процесс не запущен"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID"
        rm "$PID_FILE"
        echo "✅ Автосохранение остановлено (PID: $PID)"
    else
        rm "$PID_FILE"
        echo "⚠️  Процесс с PID $PID не найден, удален pidfile"
    fi
}

status_autosave() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Автосохранение: ОТКЛЮЧЕНО"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Автосохранение: АКТИВНО (PID: $PID)"
        echo "📊 Последние 5 коммитов:"
        cd "$REPO_PATH"
        git log --oneline -5 | sed 's/^/   /'
    else
        echo "❌ Автосохранение: НЕАКТИВНО (процесс умер)"
        rm "$PID_FILE"
    fi
}

tail_logs() {
    tail -f "$REPO_PATH/auto-commit.log"
}

# ПАРСИНГ АРГУМЕНТОВ
case "$1" in
    start)
        start_autosave
        ;;
    stop)
        stop_autosave
        ;;
    status|info)
        status_autosave
        ;;
    logs|tail)
        tail_logs
        ;;
    restart)
        stop_autosave
        sleep 1
        start_autosave
        ;;
    *)
        echo "🔄 КОНТРОЛЛЕР АВТОСОХРАНЕНИЯ ПРОЕКТА"
        echo ""
        echo "Использование:"
        echo "  ./autosave.sh start   - Запустить автосохранение"
        echo "  ./autosave.sh stop    - Остановить автосохранение"
        echo "  ./autosave.sh status  - Показать статус"
        echo "  ./autosave.sh logs    - Показать логи (real-time)"
        echo "  ./autosave.sh restart - Перезагрузить"
        echo ""
        echo "💡 Советы:"
        echo "  - Автосохранение коммитит каждые 5 минут при наличии изменений"
        echo "  - Все коммиты помечены меткой 🔄 Auto-save"
        echo "  - Логи сохраняются в: $REPO_PATH/auto-commit.log"
        ;;
esac
