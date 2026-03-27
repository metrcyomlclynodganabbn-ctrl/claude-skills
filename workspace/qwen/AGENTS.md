# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

Python project for parsing and updating news from fondvyzov.ru via Bitrix REST API. Contains 117 RU news, 87 EN news, and 130 priority news as DOCX files with images.

## Bitrix API Specifics

- OAuth tokens stored in `.bitrix_tokens.json` (auto-generated on first run)
- IBLOCK IDs: 5 (default), 19 (RU news), 65 (EN news)
- API methods: `lists.element.get`, `lists.element.update`
- IBLOCK_TYPE_ID: try "news" first, fallback to "lists"
- Base URL: `https://fondvyzov.ru/rest/`

## News Folder Structure

- Format: `fondvyzov_ru_news/news_XXX_Заголовок/`
- Each folder contains: one `.docx` file + images (`.jpeg`, `.png`)
- Title normalization via `clean_title()` for matching
- Prefix `news_XXX_` must be preserved for correct parsing

## DOCX to HTML Conversion

Безопасное преобразование DOCX в HTML для интеграции с Bitrix24 API:

### Форматирование текста

- **Bold text** → `<b>` теги
- *Italic text* → `<i>` теги
- **Combined** (bold + italic) → `<i><b>...</b></i>` теги

### Безопасность и экранирование

- Все HTML символы экранируются с помощью `html.escape()` для предотвращения XSS-атак
- Экранируются символы: `<`, `>`, `&`, `"`, `'`
- Экранирование применяется ПЕРЕД добавлением форматирования

### Производительность и оптимизация

- Оптимизировано для высокообъёмных API обновлений (сотни новостей)
- Пропускаются пустые параграфы и run'ы для ускорения обработки
- Используются списки вместо конкатенации строк

### Обработка ошибок и граничные случаи

- **Пустые файлы**: Возвращается пустая строка
- **Файлы без форматирования**: Возвращается чистый текст в `<p>` тегах
- **Файлы с некорректным форматированием**: Повреждённые run'ы игнорируются, обработка продолжается
- **Null/None вход**: Вызывает `ValueError` с информативным сообщением
- **Несуществующий путь**: Вызывает `FileNotFoundError`
- **Неверное расширение**: Вызывает `ValueError` (только .docx)
- **Нет прав на чтение**: Вызывает `PermissionError`
- **Повреждённый DOCX**: Вызывает `ValueError` с описанием ошибки

### Использование

```python
from update_rest import extract_html_from_docx

html_content = extract_html_from_docx("fondvyzov_ru_news/news_001_Заголовок/файл.docx")
# Результат: "<p><i><b>Заголовок</b></i> новости</p><p>Основной текст...</p>"
```

### Валидация входных параметров

- Проверка типа: должен быть строка
- Проверка на None/empty
- Проверка существования файла
- Проверка расширения (.docx)
- Проверка прав на чтение

### Интеграция с Bitrix API

- Выходной формат готов для отправки в `lists.element.update`
- Поддерживает кириллицу и специальные символы
- Сохраняет структуру документа (абзацы, форматирование)

## Related Project

- Location: `/Users/kapyshonchik/workspace/bitrix-browser-verify-2026-03-21/`
- Uses Playwright (via `mcp_adapter.py`) + Mammoth for browser-based updates
- Current status: Automation script upgraded to support creating missing items via `--action create` (including 100 missing Priority news and 23 EN news) and enforcing `ACTIVE` status for hidden RU news. Ready for final site deployment.
- Commands:
  - Update: `venv/bin/python3 -u scripts/update_texts_prod.py --mode run --action update`
  - Create: `venv/bin/python3 -u scripts/update_texts_prod.py --mode run --action create`

## Archives

- `fondvyzov_news_archive.zip` (304 MB): RU + EN news
- `fondvyzov_priority_news_parsed.zip` (361 MB): priority news
- `ALL_NEWS_VZ_OLD.zip` (304 MB): old archive

## Получение API ключей

Если у вас нет `BITRIX_API_ID` и `BITRIX_API_SECRET`, их нужно получить через создание локального приложения в Bitrix:

1. **Войдите на сайт** fondvyzov.ru
2. Перейдите: **Настройки → Настройки продукта → Сайты → Настройки скриптов (REST)**
3. Нажмите: **Добавить локальное приложение**
4. Заполните:
   - **Название** - любое название для вашего приложения
   - **Описание** - краткое описание
   - **Права доступа**: выберите нужные права (обычно "Чтение", "Запись")
   - **Срок действия**: укажите период (например, "Неограниченный")
   - **Тип доступа**: выберите "Внешнее" или "Внутреннее"
5. Нажмите **"Сохранить"**

6. После сохранения вы получите:
   - **Client ID** (`BITRIX_API_ID`) - скопируйте его в `.env`
   - **Client Secret** (`BITRIX_API_SECRET`) - скопируйте его в `.env`

7. Теперь можно запускать скрипты с API ключами

### Важно

- Локальное приложение создаётся в контексте вашего портала
- API ключи уникальны для каждого приложения
- Не делитесь ключами с другими пользователями
