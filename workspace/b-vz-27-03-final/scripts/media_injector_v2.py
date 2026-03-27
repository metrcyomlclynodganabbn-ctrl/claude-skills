import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# Настройка путей
PROJECT_ROOT = Path("/Users/kapyshonchik/workspace/b-vz-27-03-final")
BITRIX_VERIFY_ROOT = Path(
    "/Users/kapyshonchik/workspace/bitrix-browser-verify-2026-03-21"
)
sys.path.insert(0, str(BITRIX_VERIFY_ROOT))

from src.core.config import Config
from src.browser.mcp_adapter import BitrixMCPAdapter

# Пути к данным
DISCREPANCIES_FILE = PROJECT_ROOT / "data/registry_discrepancies.json"
VIDEO_MAPPING_FILE = PROJECT_ROOT / "data/video_mapping_v2.json"
TITLE_MAPPING_FILE = PROJECT_ROOT / "data/bitrix_title_mapping.json"


async def set_detail_text_js(
    adapter: BitrixMCPAdapter, html_to_add: str
) -> Optional[str]:
    """JS-инъекция контента в редактор Битрикс (добавление в начало)."""
    safe_html = html_to_add.replace("`", "\\`").replace("$", "\\$")
    js = f"""
        () => {{
            const html = `{safe_html}`;
            if (window.BXHtmlEditor) {{
                const editors = BXHtmlEditor.getAll ? BXHtmlEditor.getAll() : [];
                for (const ed of editors) {{
                    if (ed.id && ed.id.includes('DETAIL_TEXT')) {{
                        const current = ed.GetContent();
                        if (current.indexOf(html.substring(0, 50)) === -1) {{
                            ed.SetContent(html + "\\n" + current);
                            ed.SaveContent();
                            return "bxhtmleditor_updated";
                        }}
                        return "already_present";
                    }}
                }}
            }}
            const ta = document.getElementById('bxed_DETAIL_TEXT') || document.querySelector('[name="DETAIL_TEXT"]');
            if (ta) {{
                if (ta.value.indexOf(html.substring(0, 50)) === -1) {{
                    ta.value = html + "\\n" + ta.value;
                    return "textarea_updated";
                }}
                return "already_present";
            }}
            return "not_found";
        }}
    """
    return await adapter.evaluate(js)


async def upload_detail_picture(adapter: BitrixMCPAdapter, file_path: Path) -> bool:
    """Загрузка детальной картинки во вкладку 'Подробно'."""
    try:
        # Переключение на вкладку "Подробно"
        await adapter.click("#tab_cont_edit2")
        await asyncio.sleep(2)

        selector = "#bx_file_detail_picture_input"
        if await adapter._page.query_selector(selector):
            await adapter._page.set_input_files(selector, str(file_path.absolute()))
            # Ждем завершения AJAX-загрузки, если она есть
            await asyncio.sleep(2)
            return True
        return False
    except Exception as e:
        print(f"❌ Ошибка загрузки картинки: {e}")
        return False


def resolve_title(record: Dict[str, Any]) -> Optional[str]:
    """Разрешение названия из записи реестра."""
    title = record.get("title")
    if title:
        return str(title)

    path = record.get("new_source_file") or record.get("old_source_file")
    if path:
        return Path(str(path)).stem

    local_id = record.get("local_id", "")
    if local_id and isinstance(local_id, str) and "_" in local_id:
        parts = local_id.split("_", 2)
        if len(parts) > 2:
            return parts[2]

    return None


