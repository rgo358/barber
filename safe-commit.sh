#!/bin/bash
# 💾 SAFE-COMMIT - БЕЗОПАСНОЕ СОХРАНЕНИЕ С ПРОВЕРКАМИ

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_PATH="/workspaces/barber"
cd "$REPO_PATH" || exit 1

# ФУНКЦИИ
show_status() {
    echo -e "${BLUE}📊 СТАТУС РЕПО:${NC}"
    git status --short
}

check_python_syntax() {
    echo -ne "${YELLOW}🔍 Проверка Python синтаксиса...${NC}"
    PYTHON_FILES=$(git diff --name-only HEAD | grep '\.py$' || true)
    if [ -n "$PYTHON_FILES" ]; then
        if python3 -m py_compile $PYTHON_FILES 2>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        else
            echo -e " ${RED}✗ ОШИБКА!${NC}"
            python3 -m py_compile $PYTHON_FILES
            return 1
        fi
    else
        echo -e " ${YELLOW}пропущено${NC}"
        return 0
    fi
}

check_files_size() {
    echo -ne "${YELLOW}📏 Проверка размера файлов...${NC}"
    LARGE_FILES=$(find . -type f -size +50M ! -path './.git/*' ! -path './venv/*' 2>/dev/null || true)
    if [ -n "$LARGE_FILES" ]; then
        echo -e " ${RED}✗ Файлы > 50 MB${NC}"
        echo "$LARGE_FILES"
        return 1
    else
        echo -e " ${GREEN}✓${NC}"
        return 0
    fi
}

check_secrets() {
    echo -ne "${YELLOW}🔐 Проверка на секреты...${NC}"
    # Игнорируем строки из примеров/документации/комментариев
    # Ищем реальные присвоения с кавычками
    LEAKED=$(git diff HEAD --unified=0 | grep -E '^\+[^+]' | grep -E '(password|token|secret|api_key)\s*=\s*["\x27]' | grep -v -E '(#|echo|XXXX|\.\.\.|example)' || true)
    if [ -n "$LEAKED" ]; then
        echo -e " ${RED}✗${NC}"
        return 1
    else
        echo -e " ${GREEN}✓${NC}"
        return 0
    fi
}

safe_commit() {
    local msg="$1"
    
    echo -e "${BLUE}💾 ПРОЦЕСС КОММИТА:${NC}"
    
    # Показываем что будет добавлено
    echo -ne "${YELLOW}  • Добавление файлов...${NC}"
    git add -A
    CHANGES=$(git diff --cached --name-only | wc -l)
    echo -e " ${GREEN}✓ ($CHANGES файлов)${NC}"
    
    # Запускаем проверки
    if ! check_python_syntax; then
        echo -e "${RED}❌ Отмена из-за синтаксических ошибок${NC}"
        git reset
        return 1
    fi
    
    if ! check_files_size; then
        echo -e "${RED}❌ Отмена: файлы слишком большие${NC}"
        git reset
        return 1
    fi
    
    if ! check_secrets; then
        echo -e "${RED}❌ ОТМЕНА: ОБНАРУЖЕНЫ СЕКРЕТЫ!${NC}"
        echo -e "${YELLOW}   Удалите чувствительные данные перед коммитом${NC}"
        git reset
        return 1
    fi
    
    # Коммитим
    echo -ne "${YELLOW}  • Создание коммита...${NC}"
    if git commit -m "$msg" 2>&1 | tee /tmp/commit.log; then
        COMMIT_SHA=$(git rev-parse --short HEAD)
        echo -e " ${GREEN}✓${NC}"
        echo -e "${GREEN}✅ КОММИТ УСПЕШЕН!${NC}"
        echo -e "${BLUE}   SHA: $COMMIT_SHA${NC}"
        echo -e "${BLUE}   Сообщение: $msg${NC}"
        return 0
    else
        echo -e " ${RED}✗ ОШИБКА КОММИТА${NC}"
        return 1
    fi
}

safe_push() {
    echo -e "${BLUE}🚀 ПРОЦЕСС ПУША:${NC}"
    
    # Проверяем коммиты
    LOCAL_COMMITS=$(git rev-list origin/main..HEAD 2>/dev/null | wc -l || echo 0)
    echo -ne "${YELLOW}  • Проверка коммитов...${NC}"
    if [ "$LOCAL_COMMITS" -eq 0 ]; then
        echo -e " ${YELLOW}нечего пушить${NC}"
        return 0
    else
        echo -e " ${GREEN}$LOCAL_COMMITS коммитов${NC}"
    fi
    
    # Показываем коммиты
    echo -e "${BLUE}   Коммиты:${NC}"
    git log --oneline -$LOCAL_COMMITS | sed 's/^/      /'
    
    # Подтверждение
    read -p "📤 Отправить на GitHub? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⏭️  Пуш отменён${NC}"
        return 0
    fi
    
    # Пушим
    echo -ne "${YELLOW}  • Отправка на GitHub...${NC}"
    if git push origin main 2>&1 | tee /tmp/push.log; then
        echo -e " ${GREEN}✓${NC}"
        echo -e "${GREEN}✅ ПУША УСПЕШЕН!${NC}"
        return 0
    else
        echo -e " ${RED}✗ ОШИБКА ПУША${NC}"
        cat /tmp/push.log
        return 1
    fi
}

# MAIN
case "$1" in
    commit)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Ошибка: укажите сообщение коммита${NC}"
            echo "Использование: $0 commit 'Сообщение'"
            exit 1
        fi
        show_status
        echo ""
        safe_commit "$2"
        ;;
    push)
        show_status
        echo ""
        safe_push
        ;;
    sync)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Ошибка: укажите сообщение коммита${NC}"
            echo "Использование: $0 sync 'Сообщение'"
            exit 1
        fi
        show_status
        echo ""
        if safe_commit "$2"; then
            echo ""
            safe_push
        fi
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "${BLUE}💾 БЕЗОПАСНОЕ УПРАВЛЕНИЕ РЕПО${NC}"
        echo ""
        echo "Использование:"
        echo "  $0 status              - показать статус"
        echo "  $0 commit 'Сообщение'  - безопасный коммит"
        echo "  $0 push                - безопасный пуш"
        echo "  $0 sync 'Сообщение'    - коммит + пуш"
        echo ""
        echo "Примеры:"
        echo "  $0 commit '✨ Добавить web-app.html'"
        echo "  $0 sync '🔧 Обновить конфиг'"
        echo ""
        echo "Проверки перед операциями:"
        echo "  ✓ Python синтаксис"
        echo "  ✓ Размер файлов (макс 50 MB)"
        echo "  ✓ Чувствительные данные (tokens, passwords)"
        echo "  ✓ Staged/unstaged изменения"
        ;;
esac
