# upload_to_gitverse.py
# -*- coding: utf-8 -*-
"""
Автономный скрипт для заливки всех .py файлов проекта напрямую на GitVerse через REST API.
Работает на чистом Python, полностью игнорирует баги и ошибки утилиты 'git'.
"""

import os
import sys
import json
import base64
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ==============================================================================
# НАСТРОЙКИ АВТОРИЗАЦИИ И РЕПОЗИТОРИЯ
# ==============================================================================
GITVERSE_OWNER = "s28091973_mail_ru"
GITVERSE_REPO = "mozart"
# ВНИМАНИЕ: Вставь сюда скопированный в настройках токен вместо этой заглушки!
GITVERSE_TOKEN = "dfa59609236ee09a35ee703d927c3e3e984a84ff"
# ==============================================================================

SRC_DIR = "/home/sergey/Documents/configurate"
API_URL = f"https://gitverse.ru{GITVERSE_OWNER}/{GITVERSE_REPO}/contents"


def upload_file_via_api(relative_path, local_full_path):
    """Отправляет одиночный файл на сервер GitVerse через HTTP REST API."""
    try:
        with open(local_full_path, "rb") as f:
            content_bytes = f.read()

        # Кодируем содержимое файла в Base64 для передачи по API
        base64_content = base64.b64encode(content_bytes).decode("utf-8")
        url = f"{API_URL}/{relative_path}"

        # Проверяем, есть ли файл, чтобы получить его SHA (для перезаписи)
        sha = None
        check_req = Request(url, method="GET")
        check_req.add_header("Authorization", f"token {GITVERSE_TOKEN}")
        try:
            with urlopen(check_req) as response:
                data = json.loads(response.read().decode("utf-8"))
                sha = data.get("sha")
        except HTTPError as e:
            if e.code != 404:
                raise

        payload = {
            "message": f"Автоматическое обновление {relative_path} через API",
            "content": base64_content,
            "branch": "master"
        }
        if sha:
            payload["sha"] = sha

        body = json.dumps(payload).encode("utf-8")

        req = Request(url, data=body, method="PUT")
        req.add_header("Authorization", f"token {GITVERSE_TOKEN}")
        req.add_header("Content-Type", "application/json")

        with urlopen(req) as response:
            if response.status in [200, 201]:
                print(f"[+] Успешно залит: {relative_path}")
            else:
                print(f"[-] Статус {response.status} для {relative_path}")

    except Exception as e:
        print(f"[-] Ошибка заливки {relative_path}: {str(e)}")


def main():
    print(f"[*] Старт API-автоматизации для каталога: {SRC_DIR}")

    if not os.path.exists(SRC_DIR):
        print(f"[-] Ошибка: Путь {SRC_DIR} не существует!")
        sys.exit(1)

    if GITVERSE_TOKEN == "вставь_сюда_свой_длинный_токен" or not GITVERSE_TOKEN:
        print("[-] Ошибка: Сначала сгенерируй и впиши в код свой токен доступа GitVerse!")
        sys.exit(1)

    count = 0
    for root, dirs, files in os.walk(SRC_DIR):
        if any(ignored in root for ignored in [".venv", "venv", ".git", "__pycache__", ".idea", ".vscode"]):
            continue

        for file in files:
            if file.endswith(".py") and file != "upload_to_gitverse.py":
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, SRC_DIR)
                web_path = relative_path.replace("\\", "/")

                upload_file_via_api(web_path, full_path)
                count += 1

    print(f"\n[+] Синхронизация завершена. Всего залито файлов: {count}")


if __name__ == "__main__":
    main()
