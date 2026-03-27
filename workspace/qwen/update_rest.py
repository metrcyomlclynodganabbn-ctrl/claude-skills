import os
import sys
import json
import urllib.parse
import html
from pathlib import Path
from dotenv import load_dotenv

# Try importing required packages
try:
    import requests
    from docx import Document
except ImportError:
    print("Пожалуйста, установите зависимости: pip install requests python-docx python-dotenv")
    sys.exit(1)

# Загружаем переменные окружения из .env
load_dotenv(Path(__file__).parent / ".env")

BITRIX_URL = os.getenv("BITRIX_URL", "https://fondvyzov.ru").rstrip('/')
CLIENT_ID = os.getenv("BITRIX_API_ID")
CLIENT_SECRET = os.getenv("BITRIX_API_SECRET")

TOKEN_FILE = Path(__file__).parent / ".bitrix_tokens.json"

RU_NEWS_DIR = Path(__file__).parent / "fondvyzov_ru_news"


def get_tokens():
    """Получает токены через OAuth флоу или из файла."""
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "r") as f:
            tokens = json.load(f)
        # В идеале здесь должна быть логика refresh_token, но для разового скрипта сойдет
        return tokens.get("access_token")

    if not CLIENT_ID or not CLIENT_SECRET:
        print("Ошибка: BITRIX_API_ID и BITRIX_API_SECRET должны быть указаны в .env")
        sys.exit(1)

    auth_url = f"{BITRIX_URL}/oauth/authorize/?client_id={CLIENT_ID}"
    print(f"\n[АВТОРИЗАЦИЯ] Пожалуйста, перейдите по ссылке в браузере:")
    print(f"{auth_url}\n")
    print("После авторизации вы будете перенаправлены на страницу.")
    print("Скопируйте полный URL этой страницы (он должен содержать '?code=...') и вставьте сюда.")
    
    redirect_url = input("Введите URL с кодом: ").strip()
    
    try:
        parsed_url = urllib.parse.urlparse(redirect_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        code = params.get("code", [None])[0]
        
        if not code:
            raise ValueError("Параметр 'code' не найден в URL.")
            
    except Exception as e:
        print(f"Ошибка парсинга URL: {e}")
        sys.exit(1)

    print(f"Получен код: {code}. Обмениваем на токен...")
    
    token_url = f"{BITRIX_URL}/oauth/token/"
    # Для некоторых коробчных версий токенкентуется на самом портале
    # Для облака: https://oauth.bitrix.info/oauth/token/
    # Используем портал по умолчанию
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
    }
    
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        # Fallback to oauth.bitrix.info if cloud
        resp = requests.post("https://oauth.bitrix.info/oauth/token/", data=data)
        
    if resp.status_code != 200:
        print(f"Ошибка получения токена: {resp.status_code}")
        print(resp.text)
        sys.exit(1)
        
    tokens = resp.json()
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)
        
    print("Токены успешно получены и сохранены.")
    return tokens.get("access_token")


def bitrix_request(method, params, access_token):
    url = f"{BITRIX_URL}/rest/{method}.json"
    params["auth"] = access_token
    resp = requests.post(url, json=params)
    data = resp.json()
    if "error" in data:
        print(f"API Error ({method}):", data)
    return data


def clean_title(title):
    return ''.join(c.lower() for c in title if c.isalnum() or c.isspace()).strip()


