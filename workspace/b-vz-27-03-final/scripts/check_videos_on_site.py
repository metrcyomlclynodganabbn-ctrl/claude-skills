#!/usr/bin/env python3
"""Проверка наличия видео на сайте"""

import json
import requests  # type: ignore
import subprocess
from pathlib import Path


def get_token():
    env_file = Path.home() / ".mcp-env"
    if not env_file.exists():
        raise FileNotFoundError(f"Config file not found: {env_file}")

    result = subprocess.run(
        ["grep", "BITRIX_MCP_TOKEN", str(env_file)], capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to find BITRIX_MCP_TOKEN in {env_file}")

    parts = result.stdout.strip().split("=", 1)
    if len(parts) < 2:
        raise ValueError(f"Invalid token format in {env_file}")

    return parts[1].strip().strip('"')


def call_tool(name: str, arguments: dict) -> dict:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
        "id": 1,
    }

    try:
        response = requests.post(
            "https://fondvyzov.ru/bitrix/services/main/ajax.php?action=delight:mcp.Rpc.handler",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"API call failed: {e}")


# Загружаем наши целевые ID
mapping_file = Path(__file__).parent.parent / "data" / "FINAL_VIDEO_UPDATES.json"
if not mapping_file.exists():
    raise FileNotFoundError(f"Mapping file not found: {mapping_file}")

with open(mapping_file) as f:
    mapping = json.load(f)

print("Проверка видео на сайте:\n")

for item in mapping.get("updates", []):
    new_id = item["bitrix_id"]
    name = item["name"][:40]

    sql = f"SELECT DETAIL_TEXT FROM b_iblock_element WHERE ID = {new_id}"

    try:
        result = call_tool("sql", {"query": sql})

        if "result" in result:
            content = result["result"].get("content", [])
            if content and content[0].get("type") == "text":
                text_data = content[0].get("text", "{}")
                try:
                    data = json.loads(text_data)
                except json.JSONDecodeError:
                    print(f"⚠️  ID {new_id}: {name}... [Invalid JSON]")
                    continue

                rows = data.get("rows", [])
                if rows and rows[0]:
                    detail_text = rows[0][0] if len(rows[0]) > 0 else ""

                    has_vk = "vk.com/video_ext.php" in detail_text
                    has_yt = "youtube.com/embed" in detail_text

                    status = "✅" if (has_vk or has_yt) else "❌"
                    video_type = "VK" if has_vk else ("YT" if has_yt else "--")

                    print(f"{status} ID {new_id}: {name}... [{video_type}]")
                else:
                    print(f"⚠️  ID {new_id}: {name}... [No data]")
        else:
            error = result.get("error", {}).get("message", "Unknown error")
            print(f"❌ ID {new_id}: {name}... [API error: {error}]")
    except Exception as e:
        print(f"❌ ID {new_id}: {name}... [{e}]")
