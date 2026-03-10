import os
import sys
import asyncio
import tempfile
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from datetime import datetime, timedelta 

# ========== 1. НАСТРОЙКА ЛОГИРОВАНИЯ (СНАЧАЛА ЛОГИ) ==========
from config.logging_config import setup_logging
logger = setup_logging(level=logging.INFO, log_file="logs/bot.log")

# ========== 2. ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========
load_dotenv()

# ========== 3. ИМПОРТ КОНФИГА ==========
from config import BOT_TOKEN, ADMIN_IDS

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found! Check .env file")
    sys.exit(1)

# ========== 4. ФАЙЛ БЛОКИРОВКИ ==========
LOCK_FILE = os.path.join(
    tempfile.gettempdir(),
    f"bot_{BOT_TOKEN[-10:] if BOT_TOKEN else 'unknown'}.lock"
)


def is_already_running() -> bool:
    """Проверяет, запущен ли уже бот (с авто-очисткой stale lock)"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if sys.platform == 'win32':
                try:
                    import ctypes
                    handle = ctypes.windll.kernel32.OpenProcess(0x0001, False, pid)
                    if handle:
                        ctypes.windll.kernel32.CloseHandle(handle)
                        
                        # Авто-очистка если файл старше 5 минут
                        file_time = datetime.fromtimestamp(os.path.getmtime(LOCK_FILE))
                        if datetime.now() - file_time > timedelta(minutes=5):
                            logger.warning(f"🧹 Stale lock file detected (>5 min), removing...")
                            os.remove(LOCK_FILE)
                            return False
                        
                        return True
                    else:
                        os.remove(LOCK_FILE)
                        logger.info("🧹 Removed stale lock (process not found)")
                        return False
                except Exception as e:
                    logger.warning(f"⚠️ Error checking process: {e}")
                    try:
                        os.remove(LOCK_FILE)
                    except:
                        pass
                    return False
            else:
                try:
                    os.kill(pid, 0)
                    return True
                except ProcessLookupError:
                    os.remove(LOCK_FILE)
                    return False
                except PermissionError:
                    return True
        except (ValueError, FileNotFoundError):
            try:
                os.remove(LOCK_FILE)
            except:
                pass
            return False
        except Exception as e:
            logger.warning(f"Error checking lock: {e}")
            return False
    return False


def create_lock():
    """Создаёт файл блокировки"""
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))


def remove_lock():
    """Удаляет файл блокировки"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError as e:
        logger.error(f"Failed to remove lock file: {e}")


# ========== 5. ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

logger.info("✅ Bot and Dispatcher initialized")

# ========== 6. ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРОВ (ДО ИМПОРТА ХЕНДЛЕРОВ!) ==========
from storage.session_manager import UserSessionManager
from services.appointment_service import AppointmentService

session_manager = UserSessionManager(ttl_minutes=30)
appointment_service = AppointmentService(session_manager=session_manager)

logger.info("✅ SessionManager and AppointmentService initialized")

# ========== 7. ИМПОРТ ХЕНДЛЕРОВ ==========
from handlers import (
    start_router,
    appointment_router,
    admin_router,
    callbacks_router,
    main_menu_router  # ← ДОБАВЬ
)

from handlers.start import init_start
from handlers.appointment import init_appointment
from handlers.callbacks import init_callbacks
from handlers.main_menu import init_main_menu  # ← ДОБАВЬ

# ========== 8. ИНИЦИАЛИЗАЦИЯ ХЕНДЛЕРОВ ==========
init_start(session_manager)
init_appointment(appointment_service, session_manager)
init_callbacks(appointment_service, session_manager)
init_main_menu(session_manager)  # ← ДОБАВЬ

logger.info("✅ All handlers initialized with dependencies")

# ========== 9. ПОДКЛЮЧЕНИЕ РОУТЕРОВ (ВАЖЕН ПОРЯДОК!) ==========
dp.include_router(start_router)        # 1. /start команды
dp.include_router(appointment_router)  # 2. Запись (FSM) — ДО main_menu!
dp.include_router(callbacks_router)    # 3. Callback кнопки
dp.include_router(main_menu_router)    # 4. Кнопки меню — ПОСЛЕ appointment
dp.include_router(admin_router)        # 5. Админка

logger.info("✅ All routers registered")

# ========== 11. ЗАПУСК ==========
async def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Starting bot...")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted")
    except Exception as e:
        logger.error(f"⚠️ Error deleting webhook: {e}", exc_info=True)
    
    logger.info(f"🤖 Bot token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    logger.info(f"👥 Admin IDs: {ADMIN_IDS}")
    logger.info("📡 Bot is polling...")
    
    await asyncio.sleep(1)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"❌ Fatal error: {e}", exc_info=True)
        raise
    finally:
        remove_lock()
        await bot.session.close()
        logger.info("🔓 Bot session closed")


# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    # Проверка на дубликат
    if is_already_running():
        logger.error("❌ Bot is already running! Stop the other instance first.")
        sys.exit(1)
    
    # Создаём lock
    create_lock()
    logger.info(f"✅ Lock file created: {LOCK_FILE}")
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.critical(f"❌ Unexpected error: {e}", exc_info=True)
    finally:
        remove_lock()
        logger.info("🔓 Lock file removed")