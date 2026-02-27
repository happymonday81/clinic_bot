from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import logging

from locales import get_text
from keyboards.main_menu import main_reply_keyboard
from keyboards.appointment import (
    doctor_inline_keyboard,
    time_inline_keyboard,
    numeric_phone_inline_keyboard,
    create_calendar
)
from services.appointment_service import AppointmentService
from models.dto import AppointmentCreateDTO
from utils.helpers import validate_name, format_phone_to_international, validate_phone
from storage.session_manager import UserSessionManager

logger = logging.getLogger(__name__)

router = Router()

# FSM States
class AppointmentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

# Глобальные переменные для инициализации (будут заполнены в init_appointment)
appointment_service: AppointmentService = None
session_manager: UserSessionManager = None


def init_appointment(service: AppointmentService, manager: UserSessionManager):
    """
    Инициализация модуля с зависимостями
    
    Args:
        service: AppointmentService instance
        manager: UserSessionManager instance
    """
    global appointment_service, session_manager
    appointment_service = service
    session_manager = manager
    logger.info("Appointment handler initialized with dependencies")


# Константы для кнопок (чтобы не вызывать get_text при импорте)
APPOINTMENT_BUTTON_KEYS = ['btn_appointment']


@router.message(F.text.in_([
    get_text('ru', 'btn_appointment'), 
    get_text('en', 'btn_appointment'), 
    get_text('zh', 'btn_appointment')
]))
async def book_appointment(message: types.Message):
    """Начинает процесс записи"""
    user_id = message.from_user.id
    
    logger.info(f"User {user_id} started appointment booking")
    
    # ✅ СОХРАНЯЕМ ЯЗЫК ПЕРЕД ОЧИСТКОЙ
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Очищаем только данные записи, не язык
    session_manager.set_value(user_id, 'doctor', None)
    session_manager.set_value(user_id, 'doctor_display', None)
    session_manager.set_value(user_id, 'date', None)
    session_manager.set_value(user_id, 'date_display', None)
    session_manager.set_value(user_id, 'time', None)
    session_manager.set_value(user_id, 'phone_temp', None)
    session_manager.set_value(user_id, 'phone_message_id', None)
    
    # Сохраняем username для будущего использования
    session_manager.set_value(user_id, 'username', 
                             message.from_user.username or f"User_{user_id}")
    
    # ✅ ВОССТАНАВЛИВАЕМ ЯЗЫК (он мог быть затёрт)
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
    name = message.text.strip()
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"📝 User {user_id} entered name: {name}")  # ← Должен быть этот лог
    
    if not validate_name(name):
        await message.answer(get_text(lang, 'name_error'))
        return
    
    # Сохраняем имя в FSM state
    await state.update_data(name=name)
    await state.set_state(AppointmentStates.waiting_for_phone)
    
    # Инициализируем телефон в сессии
    session_manager.set_value(user_id, 'phone_temp', "+7")
    
    # Создаём инлайн-клавиатуру для ввода телефона
    keyboard = numeric_phone_inline_keyboard(lang, "+7")
    
    msg = await message.answer(
        f"{get_text(lang, 'enter_phone')}\n"
        f"📱 **Текущий номер:** `+7`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    # Сохраняем ID сообщения
    session_manager.set_value(user_id, 'phone_message_id', msg.message_id)
    
    logger.info(f"User {user_id} entered valid name, waiting for phone")


@router.message(lambda message: message.contact is not None)
async def handle_contact(message: types.Message, state: FSMContext):
    """Обработка отправки контакта"""
    user_id = message.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Проверяем, что мы в состоянии ожидания телефона
    current_state = await state.get_state()
    if current_state != AppointmentStates.waiting_for_phone:
        return
    
    phone = message.contact.phone_number
    logger.info(f"User {user_id} sent contact: {phone}")
    
    formatted_phone = format_phone_to_international(phone)
    await complete_appointment_flow(formatted_phone, message, state, lang, user_id)


async def complete_appointment_flow(
    phone: str,
    message: types.Message,
    state: FSMContext,
    lang: str,
    user_id: int
):
    """Завершает процесс записи"""
    # Валидация телефона
    is_valid, error_msg = validate_phone(phone)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Получаем данные из state и session
    state_data = await state.get_data()
    name = state_data.get('name')
    appointment_data = session_manager.get(user_id) or {}
    
    if not name or not appointment_data:
        logger.error(f"Missing data for user {user_id}")
        await message.answer("❌ Произошла ошибка. Начните сначала: /start")
        return
    
    # Создаём DTO
    try:
        dto = AppointmentCreateDTO(
            doctor=appointment_data.get('doctor'),
            doctor_display=appointment_data.get('doctor_display'),
            date=appointment_data.get('date'),
            date_display=appointment_data.get('date_display'),
            time=appointment_data.get('time'),
            phone=phone,
            full_name=name
        )
    except ValueError as e:
        logger.error(f"Validation error for user {user_id}: {e}")
        await message.answer(f"❌ Ошибка валидации: {str(e)}")
        return
    
    # Вызываем сервис
    result = await appointment_service.create_appointment(user_id, dto)
    
    # Обрабатываем результат
    if result.is_success:
        success_text = (
            f"{get_text(lang, 'appointment_success')}\n\n"
            f"📋 **ID:** #{result.appointment_id}\n"
            f"👤 **{get_text(lang, 'patient')}** {name}\n"
            f"📞 **{get_text(lang, 'phone')}** `{phone}`\n"
            f"👨‍️ **{get_text(lang, 'doctor')}** {dto.doctor_display or dto.doctor}\n"
            f"📅 **{get_text(lang, 'date')}** {dto.date_display or dto.date}\n"
            f"🕐 **{get_text(lang, 'time')}** {dto.time}\n\n"
            f"{get_text(lang, 'thanks')}"
        )
        
        await message.answer(
            success_text,
            reply_markup=main_reply_keyboard(lang),
            parse_mode="Markdown"
        )
        logger.info(f"Appointment created successfully for user {user_id}: ID={result.appointment_id}")
    
    elif result.is_conflict:
        await message.answer(
            f"❌ **Конфликт времени!**\n\n"
            f"{result.error_message}\n\n"
            f"Пожалуйста, выберите другое время.",
            reply_markup=main_reply_keyboard(lang),
            parse_mode="Markdown"
        )
        logger.warning(f"Time conflict for user {user_id}")
    
    else:
        await message.answer(
            f"❌ {get_text(lang, 'appointment_error')}\n"
            f"Детали: {result.error_message}",
            reply_markup=main_reply_keyboard(lang)
        )
        logger.error(f"Appointment creation failed for user {user_id}: {result.error_message}")
    
    # Очищаем state
    await state.clear()