import html
import logging

from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.appointment import (
    numeric_phone_inline_keyboard,
    specialty_inline_keyboard,
)
from keyboards.error import error_reply_keyboard
from keyboards.main_menu import main_reply_keyboard
from locales import get_text
from services.appointment_service import AppointmentService
from storage.session_manager import UserSessionManager
from utils.helpers import validate_name

logger = logging.getLogger(__name__)

router = Router()

# FSM States
class AppointmentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    confirmation = State()

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
    
    # 1. Сначала получаем язык ПОКА сессия еще целая
    current_lang = session_manager.get_value(user_id, 'language')
    
    # Если в сессии нет (None), пробуем угадать по тексту кнопки или ставим ru
    if not current_lang:
        # Логика fallback: если кнопка была английской, то en, иначе ru
        if message.text == get_text('en', 'btn_appointment'):
            current_lang = 'en'
        elif message.text == get_text('zh', 'btn_appointment'):
            current_lang = 'zh'
        else:
            current_lang = 'ru'
            
    logger.info(f"User {user_id} started booking. Detected lang: {current_lang}")
    
    # 2. Очищаем ТОЛЬКО данные записи (убедись, что clear_appointment_data НЕ трогает 'language')
    # Если твой менеджер удаляет ВСЁ, то нужно сохранять язык во временную переменную и восстанавливать
    session_manager.clear_appointment_data(user_id)
    
    # 3. Явно сохраняем язык обратно (на случай если очистка его стерла)
    session_manager.set_value(user_id, 'language', current_lang)
    session_manager.set_value(user_id, 'username', message.from_user.username or f"User_{user_id}")
    
    # 4. Используем сохраненный язык
    await message.answer(
        "🩺 <b>Выберите специализацию:</b>",
        reply_markup=specialty_inline_keyboard(current_lang),
        parse_mode=ParseMode.HTML
    )


@router.message(AppointmentStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    user_id = message.from_user.id
    text = message.text.strip()
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"📝 User {user_id} entered: {text}")
    
    # Проверка на кнопку "Вернуться в меню"
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
    
    name = text
    
    # Валидация имени
    if not validate_name(name):
        logger.warning(f"Invalid name entered by user {user_id}: {name}")
        await message.answer(
            f"{get_text(lang, 'error_title')}\n\n"
            f"{get_text(lang, 'name_error')}\n\n"
            f"<i>Нажмите «🏠 Вернуться в главное меню», чтобы начать заново</i>",
            reply_markup=error_reply_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Сохраняем имя в state
    await state.update_data(name=name)
    
    logger.info(f"User {user_id} entered valid name, waiting for phone")
    
    # Запрашиваем телефон
    # Добавим новый ключ 'or_send_contact' в locales.py (см. ниже) или используем готовый
    await message.answer(
        f"{get_text(lang, 'enter_phone')}\n\n"
        f"<i>{get_text(lang, 'or_send_contact_hint')}</i>",
        parse_mode=ParseMode.HTML
    )
    
    # Переключаем состояние
    await state.set_state(AppointmentStates.waiting_for_phone)
    
    # Показываем клавиатуру ввода телефона
    current = session_manager.get_value(user_id, 'phone_temp', "+7")
    
    # Формируем текст "Текущий номер" через локализацию
    current_number_text = get_text(lang, 'current_number_label')
    
    await message.answer(
        f"{current_number_text} <code>{html.escape(current)}</code>",
        reply_markup=numeric_phone_inline_keyboard(lang, current),
        parse_mode=ParseMode.HTML
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
    
    # 🎯 Переходим к шагу подтверждения
    from handlers.callbacks import show_confirmation_step
    await show_confirmation_step(formatted_phone, message, state, lang, user_id)


@router.message(AppointmentStates.waiting_for_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    """Обработка ввода телефона текстом"""
    user_id = message.from_user.id
    text = message.text.strip()
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"User {user_id} entered: {text}")
    
    # Проверка на кнопку "Вернуться в меню"
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
    
    # 🎯 Переходим к шагу подтверждения
    from handlers.callbacks import show_confirmation_step
    await show_confirmation_step(text, message, state, lang, user_id)


def format_phone_to_international(phone: str) -> str:
    """Форматирует телефон в международный формат"""
    # Удаляем всё кроме цифр и +
    digits = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Если нет +, добавляем
    if not digits.startswith('+'):
        digits = '+' + digits
    
    # Если начинается с +8, нормализуем к +7
    if digits.startswith('+8') and len(digits) == 12:
        digits = '+7' + digits[2:]
    
    return digits