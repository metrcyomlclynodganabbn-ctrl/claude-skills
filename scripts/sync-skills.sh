#!/usr/bin/env bash
# sync-skills.sh — Синхронизация навыков между репозиторием и Claude Code
# Использует символические ссылки для двусторонней синхронизации

set -euo pipefail

# Пути
REPO_SKILLS="$HOME/claude-skills/skills"
CLAUDE_SKILLS="$HOME/.claude/skills"

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Проверка существования директорий
check_directories() {
    if [[ ! -d "$REPO_SKILLS" ]]; then
        log_error "Репозиторий навыков не найден: $REPO_SKILLS"
        exit 1
    fi

    if [[ ! -d "$CLAUDE_SKILLS" ]]; then
        log_info "Создание директории Claude Skills: $CLAUDE_SKILLS"
        mkdir -p "$CLAUDE_SKILLS"
    fi
}

# Создание символической ссылки для навыка
link_skill() {
    local skill_name="$1"
    local repo_path="$REPO_SKILLS/$skill_name"
    local claude_path="$CLAUDE_SKILLS/$skill_name"

    if [[ ! -d "$repo_path" ]]; then
        log_error "Навык не найден в репозитории: $skill_name"
        return 1
    fi

    # Если уже существует symlink — обновляем
    if [[ -L "$claude_path" ]]; then
        log_info "Обновление symlink: $skill_name"
        rm "$claude_path"
    elif [[ -e "$claude_path" ]]; then
        # Если существует обычная папка — делаем резервную копию
        log_info "Создание резервной копии: $skill_name -> $skill_name.bak"
        mv "$claude_path" "$claude_path.bak"
    fi

    ln -s "$repo_path" "$claude_path"
    log_success "Сlinked: $skill_name"
}

# Синхронизация всех навыков
sync_all() {
    log_info "Синхронизация всех навыков..."

    for skill_dir in "$REPO_SKILLS"/*/; do
        if [[ -d "$skill_dir" ]]; then
            skill_name=$(basename "$skill_dir")
            link_skill "$skill_name"
        fi
    done

    echo ""
    log_success "Синхронизация завершена!"

    # Статистика
    local total=$(find "$REPO_SKILLS" -maxdepth 1 -type d | wc -l | tr -d ' ')
    local linked=$(find "$CLAUDE_SKILLS" -maxdepth 1 -type l | wc -l | tr -d ' ')

    echo ""
    echo "📊 Статистика:"
    echo "   Навыков в репозитории: $((total - 1))"
    echo "   Подключено к Claude: $linked"
}

# Синхронизация одного навыка
sync_one() {
    local skill_name="$1"

    if [[ -z "$skill_name" ]]; then
        log_error "Укажите название навыка"
        echo "Использование: $0 sync <skill-name>"
        exit 1
    fi

    link_skill "$skill_name"
}

# Отмена синхронизации (удаление symlink)
unlink_skill() {
    local skill_name="$1"
    local claude_path="$CLAUDE_SKILLS/$skill_name"

    if [[ -z "$skill_name" ]]; then
        log_error "Укажите название навыка"
        echo "Использование: $0 unlink <skill-name>"
        exit 1
    fi

    if [[ -L "$claude_path" ]]; then
        rm "$claude_path"
        log_success "Отключён: $skill_name"
    elif [[ -e "$claude_path" ]]; then
        log_error "$skill_name — это не символическая ссылка, не удаляю"
    else
        log_error "$skill_name не найден"
    fi
}

# Список всех навыков
list_skills() {
    echo "📋 Навыки в репозитории:"
    echo ""

    for skill_dir in "$REPO_SKILLS"/*/; do
        if [[ -d "$skill_dir" ]]; then
            skill_name=$(basename "$skill_dir")
            skill_file="$skill_dir/SKILL.md"

            if [[ -f "$skill_file" ]]; then
                # Извлекаем description из YAML
                description=$(grep -A1 '^description:' "$skill_file" | tail -1 | sed 's/^[[:space:]]*//' | sed 's/^"//' | sed 's/"$//')

                # Проверяем статус ссылки
                if [[ -L "$CLAUDE_SKILLS/$skill_name" ]]; then
                    status="${GREEN}●${NC} подключен"
                elif [[ -e "$CLAUDE_SKILLS/$skill_name" ]]; then
                    status="${BLUE}○${NC} копия"
                else
                    status="  отключен"
                fi

                printf "   %-35s $status\n" "$skill_name"
                if [[ -n "$description" ]]; then
                    echo "   └─ $description"
                fi
                echo ""
            fi
        fi
    done
}

# Справка
show_help() {
    cat << EOF
sync-skills.sh — Синхронизация навыков между репозиторием и Claude Code

Использование:
    $0 [команда] [аргументы]

Команды:
    sync [skill-name]     Синхронизировать все навыки или один конкретный
    unlink <skill-name>   Отключить навык (удалить symlink)
    list                  Показать список всех навыков со статусом
    help                  Показать эту справку

Примеры:
    $0 sync                      # Синхронизировать все навыки
    $0 sync ux-brief-russian     # Синхронизировать один навык
    $0 unlink old-skill          # Отключить навык
    $0 list                      # Показать список навыков

EOF
}

# Главная логика
main() {
    check_directories

    case "${1:-help}" in
        sync)
            if [[ -n "${2:-}" ]]; then
                sync_one "$2"
            else
                sync_all
            fi
            ;;
        unlink)
            unlink_skill "$2"
            ;;
        list)
            list_skills
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Неизвестная команда: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
