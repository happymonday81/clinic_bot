from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State  # ✅ ДОБАВЛЕНО
from datetime import datetime
import logging
import re

from locales import get_text
from keyboards.main_menu import main_reply_keyboard
from keyboards.appointment import doctor_inline_keyboard
from keyboards.error import error_reply_keyboard
from storage.session_manager import UserSessionManager
from services.appointment_service import AppointmentService
from utils.helpers import validate_name, validate_phone

logger = logging.getLogger(__name__)

router = Router()

# FSM States
class AppointmentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

# Глобальные переменные для инициализации
session_manager: UserSessionManager = None


def init_appointment(service: AppointmentService, manager: UserSessionManager):
    """
    Инициализация модуля с зависимостями
    
    Args:
        service: AppointmentService instance
        manager: UserSessionManager instance
    """
    global session_manager
    session_manager = manager
    logger.info("Appointment handler initialized with dependencies")


@router.message(F.text.in_([
    get_text('ru', 'btn_appointment'),
    get_text('en', 'btn_appointment'),
    get_text('zh', 'btn_appointment')
]))
async def book_appointment(message: types.Message):
    """Начинает процесс записи"""
    user_id = message.from_user.id
    
    logger.info(f"User {user_id} started appointment booking")
    
    # Сохраняем язык перед очисткой
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # ✅ ИСПОЛЬЗУЕМ clear_appointment_data вместо установки в None
    session_manager.clear_appointment_data(user_id)
    
    # Сохраняем username
    session_manager.set_value(user_id, 'username', message.from_user.username or f"User_{user_id}")
    
    # Восстанавливаем язык
    session_manager.set_value(user_id, 'language', lang)
    
    logger.info(f"User {user_id} started booking with language: {lang}")
    
    await message.answer(
        get_text(lang, 'select_doctor'),
        reply_markup=doctor_inline_keyboard(lang)
    )


@router.message(AppointmentStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    user_id = message.from_user.id
    text = message.text.strip()
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"📝 User {user_id} entered: {text}")
    
    # ✅ ПРОВЕРКА НА КНОПКУ "ВЕРНУТЬСЯ В МЕНЮ"
    back_to_menu_texts = [
        get_text('ru', 'btn_back_to_menu'),
        get_text('en', 'btn_back_to_menu'),
        get_text('zh', 'btn_back_to_menu')
    ]
    
    if text in back_to_menu_texts:
        logger.info(f"User {user_id} clicked back to menu from FSM state")
        await state.clear()
        session_manager.clear_appointment_data(user_id)
        await message.answer(
            get_text(lang, 'welcome'),
            reply_markup=main_reply_keyboard(lang)
        )
        return
    
    # ✅ ТЕПЕРЬ text — это имя (после проверки на кнопку)
    name = text
    
    # Валидация имени
    if not validate_name(name):
        logger.warning(f"Invalid name entered by user {user_id}: '{name}'")
        await message.answer(
            f"<b>{get_text(lang, 'error_title')}</b>\n\n"
            f"{get_text(lang, 'name_error')}\n\n"
            f"<i>Нажмите «🏠 Вернуться в главное меню», чтобы начать заново</i>",
            reply_markup=error_reply_keyboard(lang),
            parse_mode='HTML'
        )
        return
    
    # ✅ Сохраняем имя в state (теперь name определён!)
    await state.update_data(name=name)
    
    logger.info(f"User {user_id} entered valid name, waiting for phone")
    
    # Запрашиваем телефон
    await message.answer(
        f"{get_text(lang, 'enter_phone')}\n\n"
        f"<i>Или нажмите 📱 Отправить контакт</i>",
        parse_mode='HTML'
    )
    
    # Переключаем состояние
    await state.set_state(AppointmentStates.waiting_for_phone)
    
    # Показываем клавиатуру ввода телефона
    from keyboards.appointment import numeric_phone_inline_keyboard
    current = session_manager.get_value(user_id, 'phone_temp', "+7")
    await message.answer(
        f"📱 **Текущий номер:** `{current}`",
        reply_markup=numeric_phone_inline_keyboard(lang, current),
        parse_mode="Markdown"
    )


@router.message(AppointmentStates.waiting_for_phone, F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    """Обработка отправленного контакта"""
    user_id = message.from_user.id
    phone = message.contact.phone_number
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"User {user_id} sent contact: {phone}")
    
    # Форматируем телефон
    formatted_phone = format_phone_to_international(phone)
    
    # Завершаем запись
    from handlers.callbacks import complete_appointment_flow
    await complete_appointment_flow(formatted_phone, message, state, lang, user_id)


@router.message(AppointmentStates.waiting_for_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    """Обработка ввода телефона текстом"""
    user_id = message.from_user.id
    text = message.text.strip()
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"User {user_id} entered: {text}")
    
    # ✅ ПРОВЕРКА НА КНОПКУ "ВЕРНУТЬСЯ В МЕНЮ"
    back_to_menu_texts = [
        get_text('ru', 'btn_back_to_menu'),
        get_text('en', 'btn_back_to_menu'),
        get_text('zh', 'btn_back_to_menu')
    ]
    
    if text in back_to_menu_texts:
        logger.info(f"User {user_id} clicked back to menu from FSM state")
        await state.clear()
        session_manager.clear_appointment_data(user_id)
        await message.answer(
            get_text(lang, 'welcome'),
            reply_markup=main_reply_keyboard(lang)
        )
        return
    
    # Завершаем запись
    from handlers.callbacks import complete_appointment_flow
    await complete_appointment_flow(text, message, state, lang, user_id)


def format_phone_to_international(phone: str) -> str:
    """Форматирует телефон в международный формат"""
    # Удаляем всё кроме цифр и +
    digits = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Если нет +, добавляем
    if not digits.startswith('+'):
        digits = '+' + digits
    
    # Если начинается с +7 или +8, нормализуем
    if digits.startswith('+8') and len(digits) == 12:
        digits = '+7' + digits[2:]
    
    return digits