def extract_html_from_docx(docx_path: str) -> str:
    """
    Извлекает HTML содержимое из DOCX файла с безопасной обработкой форматирования.
    
    Эта функция обеспечивает безопасное преобразование DOCX в HTML для интеграции с Bitrix24 API:
    - Жирный текст → <b> теги
    - Курсив → <i> теги
    - Комбинированное форматирование (жирный + курсив) → <i><b>...</b></i>
    - Экранирование всех HTML символов для предотвращения XSS-атак
    - Оптимизировано для высокообъёмных API обновлений
    
    Args:
        docx_path: Путь к DOCX файлу (обязательный параметр)
        
    Returns:
        HTML строка с содержимым документа, готовая для отправки в Bitrix24 API
        
    Raises:
        FileNotFoundError: Если файл не существует по указанному пути
        ValueError: Если путь не является строкой, не имеет расширение .docx, или файл повреждён
        PermissionError: Если нет прав на чтение файла
        Exception: При других ошибках чтения файла
        
    Example:
        >>> html = extract_html_from_docx("fondvyzov_ru_news/news_001_Заголовок/файл.docx")
        >>> print(html)
        <p><i><b>Заголовок</b></i> новости</p>
        <p>Основной текст статьи...</p>
        
    Edge Cases:
        - Пустые файлы: Возвращает пустую строку
        - Файлы без форматирования: Возвращает чистый текст в <p> тегах
        - Файлы с некорректным форматированием: Игнорирует повреждённые run'ы
        - Null/None вход: Вызывает ValueError с информативным сообщением
        - Несуществующий путь: Вызывает FileNotFoundError
    """
    # Валидация входных параметров (защита от null/None и неправильных типов)
    if docx_path is None:
        raise ValueError("docx_path не может быть None")
    
    if not isinstance(docx_path, str):
        raise ValueError(f"docx_path должен быть строкой, получен тип: {type(docx_path).__name__}")
    
    if not docx_path.strip():
        raise ValueError("docx_path не может быть пустой строкой")
    
    # Проверка существования файла
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Файл не найден: {docx_path}")
    
    # Валидация расширения файла
    if not docx_path.lower().endswith('.docx'):
        raise ValueError(f"Файл должен иметь расширение .docx: {docx_path}")
    
    # Проверка прав на чтение
    if not os.access(docx_path, os.R_OK):
        raise PermissionError(f"Нет прав на чтение файла: {docx_path}")
    
    # Безопасное открытие и чтение DOCX файла
    try:
        doc = Document(docx_path)
    except Exception as e:
        raise ValueError(f"Ошибка при чтении DOCX файла {docx_path}: {e}")
    
    html_parts = []
    
    # Обработка каждого параграфа
    for para in doc.paragraphs:
        # Пропускаем пустые абзацы (оптимизация производительности)
        if not para.text.strip():
            continue
            
        try:
            # Обрабатываем каждый run в абзаце с защитой от ошибок
            para_html = _process_paragraph_runs(para)
            
            if para_html:
                html_parts.append(f"<p>{para_html}</p>")
        except Exception as e:
            # Логируем ошибку, но продолжаем обработку других параграфов
            print(f"Предупреждение: Ошибка при обработке параграфа: {e}")
            continue
    
    return "\n".join(html_parts)


def _process_paragraph_runs(para) -> str:
    """
    Обрабатывает runs в абзаце DOCX с безопасным экранированием HTML.
    
    Функция обеспечивает:
    - Безопасное экранирование HTML символов для предотвращения XSS
    - Правильную обработку комбинированного форматирования (bold + italic)
    - Оптимизированную производительность для больших документов
    
    Args:
        para: Объект параграфа из python-docx
        
    Returns:
        HTML строка с форматированием или пустая строка если нет содержимого
        
    Raises:
        Exception: При критических ошибках обработки run'ов
    """
    html_parts = []
    
    for run in para.runs:
        try:
            # Получаем текст из run
            run_text = run.text
            
            # Пропускаем пустые run'ы (оптимизация)
            if not run_text.strip() and not run_text.isspace():
                continue
            
            # БЕЗОПАСНОЕ экранирование HTML символов (предотвращение XSS)
            # html.escape() экранирует: <, >, &, ", '
            run_text = html.escape(run_text, quote=True)
            
            # Применяем форматирование с учётом комбинированных стилей
            # Важно: порядок тегов важен для правильного отображения
            if run.italic and run.bold:
                run_text = f"<i><b>{run_text}</b></i>"
            elif run.italic:
                run_text = f"<i>{run_text}</i>"
            elif run.bold:
                run_text = f"<b>{run_text}</b>"
            
            html_parts.append(run_text)
            
        except Exception as e:
            # Продолжаем обработку даже при ошибке в одном run'е
            print(f"Предупреждение: Ошибка при обработке run: {e}")
            continue
    
    return "".join(html_parts)


def load_local_news():
    local_news = {}
    if not RU_NEWS_DIR.exists():
        print(f"Директория {RU_NEWS_DIR} не найдена!")
        return local_news
        
    for item in RU_NEWS_DIR.iterdir():
        if item.is_dir() and item.name.startswith("news_"):
            docx_files = list(item.glob("*.docx"))
            if docx_files:
                docx_path = docx_files[0]
                parts = item.name.split('_', 2)
                title = parts[2] if len(parts) >= 3 else item.name
                
                local_news[clean_title(title)] = {
                    "original_title": title,
                    "docx_path": docx_path,
                }
    return local_news


