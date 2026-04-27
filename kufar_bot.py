import requests
import json
import os
import re
from datetime import datetime

# ========== НАСТРОЙКИ (изменяемые параметры) ==========
# Вставьте сюда URL, который вы скопировали с Kufar
SEARCH_URL = "https://auto.kufar.by/l/cars?elementType=categories&_gl=1*2o7ngg*_gcl_au*MTkwODc2MjEyNi4xNzc3MDY4MTAy*_ga*MTQ0Mzg3ODYxOS4xNzc3MDY4MDg4*_ga_ESH3WRCK3J*czE3NzcyODAxMTUkbzUkZzEkdDE3NzcyODAxNzEkajQkbDAkaDA."

# Токены читаются из переменных окружения (защищённые секреты GitHub Actions)
TELEGRAM_BOT_TOKEN = os.getenv("8517056028:AAHwxR1kXKaPBJYFqsljbXSQDM1y6yk7Ee0")
TELEGRAM_CHAT_ID = os.getenv("5001350756")

# Если вы запускаете скрипт не в GitHub Actions (например, на своём ПК) – 
# раскомментируйте следующие строки и впишите свои токены:
# TELEGRAM_BOT_TOKEN = "вставьте_свой_токен_сюда"
# TELEGRAM_CHAT_ID = "вставьте_свой_chat_id_сюда"

# Файл для хранения уже обработанных ID объявлений
KNOWN_IDS_FILE = "known_ids.json"
# ===================================================

def get_listing_ids_from_kufar():
    """
    Запрашивает страницу поиска Kufar и извлекает ID объявлений.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/537.36"
    }
    try:
        response = requests.get(SEARCH_URL, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
        
        # Ищем ID в атрибутах data-ad-id
        ids = re.findall(r'data-ad-id="(\d+)"', html)
        
        # Если не нашли, пробуем другой паттерн (JSON внутри страницы)
        if not ids:
            ids = re.findall(r'"ad_id":(\d+)', html)
        
        return set(ids)
    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return set()

def load_known_ids():
    if os.path.exists(KNOWN_IDS_FILE):
        with open(KNOWN_IDS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_known_ids(ids):
    with open(KNOWN_IDS_FILE, "w") as f:
        json.dump(list(ids), f)

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Не заданы TELEGRAM_TOKEN или TELEGRAM_CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def main():
    print(f"{datetime.now()} - Проверка новых объявлений...")
    current_ids = get_listing_ids_from_kufar()
    if not current_ids:
        print("Не удалось получить ID. Возможно, изменилась структура страницы.")
        return
    
    known_ids = load_known_ids()
    new_ids = current_ids - known_ids
    
    if new_ids:
        print(f"Найдено новых объявлений: {len(new_ids)}")
        for ad_id in new_ids:
            link = f"https://kufar.by/item/{ad_id}"
            message = f"🔔 <b>Новое помещение!</b>\n{link}"
            send_telegram_message(message)
            print(f"Отправлено: {message}")
        known_ids.update(new_ids)
    else:
        print("Новых объявлений нет.")
    
    save_known_ids(known_ids)

if name == "__main__":
    main()
