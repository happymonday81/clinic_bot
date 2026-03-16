import os
from pathlib import Path

from dotenv import load_dotenv

# === 1. Корректная загрузка .env ===
# __file__ -> .../clinic_bot/Bot/config/__init__.py
# .parent -> .../clinic_bot/Bot/config/
# .parent.parent -> .../clinic_bot/Bot/
# .parent.parent.parent -> .../clinic_bot/ (КОРЕНЬ ПРОЕКТА)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"

# Явно указываем путь к файлу
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    # print(f"✅ .env loaded from: {env_path}") # Можно раскомментировать для отладки
else:
    # Если не нашли, пробуем стандартный механизм (на всякий случай)
    load_dotenv()
    print(f"⚠️ Warning: .env not found at {env_path}, trying default location.")

# === 2. Загрузка токена ===
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ CRITICAL ERROR: BOT_TOKEN not found in .env file!")
    print(f"   Checked path: {env_path.absolute()}")
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
    BOT_TOKEN = ""

# === 5. Пути к медиа ===
BOT_FOLDER = Path(__file__).resolve().parent.parent
MEDIA_DIR = BOT_FOLDER / "media"
WELCOME_IMAGE_PATH = MEDIA_DIR / "welcome_bot.png"

if not WELCOME_IMAGE_PATH.exists():
    print(f"⚠️ Warning: Welcome image not found at {WELCOME_IMAGE_PATH}")