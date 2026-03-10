from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest  # ✅ ДОБАВЛЕНО
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
from keyboards.error import error_reply_keyboard, error_inline_keyboard  # ✅ ДОБАВЛЕНО
from services.appointment_service import AppointmentService
from models.dto import AppointmentCreateDTO, AppointmentResult
from models.appointment import Doctor
from utils.helpers import validate_name, validate_phone
from storage.session_manager import UserSessionManager

logger = logging.getLogger(__name__)

router = Router()

# FSM States
from handlers.appointment import AppointmentStates

# Глобальные переменные для инициализации
appointment_service: AppointmentService = None
session_manager: UserSessionManager = None


def init_callbacks(service: AppointmentService, manager: UserSessionManager):
    """Инициализация модуля с зависимостями"""
    global appointment_service, session_manager
    appointment_service = service
    session_manager = manager
    logger.info("Callbacks handler initialized with dependencies")


# ========== HELPER: Безопасный ответ на callback ==========
async def safe_callback_answer(callback: types.CallbackQuery, text: str = None, show_alert: bool = False):
    """Отвечает на callback, игнорируя истёкшие query"""
    try:
        await callback.answer(text=text, show_alert=show_alert)
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            logger.debug(f"⏰ Callback expired for user {callback.from_user.id}")
        else:
            logger.warning(f"Telegram error in callback.answer: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error in callback.answer: {e}")


