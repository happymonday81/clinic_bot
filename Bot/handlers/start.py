import logging

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from config import WELCOME_IMAGE_PATH
from keyboards.appointment import language_keyboard
from locales import get_text

logger = logging.getLogger(__name__)

router = Router()

# Глобальная переменная для инициализации
from storage.session_manager import UserSessionManager

session_manager: UserSessionManager = None


def init_start(manager: UserSessionManager):
    """Инициализация модуля с зависимостями"""
    global session_manager
    session_manager = manager
    logger.info("Start handler initialized with dependencies")


# ✅ 2. ДОБАВЬ ДЕКОРАТОР СЮДА:
@router.message(Command("start"))
async def handle_start_command(message: types.Message):
    """Обрабатывает команду /start"""
    user_id = message.from_user.id
    logger.info(f"🎯 START COMMAND RECEIVED from user {user_id}")
    
    # Проверяем, есть ли у пользователя сохранённый язык
    # (Убедись, что session_manager не None, иначе будет ошибка)
    if session_manager is None:
        await message.answer("⚠️ Ошибка инициализации бота. Попробуйте позже.")
        logger.error("session_manager is None in start handler!")
        return

    lang = session_manager.get_value(user_id, 'language')
    
    if lang:
        # Если язык уже выбран — показываем главное меню
        from keyboards.main_menu import main_reply_keyboard
        await message.answer(
            get_text(lang, 'welcome'),
            reply_markup=main_reply_keyboard(lang)
        )
        logger.info(f"User {user_id} started bot (existing user, lang={lang})")
    else:
        # ✅ ОТПРАВЛЯЕМ ИЗОБРАЖЕНИЕ С ПРИВЕТСТВИЕМ
        try:
            if WELCOME_IMAGE_PATH.exists():
                photo = FSInputFile(str(WELCOME_IMAGE_PATH))
                await message.answer_photo(
                    photo=photo,
                    caption=(
                        "👋 <b>Добро пожаловать в нашу клинику!</b>\n\n"
                        "Я — ваш персональный ассистент для записи к врачу.\n\n"
                        "Please select your language / Выберите язык / 选择语言："
                    ),
                    reply_markup=language_keyboard(),
                    parse_mode='HTML'
                )
                logger.info(f"Sent welcome image to user {user_id}")
            else:
                # Если файл не найден — отправляем только текст
                logger.warning(f"Welcome image not found at {WELCOME_IMAGE_PATH}")
                await message.answer(
                    "👋 <b>Добро пожаловать в нашу клинику!</b>\n\n"
                    "Please select your language / Выберите язык / 选择语言：",
                    reply_markup=language_keyboard(),
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error sending welcome image: {e}")
            # Fallback на текст
            await message.answer(
                "👋 <b>Добро пожаловать в нашу клинику!</b>\n\n"
                "Please select your language / Выберите язык / 选择语言：",
                reply_markup=language_keyboard(),
                parse_mode='HTML'
            )