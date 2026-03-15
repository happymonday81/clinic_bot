import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# === 1. Корректная загрузка .env ===
# Явно указываем путь к .env в корне проекта (на уровень выше от config/__init__.py)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# === 2. Загрузка токена ===
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ CRITICAL ERROR: BOT_TOKEN not found in .env file!")
    print(f"   Checked path: {env_path.absolute()}")
    # Не вызываем ошибку здесь, чтобы дать боту шанс упасть красиво в main.py
    BOT_TOKEN = "" 

# === 3. Загрузка админов ===
def load_admin_ids() -> list:
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return []
    
    admin_ids = []
    for item in admin_ids_str.split(","):
        item = item.strip()
        if item:
            try:
                admin_ids.append(int(item))
            except ValueError:
                print(f"⚠️ Invalid admin ID: {item}")
    return admin_ids

ADMIN_IDS = load_admin_ids()

# === 4. Проверка переменных при импорте ===
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing! Check your .env file.")

# Для отладки (удалишь потом)
# print(f"✅ Config loaded successfully. Token: {BOT_TOKEN[:10]}...")
# print(f"✅ Admin IDs: {ADMIN_IDS}")

# ✅ ПУТЬ К ИЗОБРАЖЕНИЮ ПЕРСОНАЖА
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
WELCOME_IMAGE_PATH = STATIC_DIR / "welcome_bot.png"

if not WELCOME_IMAGE_PATH.exists():
    print(f"⚠️ Warning: Welcome image not found at {WELCOME_IMAGE_PATH}")