# ========== Callback: Выбор языка ==========
@router.callback_query(F.data.startswith('lang:'))
async def set_language(callback: types.CallbackQuery):
    """Устанавливает язык пользователя"""
    try:
        lang = callback.data.split(':')[1]
        user_id = callback.from_user.id
        
        session_manager.set_value(user_id, 'language', lang)
        logger.info(f"User {user_id} selected language: {lang}")
        
        await callback.message.delete()
        await callback.message.answer(
            get_text(lang, 'welcome'),
            reply_markup=main_reply_keyboard(lang)
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning(f"⏰ Language selection expired for user {callback.from_user.id}")
            await callback.message.answer(
                f"<b>{get_text('ru', 'error_title')}</b>\n\n"
                f"{get_text('ru', 'session_expired')}",
                reply_markup=error_reply_keyboard('ru'),
                parse_mode='HTML'
            )
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in set_language: {e}")


# ========== Callback: Выбор врача ==========
@router.callback_query(F.data.startswith('doctor:'))
async def process_doctor(callback: types.CallbackQuery):
    """Обработка выбора врача"""
    try:
        doctor_ru = callback.data.split(':', 1)[1]
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        doctor_display = Doctor.get_display_name(doctor_ru, lang)
        
        session_manager.set_value(user_id, 'doctor', doctor_ru)
        session_manager.set_value(user_id, 'doctor_display', doctor_display)
        
        logger.info(f"User {user_id} selected doctor: {doctor_ru}")
        
        now = datetime.now()
        await callback.message.edit_text(
            get_text(lang, 'you_selected_doctor', doctor=doctor_display) + 
            "\n\n" + get_text(lang, 'select_date'),
            reply_markup=create_calendar(lang, now.year, now.month)
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.warning(f"⏰ Doctor selection expired for user {callback.from_user.id}")
            await callback.message.answer(
                f"<b>{get_text(lang, 'error_title')}</b>\n\n"
                f"{get_text(lang, 'session_expired')}",
                reply_markup=error_reply_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in process_doctor: {e}")


# ========== Callback: Навигация календаря ==========
@router.callback_query(F.data.startswith('calendar:'))
async def process_calendar_navigation(callback: types.CallbackQuery):
    """Переключение месяцев в календаре"""
    try:
        _, year, month = callback.data.split(':')
        year, month = int(year), int(month)
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        logger.debug(f"User {user_id} navigating calendar: {year}-{month}")
        
        await callback.message.edit_text(
            get_text(lang, 'select_date'),
            reply_markup=create_calendar(lang, year, month)
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.debug(f"⏰ Calendar navigation expired for user {callback.from_user.id}")
        else:
            logger.warning(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in calendar navigation: {e}")


# ========== Callback: Выбор даты ==========
@router.callback_query(F.data.startswith('calendar_date:'))
async def process_calendar_date(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    try:
        date_str = callback.data.split(':', 1)[1]
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        doctor = session_manager.get_value(user_id, 'doctor')
        if not doctor:
            await callback.message.edit_text("❌ Error. Start over: /start")
            await safe_callback_answer(callback)
            return
        
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        date_for_db = date_obj.strftime("%Y-%m-%d")
        date_display = date_obj.strftime("%d.%m")
        
        session_manager.set_value(user_id, 'date', date_for_db)
        session_manager.set_value(user_id, 'date_display', date_display)
        
        logger.info(f"User {user_id} selected date: {date_for_db}")
        
        await callback.message.edit_text(
            get_text(lang, 'you_selected_date', date=date_display) + 
            "\n\n" + get_text(lang, 'select_time'),
            reply_markup=time_inline_keyboard(lang)
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.warning(f"⏰ Date selection expired for user {callback.from_user.id}")
            await callback.message.answer(
                f"<b>{get_text(lang, 'error_title')}</b>\n\n"
                f"{get_text(lang, 'session_expired')}",
                reply_markup=error_reply_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in process_calendar_date: {e}")


# ========== Callback: Выбор времени ==========
@router.callback_query(F.data.startswith('time:'))
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    try:
        time_str = callback.data.split(':', 1)[1]
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        date = session_manager.get_value(user_id, 'date')
        if not date:
            await callback.message.edit_text("❌ Error. Start over: /start")
            await safe_callback_answer(callback)
            return
        
        session_manager.set_value(user_id, 'time', time_str)
        
        logger.info(f"User {user_id} selected time: {time_str}")
        
        await state.set_state(AppointmentStates.waiting_for_name)
        
        await callback.message.edit_text(
            get_text(lang, 'you_selected_time', time=time_str) + 
            "\n\n" + get_text(lang, 'enter_name')
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.warning(f"⏰ Time selection expired for user {callback.from_user.id}")
            await callback.message.answer(
                f"<b>{get_text(lang, 'error_title')}</b>\n\n"
                f"{get_text(lang, 'session_expired')}",
                reply_markup=error_reply_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in process_time: {e}")


# ========== Callback: Ввод телефона ==========
@router.callback_query(F.data.startswith('phone:'))
async def process_phone_input(callback: types.CallbackQuery, state: FSMContext):
    """Обработка ввода телефона через инлайн-клавиатуру"""
    try:
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        action = callback.data.split(':')[1]
        
        # ✅ ПОЛУЧАЕМ ТЕКУЩИЙ НОМЕР (С ЗАЩИТОЙ ОТ NONE)
        current = session_manager.get_value(user_id, 'phone_temp', "+7")
        if current is None or current == "":
            current = "+7"
        
        logger.debug(f"Phone input: user={user_id}, current={current!r}, action={action}")
        
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
            await safe_callback_answer(callback)
            return
        
        # Обработка кнопки "Готово"
        elif action == "done":
            is_valid, error_msg = validate_phone(current)
            if is_valid:
                await complete_appointment_flow(current, callback.message, state, lang, user_id, callback)
            else:
                keyboard = numeric_phone_inline_keyboard(lang, current)
                await callback.message.edit_text(
                    f"<b>{get_text(lang, 'error_title')}</b>\n\n"
                    f"{error_msg}\n\n"
                    f"{get_text(lang, 'enter_phone')}\n"
                    f"📱 **Текущий номер:** `{current}`",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            await safe_callback_answer(callback)
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
            # ✅ ЗАЩИТА: преобразуем current в строку перед итерацией
            current_str = str(current) if current else "+7"
            digits = ''.join(c for c in current_str if c.isdigit())
            if len(digits) < 12:
                current = current_str + action
        
        # Сохраняем и обновляем
        session_manager.set_value(user_id, 'phone_temp', current)
        
        keyboard = numeric_phone_inline_keyboard(lang, current)
        await callback.message.edit_text(
            f"{get_text(lang, 'enter_phone')}\n"
            f"📱 **Текущий номер:** `{current}`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.warning(f"⏰ Phone input expired for user {callback.from_user.id}")
            await callback.message.answer(
                f"<b>{get_text(lang, 'error_title')}</b>\n\n"
                f"{get_text(lang, 'session_expired')}",
                reply_markup=error_reply_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in phone input: {e}")
        await callback.message.answer("❌ Произошла ошибка. Начните заново: /start")


# ========== Callback: Назад в меню ==========
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    try:
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        await state.clear()
        
        session_manager.set_value(user_id, 'doctor', None)
        session_manager.set_value(user_id, 'doctor_display', None)
        session_manager.set_value(user_id, 'date', None)
        session_manager.set_value(user_id, 'date_display', None)
        session_manager.set_value(user_id, 'time', None)
        session_manager.set_value(user_id, 'phone_temp', None)
        session_manager.set_value(user_id, 'phone_message_id', None)
        
        await callback.message.delete()
        await callback.message.answer(
            get_text(lang, 'welcome'),
            reply_markup=main_reply_keyboard(lang)
        )
        await safe_callback_answer(callback)
        
        logger.info(f"User {user_id} returned to menu with language: {lang}")
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.debug(f"⏰ Back to menu expired for user {callback.from_user.id}")
        else:
            logger.warning(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in back_to_menu: {e}")


# ========== Callback: Назад к врачу ==========
@router.callback_query(F.data == "back_to_doctor")
async def back_to_doctor(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору врача"""
    try:
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        await state.clear()
        
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
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.debug(f"⏰ Back to doctor expired for user {callback.from_user.id}")
        else:
            logger.warning(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in back_to_doctor: {e}")


# ========== Callback: Игнор ==========
@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Игнорирует нажатия на неактивные кнопки"""
    await safe_callback_answer(callback)


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
        await message.answer(
            f"<b>{get_text(lang, 'error_title')}</b>\n\n"
            f"{error_msg}\n\n"
            f"<i>Нажмите «🏠 Вернуться в главное меню», чтобы начать заново</i>",
            reply_markup=error_reply_keyboard(lang),
            parse_mode='HTML'
        )
        if callback:
            await safe_callback_answer(callback)
        return
    
    # Получаем данные из сессии
    session_data = session_manager.get(user_id)
    if not session_data:
        logger.error(f"No session data for user {user_id}")
        await message.answer(
            f"<b>{get_text(lang, 'error_title')}</b>\n\n"
            f"{get_text(lang, 'database_error')}",
            reply_markup=error_reply_keyboard(lang),
            parse_mode='HTML'
        )
        if callback:
            await safe_callback_answer(callback)
        return
    
    # Получаем имя из FSM state
    state_data = await state.get_data()
    name = state_data.get('name')
    
    if not name:
        logger.error(f"No name for user {user_id}")
        await message.answer(
            f"<b>{get_text(lang, 'error_title')}</b>\n\n"
            f"{get_text(lang, 'database_error')}",
            reply_markup=error_reply_keyboard(lang),
            parse_mode='HTML'
        )
        if callback:
            await safe_callback_answer(callback)
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
        await message.answer(
            f"<b>{get_text(lang, 'error_title')}</b>\n\n"
            f"❌ Ошибка валидации: {str(e)}",
            reply_markup=error_reply_keyboard(lang),
            parse_mode='HTML'
        )
        if callback:
            await safe_callback_answer(callback)
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
            f"<b>{get_text(lang, 'error_title')}</b>\n\n"
            f"❌ **Конфликт времени!**\n\n"
            f"{result.error_message}\n\n"
            f"Пожалуйста, выберите другое время.",
            reply_markup=error_reply_keyboard(lang),
            parse_mode="Markdown"
        )
        logger.warning(f"Time conflict for user {user_id}")
    
    else:
        await message.answer(
            f"<b>{get_text(lang, 'error_title')}</b>\n\n"
            f"{result.error_message or get_text(lang, 'database_error')}\n\n"
            f"<i>Нажмите «🏠 Вернуться в главное меню», чтобы начать заново</i>",
            reply_markup=error_reply_keyboard(lang),
            parse_mode='HTML'
        )
        logger.error(f"Appointment creation failed for user {user_id}: {result.error_message}")
    
    # Очищаем state
    await state.clear()
    
    # Если был callback, отвечаем на него
    if callback:
        await safe_callback_answer(
            callback,
            text="✅ Запись создана!" if result.is_success else "❌ Ошибка"
        )