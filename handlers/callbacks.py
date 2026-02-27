from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
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
from models.appointment import Doctor
from utils.helpers import validate_name, format_phone_to_international, validate_phone
from storage.session_manager import UserSessionManager

logger = logging.getLogger(__name__)

router = Router()

# FSM States (импортируем из appointment.py чтобы избежать дублирования)
from handlers.appointment import AppointmentStates

# Глобальные переменные для инициализации
appointment_service: AppointmentService = None
session_manager: UserSessionManager = None


def init_callbacks(service: AppointmentService, manager: UserSessionManager):
    """
    Инициализация модуля с зависимостями
    
    Args:
        service: AppointmentService instance
        manager: UserSessionManager instance
    """
    global appointment_service, session_manager
    appointment_service = service
    session_manager = manager
    logger.info("Callbacks handler initialized with dependencies")


# ========== Callback: Выбор языка ==========
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


# ========== Callback: Выбор врача ==========
@router.callback_query(F.data.startswith('doctor:'))
async def process_doctor(callback: types.CallbackQuery):
    """Обработка выбора врача"""
    doctor_ru = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Получаем отображаемое имя врача
    doctor_display = Doctor.get_display_name(doctor_ru, lang)
    
    # Сохраняем данные в сессию
    session_manager.set_value(user_id, 'doctor', doctor_ru)
    session_manager.set_value(user_id, 'doctor_display', doctor_display)
    
    logger.info(f"User {user_id} selected doctor: {doctor_ru}")
    
    now = datetime.now()
    await callback.message.edit_text(
        get_text(lang, 'you_selected_doctor', doctor=doctor_display) + 
        "\n\n" + get_text(lang, 'select_date'),
        reply_markup=create_calendar(lang, now.year, now.month)
    )
    await callback.answer()


# ========== Callback: Навигация календаря ==========
@router.callback_query(F.data.startswith('calendar:'))
async def process_calendar_navigation(callback: types.CallbackQuery):
    """Переключение месяцев в календаре"""
    _, year, month = callback.data.split(':')
    year, month = int(year), int(month)
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.debug(f"User {user_id} navigating calendar: {year}-{month}")
    
    await callback.message.edit_text(
        get_text(lang, 'select_date'),
        reply_markup=create_calendar(lang, year, month)
    )
    await callback.answer()


