from aiogram import Router, types, F
from aiogram.filters import CommandStart
import logging

from locales import get_text
from keyboards.main_menu import main_reply_keyboard
from keyboards.appointment import language_keyboard
from storage.session_manager import UserSessionManager

logger = logging.getLogger(__name__)

router = Router()

# Глобальная переменная для инициализации
session_manager: UserSessionManager = None


def init_start(manager: UserSessionManager):
    """
    Инициализация модуля с зависимостями
    """
    global session_manager
    session_manager = manager
    logger.info("Start handler initialized with dependencies")


@router.message(CommandStart())
async def start(message: types.Message):
    """Обработчик команды /start (через фильтр)"""
    await handle_start_command(message)


@router.message(F.text == "/start")
async def start_fallback(message: types.Message):
    """Фоллбэк для команды /start (явная проверка текста)"""
    logger.info(f"🎯 Fallback /start triggered for user {message.from_user.id}")
    await handle_start_command(message)


async def handle_start_command(message: types.Message):
    """Основная логика обработки /start"""
    user_id = message.from_user.id
    
    logger.info(f"🎯 START COMMAND RECEIVED from user {user_id}")
    
    # Сбрасываем язык на дефолтный при старте
    session_manager.set_value(user_id, 'language', 'ru')
    
    # Сохраняем username для будущего использования
    username = message.from_user.username or f"User_{user_id}"
    session_manager.set_value(user_id, 'username', username)
    
    logger.info(f"User {user_id} started bot")
    
    await message.answer(
        "🌐 Please select your language / 请选择语言 / Выберите язык:",
        reply_markup=language_keyboard()
    )


@router.callback_query(F.data.startswith('lang:'))
async def set_language(callback: types.CallbackQuery):
    """Устанавливает язык пользователя"""
    lang = callback.data.split(':')[1]
    user_id = callback.from_user.id
    
    session_manager.set_value(user_id, 'language', lang)
    logger.info(f"User {user_id} selected language: {lang}")
    
    await callback.message.delete()
    await callback.message.answer(
        get_text(lang, 'welcome'),
        reply_markup=main_reply_keyboard(lang)
    )
    await callback.answer()