def fetch_site_news(access_token, iblock_id=5):
    # Получаем элементы инфоблока новостей
    # Метод зависит от того, используется ли CRM или списки (lists.element.get vs crm.item.list)
    # Для классических новостей на сайте обычно используется lists.element.get
    # Внимание: для lists нужно знать IBLOCK_TYPE_ID, обычно это "news" или "lists"
    # Попробуем получить через lists.element.get
    
    print("Получаем список новостей с сайта...")
    # Сначала пытаемся угадать тип инфоблока или просто отправляем запрос
    # Если не сработает, попробуем crm.item.list
    
    params = {
        "IBLOCK_TYPE_ID": "news", # часто встречающийся тип
        "IBLOCK_ID": iblock_id,
        "ELEMENT_ORDER": {"ID": "DESC"},
        "FILTER": {"ACTIVE": "Y"}
    }
    
    # Можно попробовать получить все без IBLOCK_TYPE_ID? Документация говорит он обязателен.
    # Но мы проверим.
    resp = bitrix_request("lists.element.get", params, access_token)
    
    if "error" in resp and resp["error"] == "ERROR_IBLOCK_TYPE":
        # Попробуем другой тип
        params["IBLOCK_TYPE_ID"] = "lists"
        resp = bitrix_request("lists.element.get", params, access_token)
        
    if "error" in resp:
        print("Критическая ошибка при получении списка новостей!")
        return []
        
    result = resp.get("result", [])
    print(f"Получено новостей с сайта: {len(result)}")
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "test-one", "run"], default="dry-run")
    parser.add_argument("--iblock", type=int, default=5, help="ID инфоблока с новостями")
    args = parser.parse_args()
    
    print(f"--- Запуск в режиме {args.mode.upper()} ---")
    access_token = get_tokens()
    if not access_token:
        print("Нет access token! Выход.")
        return
        
    print("Авторизация успешна. Токен загружен.")
    local_news = load_local_news()
    print(f"Загружено локальных новостей: {len(local_news)}")
    
    site_news = fetch_site_news(access_token, args.iblock)
    if not site_news:
        print("Список новостей с сайта пуст или недоступен.")
        return
        
    matched = []
    not_found_local = []
    
    for s_news in site_news:
        name = s_news.get("NAME", "")
        if not name:
            continue
            
        cleaned_name = clean_title(name)
        match = None
        for l_clean, l_data in local_news.items():
            if l_clean in cleaned_name or cleaned_name in l_clean:
                match = l_data
                break
                
        if match:
            matched.append((s_news, match))
        else:
            not_found_local.append(s_news)
            
    print(f"\n--- Итоги сопоставления ---")
    print(f"Успешно сопоставлено: {len(matched)}")
    print(f"На сайте есть, но локально не найдено: {len(not_found_local)}")
    
    if args.mode == "dry-run":
        print("\nПримеры сопоставленных:")
        for s, l in matched[:5]:
            print(f" С: {s.get('NAME')} -> Л: {l['original_title']}")
            
        print("\nПримеры не найденных локально (есть только на сайте):")
        for n in not_found_local[:5]:
            print(f" С: {n.get('NAME')}")
            
    elif args.mode == "test-one":
        if not matched:
            print("Нет совпадений для теста.")
            return
            
        test_s, test_l = matched[0]
        element_id = test_s.get("ID")
        print(f"Тестовое обновление новости ID {element_id}: {test_s.get('NAME')}")
        
        html_content = extract_html_from_docx(test_l['docx_path'])
        
        # Обновление
        update_params = {
            "IBLOCK_TYPE_ID": site_news[0].get("IBLOCK_TYPE_ID", "news"),
            "IBLOCK_ID": args.iblock,
            "ELEMENT_CODE": test_s.get("CODE") or element_id, # Обычно ELEMENT_ID не передаётся в lists.element.update! А передается ELEMENT_ID 
            "ELEMENT_ID": element_id,
            "FIELDS": {
                "DETAIL_TEXT": html_content,
                "DETAIL_TEXT_TYPE": "html"
            }
        }
        
        print("Отправка запроса на обновление...")
        resp = bitrix_request("lists.element.update", update_params, access_token)
        print(f"Ответ сервера: {resp}")


if __name__ == "__main__":
    main()
