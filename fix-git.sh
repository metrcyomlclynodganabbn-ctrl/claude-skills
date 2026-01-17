#!/usr/bin/env bash
# fix-git.sh — Восстановление git репозитория claude-skills
# Выполните: bash fix-git.sh

set -e

echo "🔧 Восстановление git репозитория..."
echo ""

cd "$(dirname "$0")"

# 1. Удаляем повреждённый .git
if [[ -d ".git" ]]; then
    echo "1/4 Удаление повреждённого .git..."
    rm -rf .git
fi

# 2. Инициализируем заново
echo "2/4 Инициализация git..."
git init
git config user.name "Claude Skills"
git config user.email "skills@claude.local"

# 3. Добавляем файлы
echo "3/4 Добавление файлов..."
git add .
git add .gitignore

# 4. Коммит
echo "4/4 Создание коммита..."
git commit -m "Initial commit: 12 Claude Skills for studio/hq

- UX/UI & Figma: ux-brief, ux-spec, figma-planner, campaign-site
- Documentation: ru-docs-architect, ru-content-ilyahov
- AI & Integrations: ai-agent, mcp-architect, vector-db
- Infrastructure: n8n, telegram-bot, server-admin

Инфраструктура:
- scripts/ для синхронизации
- docs/ с bundles и индексом
- README.md с описанием

Путь к репозиторию:
~/workspace/projects/claude-skills"

echo ""
echo "✅ Git репозиторий восстановлен!"
echo ""
echo "Следующие шаги:"
echo "   1. Создайте репозиторий на GitHub"
echo "   2. Добавьте remote:"
echo "      git remote add origin <your-repo-url>"
echo "   3. Запушьте:"
echo "      git branch -M main"
echo "      git push -u origin main"
echo ""