async def main(dry_run: bool = True) -> None:
    print(f"🚀 Запуск инжектора медиа v3.2 (MODE: {'DRY-RUN' if dry_run else 'LIVE'})")

    try:
        with open(DISCREPANCIES_FILE, "r") as f:
            registry = json.load(f)
        with open(VIDEO_MAPPING_FILE, "r") as f:
            video_mapping = json.load(f)
        with open(TITLE_MAPPING_FILE, "r") as f:
            title_mapping = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return

    targets: Dict[str, Dict[str, Any]] = {}

    # 1. Собираем видео
    for lang_key, items in video_mapping.items():
        lang_code = "ru" if lang_key == "ru_news" else "en"
        ib_id = 19 if lang_code == "ru" else 65
        for news_id, url in items.items():
            title = None
            discrepancies = registry.get("discrepancies", {})
            if isinstance(discrepancies, dict):
                for d_type in discrepancies.keys():
                    records = discrepancies.get(d_type, [])
                    if isinstance(records, list):
                        for rec in records:
                            if isinstance(rec, dict):
                                local_id = rec.get("local_id", "")
                                if local_id and news_id in str(local_id):
                                    title = resolve_title(rec)
                                    if title:
                                        break
                    if title:
                        break

            if title:
                if title not in targets:
                    targets[title] = {"ib_id": ib_id, "lang": lang_code}
                targets[title]["video_url"] = url

    # 2. Собираем картинки
    discrepancies = registry.get("discrepancies", {})
    if isinstance(discrepancies, dict):
        for d_type in ["missing_preview", "missing_photos_body"]:
            for record in discrepancies.get(d_type, []):
                title = resolve_title(record)
                if not title:
                    continue

                old_folder = record.get("old_folder", "")
                lang_code = (
                    "ru"
                    if isinstance(old_folder, str) and "ru_news" in old_folder
                    else "en"
                )
                ib_id = 19 if lang_code == "ru" else 65
                images = record.get("old_images", [])
                if not images:
                    continue

                file_path = Path(str(images[0]))
                if not file_path.exists():
                    file_path = Path(
                        str(file_path).replace("/qwen/", "/qwen/ALL_NEWS_VZ_OLD/")
                    )

                if file_path.exists():
                    if title not in targets:
                        targets[title] = {"ib_id": ib_id, "lang": lang_code}
                    targets[title]["image_path"] = file_path

    config = Config.from_env()
    adapter = BitrixMCPAdapter(mock_mode=False)
    await adapter.start(headless=True)

    try:
        print("🔑 Авторизация...")
        if not await adapter.login(
            config.bitrix_url, config.bitrix_login, config.bitrix_password
        ):
            return

        for title, data in targets.items():
            ib_id = data["ib_id"]
            lang = data["lang"]

            b_id = title_mapping.get(lang, {}).get(title)
            if not b_id or "template" in str(b_id):
                lang_mapping = title_mapping.get(lang, {})
                if isinstance(lang_mapping, dict):
                    for t, tid in lang_mapping.items():
                        if "template" in str(tid):
                            continue
                        if isinstance(t, str) and isinstance(tid, (str, int)):
                            title_prefix = (
                                title[:50].lower() if isinstance(title, str) else ""
                            )
                            t_prefix = t[:50].lower() if isinstance(t, str) else ""
                            if title_prefix in t_prefix or t_prefix in title_prefix:
                                b_id = tid
                                break

            if not b_id:
                continue

            try:
                numeric_id = int(str(b_id).replace("E", "").replace("S", ""))
                print(f"🔄 Изменение ID {numeric_id}: {str(title)[:40]}...")

                if not dry_run:
                    await adapter.open_news_editor(ib_id, numeric_id)
                    updated = False

                    if "video_url" in data:
                        iframe = f'<div class="video-container"><iframe width="560" height="315" src="{data["video_url"]}" frameborder="0" allowfullscreen></iframe></div>'
                        res = await set_detail_text_js(adapter, iframe)
                        if res != "already_present":
                            print(f"  🎬 Видео +")
                            updated = True

                    if "image_path" in data:
                        if await upload_detail_picture(adapter, data["image_path"]):
                            print(f"  📸 Картинка +")
                            updated = True

                    if updated:
                        await adapter._page.click('input[name="save"]')
                        await asyncio.sleep(2)
                        print(f"  ✅ Сохранено.")

            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

    finally:
        await adapter.stop()
        print("🏁 Завершено.")


if __name__ == "__main__":
    asyncio.run(main(dry_run="--run" not in sys.argv))
