# Claude Skills для штаба / студии

Набор кастомных Agent Skills для Claude (Claude Code / Claude API):
- под UX/UI и Figma,
- под инфраструктуру (боты, серверы, n8n),
- под знания (документация, векторная БД, MCP, агенты).

Каждый skill — отдельная папка в `skills/` с файлом `SKILL.md`.

## Категории

### 1. UX, сайты, Figma
- `ux-brief-russian` — собирает бриф и документ «Понимание задачи».
- `ux-spec-for-dev-russian` — делает UX/UI‑спеку для разработчиков.
- `political-campaign-site-planner` — планирует структуру сайта кампании/партии.
- `figma-ux-flow-planner-ru` — раскладывает проект в структуру Figma.

### 2. Контент и документация
- `ru-content-ilyahov-style` — тексты на русском в стиле Ильяхова.
- `ru-docs-architect` — ТЗ, README, гайды, SOP, базы знаний.

### 3. Автоматизация и инфраструктура
- `n8n-workflow-designer-ru` — проектирование n8n‑воркфлоу.
- `telegram-bot-architect-ru` — архитектура и ТЗ для Telegram‑ботов.
- `server-admin-consultant-ru` — планы по администрированию серверов (Linux, Docker).

### 4. AI‑агенты и интеграции
- `ai-agent-designer-ru` — проектирование и документация AI‑агентов.
- `mcp-architect-ru` — дизайн MCP‑серверов и их инструментов.
- `vector-db-architect-ru` — схемы векторной БД и RAG‑пайплайны.

## Как использовать

1. Скопируйте нужную папку из `skills/` в каталог Skills Claude (или упакуйте в ZIP для загрузки в Claude/Claude Code).
2. Проверьте YAML‑метаданные в начале `SKILL.md` (`name`, `description`).
3. В Claude:
   - включите Skills в настройках или контейнере (для API), указав соответствующие `skill_id`/название;
   - обратитесь к задаче обычным языком, Claude сам подберёт skill по описанию.

Рекомендуется подключать несколько skills сразу для комплексных сценариев (см. `docs/bundles.md`).

## Структура репозитория

```
claude-skills/
├── README.md
├── skills/
│   ├── ux-brief-russian/
│   │   └── SKILL.md
│   ├── ux-spec-for-dev-russian/
│   │   └── SKILL.md
│   ├── political-campaign-site-planner/
│   │   └── SKILL.md
│   ├── n8n-workflow-designer-ru/
│   │   └── SKILL.md
│   ├── ru-content-ilyahov-style/
│   │   └── SKILL.md
│   ├── figma-ux-flow-planner-ru/
│   │   └── SKILL.md
│   ├── ru-docs-architect/
│   │   └── SKILL.md
│   ├── ai-agent-designer-ru/
│   │   └── SKILL.md
│   ├── telegram-bot-architect-ru/
│   │   └── SKILL.md
│   ├── server-admin-consultant-ru/
│   │   └── SKILL.md
│   ├── mcp-architect-ru/
│   │   └── SKILL.md
│   └── vector-db-architect-ru/
│       └── SKILL.md
└── docs/
    ├── skills-index.md      # список и краткие описания
    └── bundles.md           # готовые наборы skills по задачам
```

## Дополнительно

Каждый skill может содержать дополнительные файлы:
- `reference.md` — развёрнутые инструкции и шаблоны
- `examples.md` — готовые примеры использования

В `SKILL.md` делаются ссылки на эти файлы для progressive disclosure.
