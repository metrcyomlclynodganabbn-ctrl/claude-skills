#!/usr/bin/env bash
# Настройка git репозитория для Claude Skills
# Выполните этот скрипт: bash GIT_SETUP.sh

set -e

echo "🔧 Настройка git репозитория Claude Skills..."
echo ""

cd ~/claude-skills

# Инициализация
if [[ ! -d .git ]]; then
    echo "1/4 Инициализация git..."
    git init
    git config user.name "Claude Skills"
    git config user.email "skills@claude.local"
else
    echo "1/4 Git уже инициализирован ✅"
fi

# Добавление файлов
echo ""
echo "2/4 Добавление файлов в git..."
git add .
git add .gitignore

# Коммит
echo ""
echo "3/4 Создание первого коммита..."
git commit -m "Initial commit: 12 Claude Skills for studio/hq

- UX/UI & Figma: ux-brief, ux-spec, figma-planner, campaign-site
- Documentation: ru-docs-architect, ru-content-ilyahov
- AI & Integrations: ai-agent, mcp-architect, vector-db
- Infrastructure: n8n, telegram-bot, server-admin

Инфраструктура:
- scripts/ для синхронизации
- docs/ с bundles и индексом
- README.md с описанием"

# Статус
echo ""
echo "4/4 Статус репозитория:"
git status

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "Следующие шаги:"
echo "   1. Создайте репозиторий на GitHub (опционально)"
echo "   2. Добавьте remote: git remote add origin <url>"
echo "   3. Запушьте: git push -u origin main"
