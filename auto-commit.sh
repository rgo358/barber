#!/bin/bash
# 🔄 АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ ПРОЕКТА В GIT
# Скрипт следит за изменениями и коммитит их с интервалом

REPO_PATH="/workspaces/barber"
COMMIT_INTERVAL=300  # Коммитить каждые 5 минут (300 сек)
LOG_FILE="$REPO_PATH/auto-commit.log"

echo "🔄 Инициализирую автоматическое сохранение..." | tee -a "$LOG_FILE"
echo "📁 Репо: $REPO_PATH" | tee -a "$LOG_FILE"
echo "⏱️  Интервал: ${COMMIT_INTERVAL}s (5 минут)" | tee -a "$LOG_FILE"
echo "📝 Логи: $LOG_FILE" | tee -a "$LOG_FILE"
echo "---" | tee -a "$LOG_FILE"

cd "$REPO_PATH" || exit 1

while true; do
    # ЖДЁМ ИНТЕРВАЛ
    sleep "$COMMIT_INTERVAL"
    
    # ТЕКУЩЕЕ ВРЕМЯ
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # ПРОВЕРЯЕМ, ЕСТЬ ЛИ ИЗМЕНЕНИЯ
    cd "$REPO_PATH"
    git status --porcelain > /tmp/git_status.txt 2>&1
    
    if [ -s /tmp/git_status.txt ]; then
        # ЕСТЬ ИЗМЕНЕНИЯ - КОММИТИМ
        echo "[$TIMESTAMP] ✅ Обнаружены изменения:" | tee -a "$LOG_FILE"
        cat /tmp/git_status.txt | tee -a "$LOG_FILE"
        
        # ДОБАВЛЯЕМ ВСЁ
        git add -A 2>> "$LOG_FILE"
        
        # КОММИТИМ С АВТОМАТИЧЕСКИМ СООБЩЕНИЕМ
        CHANGES_COUNT=$(git diff --cached --stat | tail -1 | awk '{print $1}')
        COMMIT_MSG="🔄 Auto-save: $TIMESTAMP | Changed: $CHANGES_COUNT"
        
        git commit -m "$COMMIT_MSG" 2>> "$LOG_FILE"
        COMMIT_SHA=$(git rev-parse --short HEAD)
        
        echo "[$TIMESTAMP] 🎉 Коммит: $COMMIT_SHA - $COMMIT_MSG" | tee -a "$LOG_FILE"
        echo "---" | tee -a "$LOG_FILE"
    else
        echo "[$TIMESTAMP] ℹ️  Нет изменений" >> "$LOG_FILE"
    fi
done
