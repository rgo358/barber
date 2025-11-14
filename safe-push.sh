#!/bin/bash
# 🚀 PRE-PUSH HOOK - ФИНАЛЬНЫЕ ПРОВЕРКИ ПЕРЕД ПУШЕМ

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 PRE-PUSH CHECKS...${NC}"

# 1️⃣ КОЛИЧЕСТВО КОММИТОВ
echo -ne "${YELLOW}  • Проверка коммитов...${NC}"
LOCAL_COMMITS=$(git rev-list origin/main..HEAD 2>/dev/null | wc -l)
if [ "$LOCAL_COMMITS" -eq 0 ]; then
    echo -e " ${YELLOW}нечего пушить${NC}"
    exit 0
else
    echo -e " ${GREEN}$LOCAL_COMMITS коммитов к отправке${NC}"
fi

# 2️⃣ ПРОВЕРКА РАБОЧЕЙ ДИРЕКТОРИИ
echo -ne "${YELLOW}  • Проверка рабочей директории...${NC}"
if ! git diff-files --quiet; then
    echo -e " ${RED}✗ ОШИБКА!${NC}"
    echo -e "${RED}Есть изменения в файлах (не staged):${NC}"
    git diff-files --name-status
    exit 1
fi
echo -e " ${GREEN}✓${NC}"

# 3️⃣ ПРОВЕРКА STAGED CHANGES
echo -ne "${YELLOW}  • Проверка staged changes...${NC}"
if ! git diff --cached --quiet; then
    echo -e " ${RED}✗ ОШИБКА!${NC}"
    echo -e "${RED}Есть staged changes, которые не закоммичены:${NC}"
    git diff --cached --name-status
    exit 1
fi
echo -e " ${GREEN}✓${NC}"

# 4️⃣ ПРОВЕРКА ВЕТКИ
echo -ne "${YELLOW}  • Проверка ветки...${NC}"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo -e " ${GREEN}✓ main${NC}"
else
    echo -e " ${YELLOW}⚠ $CURRENT_BRANCH${NC}"
fi

# 5️⃣ ПРОВЕРКА ЧУВСТВИТЕЛЬНЫХ ФАЙЛОВ
echo -ne "${YELLOW}  • Проверка на токены/пароли...${NC}"
if git ls-files | grep -q -E '\.env|secrets|config\.local'; then
    echo -e " ${RED}✗ ОШИБКА!${NC}"
    echo -e "${RED}Обнаружены чувствительные файлы${NC}"
    exit 1
fi
echo -e " ${GREEN}✓${NC}"

echo -e "${GREEN}✅ ГОТОВО К ОТПРАВКЕ!${NC}"
echo -e "${BLUE}Коммиты:${NC}"
git log --oneline -$LOCAL_COMMITS | sed 's/^/   /'

exit 0