# ========== Callback: Выбор даты ==========
@router.callback_query(F.data.startswith('calendar_date:'))
async def process_calendar_date(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    date_str = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Проверяем, выбран ли врач
    doctor = session_manager.get_value(user_id, 'doctor')
    if not doctor:
        await callback.message.edit_text("❌ Error. Start over: /start")
        await callback.answer()
        return
    
    # Форматируем дату
    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
    date_for_db = date_obj.strftime("%Y-%m-%d")
    date_display = date_obj.strftime("%d.%m")
    
    # Сохраняем в сессию
    session_manager.set_value(user_id, 'date', date_for_db)
    session_manager.set_value(user_id, 'date_display', date_display)
    
    logger.info(f"User {user_id} selected date: {date_for_db}")
    
    await callback.message.edit_text(
        get_text(lang, 'you_selected_date', date=date_display) + 
        "\n\n" + get_text(lang, 'select_time'),
        reply_markup=time_inline_keyboard(lang)
    )
    await callback.answer()


# ========== Callback: Выбор времени ==========
@router.callback_query(F.data.startswith('time:'))
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time_str = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Проверяем, выбрана ли дата
    date = session_manager.get_value(user_id, 'date')
    if not date:
        await callback.message.edit_text("❌ Error. Start over: /start")
        await callback.answer()
        return
    
    # Сохраняем время в сессию
    session_manager.set_value(user_id, 'time', time_str)
    
    logger.info(f"User {user_id} selected time: {time_str}")
    
    # Переходим к вводу имени
    await state.set_state(AppointmentStates.waiting_for_name)
    
    await callback.message.edit_text(
        get_text(lang, 'you_selected_time', time=time_str) + 
        "\n\n" + get_text(lang, 'enter_name')
    )
    await callback.answer()


# ========== Callback: Ввод телефона ==========
@router.callback_query(F.data.startswith('phone:'))
async def process_phone_input(callback: types.CallbackQuery, state: FSMContext):
    """Обработка ввода телефона через инлайн-клавиатуру"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    action = callback.data.split(':')[1]
    
    # Получаем текущий номер
    current = session_manager.get_value(user_id, 'phone_temp', "+7")
    
    # Обработка кнопки "Отправить контакт"
    if action == "contact":
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        contact_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить контакт", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await callback.message.answer(
            "Нажмите кнопку ниже, чтобы отправить контакт:",
            reply_markup=contact_keyboard
        )
        await callback.answer()
        return
    
    # Обработка кнопки "Готово"
    elif action == "done":
        is_valid, error_msg = validate_phone(current)
        if is_valid:
            await complete_appointment_flow(current, callback.message, state, lang, user_id, callback)
        else:
            keyboard = numeric_phone_inline_keyboard(lang, current)
            await callback.message.edit_text(
                f"❌ {error_msg}\n\n"
                f"{get_text(lang, 'enter_phone')}\n"
                f"📱 **Текущий номер:** `{current}`",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer()
        return
    
    # Обработка backspace
    elif action == "backspace":
        if len(current) > 2:
            current = current[:-1]
        else:
            current = "+7"
    
    # Обработка +
    elif action == "+":
        if "+" not in current:
            current = "+" + current.lstrip('+')
    
    # Обработка цифр
    else:
        digits = ''.join(c for c in current if c.isdigit())
        if len(digits) < 12:
            current = current + action
    
    # Сохраняем и обновляем
    session_manager.set_value(user_id, 'phone_temp', current)
    
    keyboard = numeric_phone_inline_keyboard(lang, current)
    await callback.message.edit_text(
        f"{get_text(lang, 'enter_phone')}\n"
        f"📱 **Текущий номер:** `{current}`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Назад в меню ==========
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')  # ← Сохраняем язык
    
    await state.clear()
    
    # ✅ Очищаем данные записи, но сохраняем язык
    session_manager.set_value(user_id, 'doctor', None)
    session_manager.set_value(user_id, 'doctor_display', None)
    session_manager.set_value(user_id, 'date', None)
    session_manager.set_value(user_id, 'date_display', None)
    session_manager.set_value(user_id, 'time', None)
    session_manager.set_value(user_id, 'phone_temp', None)
    session_manager.set_value(user_id, 'phone_message_id', None)
    # ✅ Язык НЕ трогаем!
    
    await callback.message.delete()
    await callback.message.answer(
        get_text(lang, 'welcome'),
        reply_markup=main_reply_keyboard(lang)
    )
    await callback.answer()
    
    logger.info(f"User {user_id} returned to menu with language: {lang}")


# ========== Callback: Назад к врачу ==========
@router.callback_query(F.data == "back_to_doctor")
async def back_to_doctor(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору врача"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    await state.clear()
    
    # Очищаем данные о дате и времени, но сохраняем врача
    doctor = session_manager.get_value(user_id, 'doctor')
    doctor_display = session_manager.get_value(user_id, 'doctor_display')
    session_manager.delete(user_id)
    if doctor:
        session_manager.set_value(user_id, 'doctor', doctor)
        session_manager.set_value(user_id, 'doctor_display', doctor_display)
    
    await callback.message.edit_text(
        get_text(lang, 'select_doctor'),
        reply_markup=doctor_inline_keyboard(lang)
    )
    await callback.answer()


# ========== Callback: Игнор ==========
@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Игнорирует нажатия на неактивные кнопки"""
    await callback.answer()


# ========== Завершение записи (общая функция) ==========
async def complete_appointment_flow(
    phone: str,
    message: types.Message,
    state: FSMContext,
    lang: str,
    user_id: int,
    callback: types.CallbackQuery = None
):
    """Завершает процесс записи"""
    # Валидация телефона
    is_valid, error_msg = validate_phone(phone)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Получаем данные из сессии
    session_data = session_manager.get(user_id)
    if not session_data:
        logger.error(f"No session data for user {user_id}")
        await message.answer("❌ Произошла ошибка. Начните сначала: /start")
        return
    
    # Получаем имя из FSM state
    state_data = await state.get_data()
    name = state_data.get('name')
    
    if not name:
        logger.error(f"No name for user {user_id}")
        await message.answer("❌ Произошла ошибка. Начните сначала: /start")
        return
    
    # Создаём DTO
    try:
        dto = AppointmentCreateDTO(
            doctor=session_data.get('doctor'),
            doctor_display=session_data.get('doctor_display'),
            date=session_data.get('date'),
            date_display=session_data.get('date_display'),
            time=session_data.get('time'),
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
            f"👨‍⚕️ **{get_text(lang, 'doctor')}** {dto.doctor_display or dto.doctor}\n"
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
    
    # Если был callback, отвечаем на него
    if callback:
        await callback.answer("✅ Запись создана!" if result.is_success else "❌ Ошибка")