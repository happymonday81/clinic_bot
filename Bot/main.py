import asyncio
import logging
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from dev_console import run_console


# ========== 0. НАСТРОЙКА ПУТЕЙ ==========
BOT_DIR = Path(__file__).resolve().parent
ROOT_DIR = BOT_DIR.parent

if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

# Создаем папки
LOGS_DIR = BOT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

STATIC_DIR = BOT_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

MEDIA_DIR = BOT_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)


# ========== 1. ЛОГИРОВАНИЕ ==========
from config.logging_config import setup_logging  # noqa: E402

logger = setup_logging(level=logging.INFO, log_file=str(LOGS_DIR / "bot.log"))

logger.info("📂 Bot directory: %s", BOT_DIR)
logger.info("📂 Root directory: %s", ROOT_DIR)


# ========== 2. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
env_path = ROOT_DIR / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info("✅ .env loaded from root")
else:
    load_dotenv()
    logger.warning("⚠️ .env not found in root")


# ========== 3. КОНФИГ ==========
from config import BOT_TOKEN  # noqa: E402

# Проверяем токен только если НЕ запущен dev-режим
# (Но учти, что config.py сам может падать с ошибкой, если токена нет. 
#  Если config.py уже упал - тогда оставь как есть, это нормально.)
if not BOT_TOKEN and "--dev" not in sys.argv:
    logger.error("❌ BOT_TOKEN missing!")
    sys.exit(1)

if BOT_TOKEN:
    logger.info(f"🔑 Token loaded: {BOT_TOKEN[:6]}...{BOT_TOKEN[-4:]}")
else:
    logger.warning("⚠️ No BOT_TOKEN found. Running in offline mode.")


# ========== 4. LOCK FILE ==========
LOCK_FILE = os.path.join(tempfile.gettempdir(), f"bot_{BOT_TOKEN[-10:]}.lock")


def is_already_running() -> bool:
    if not os.path.exists(LOCK_FILE):
        return False

    try:
        with open(LOCK_FILE, "r") as f:
            pid = int(f.read().strip())

        if sys.platform == "win32":
            import ctypes

            handle = ctypes.windll.kernel32.OpenProcess(0x0001, False, pid)

            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)

                file_time = datetime.fromtimestamp(os.path.getmtime(LOCK_FILE))

                if datetime.now() - file_time > timedelta(minutes=5):
                    logger.warning("🧹 Removing stale lock (>5 min)")
                    os.remove(LOCK_FILE)
                    return False

                return True
            else:
                os.remove(LOCK_FILE)
                return False

        else:
            os.kill(pid, 0)
            return True

    except Exception:
        try:
            os.remove(LOCK_FILE)
        except:
            pass
        return False


def create_lock():
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError as e:
        logger.error("Failed to remove lock: %s", e)


# ========== 5. БОТ И ДИСПЕТЧЕР ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logger.info("✅ Bot & Dispatcher initialized")


# ========== 6. СЕРВИСЫ ==========
from services.appointment_service import AppointmentService
from services.notification_service import NotificationService
from storage.session_manager import UserSessionManager

session_manager = UserSessionManager(ttl_minutes=30)

appointment_service = AppointmentService(
    session_manager=session_manager
)

notification_service = NotificationService(
    bot=bot
)

logger.info("✅ Services initialized")


async def background_notifications():
    logger.info("🕒 Notification task started")

    while True:
        try:
            await notification_service.check_and_send_reminders()
        except Exception as e:
            logger.error("Notification error: %s", e, exc_info=True)

        await asyncio.sleep(60)


# ========== 7. ХЕНДЛЕРЫ ==========
from handlers import (  # noqa: E402
    admin_router,
    appointment_router,
    callbacks_router,
    main_menu_router,
    start_router,
)

from handlers.appointment import init_appointment
from handlers.callbacks import init_callbacks
from handlers.main_menu import init_main_menu
from handlers.start import init_start


init_start(session_manager)
init_appointment(appointment_service, session_manager)
init_callbacks(appointment_service, session_manager)
init_main_menu(session_manager)

dp.include_router(start_router)
dp.include_router(appointment_router)
dp.include_router(callbacks_router)
dp.include_router(main_menu_router)
dp.include_router(admin_router)

logger.info("✅ Routers registered")


# ========== 8. ЗАПУСК ==========
async def main():

    logger.info("🚀 Starting bot...")

    # --- DEV MODE ---
    if "--dev" in sys.argv:
        logger.info("🧪 DEV MODE ENABLED")
        await run_console(dp)
        return

    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.error("Webhook delete error: %s", e)

    asyncio.create_task(background_notifications())

    logger.info("📡 Polling started...")

    try:
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")

    finally:
        await bot.session.close()
        remove_lock()


# ========== 9. ENTRYPOINT ==========
if __name__ == "__main__":

    if is_already_running():
        logger.error("❌ Already running!")
        sys.exit(1)

    create_lock()

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

    except Exception as e:
        logger.critical("Fatal error: %s", e, exc_info=True)

    finally:
        remove_lock()
