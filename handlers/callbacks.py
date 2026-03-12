import html
from aiogram.enums import ParseMode
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import logging

from locales import get_text
from keyboards.main_menu import main_reply_keyboard
from keyboards.appointment import (
    time_inline_keyboard,
    numeric_phone_inline_keyboard,
    create_calendar,
    confirmation_inline_keyboard,
    specialty_inline_keyboard,
    doctors_inline_keyboard
)
from config.doctors import (
    DOCTORS_CONFIG,
    get_specialty_name,
    get_doctors_by_specialty,
    get_doctor_by_key
)
from keyboards.error import error_reply_keyboard
from services.appointment_service import AppointmentService
from models.dto import AppointmentCreateDTO, AppointmentResult
from models.appointment import Doctor
from utils.helpers import validate_name, validate_phone
from storage.session_manager import UserSessionManager
from handlers.appointment import AppointmentStates

logger = logging.getLogger(__name__)

router = Router()

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
                f"{get_text('ru', 'error_title')}\n\n"
                f"{get_text('ru', 'session_expired')}",
                reply_markup=error_reply_keyboard('ru'),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in set_language: {e}")


# ========== Callback: Выбор специализации ==========
@router.callback_query(F.data.startswith('specialty:'))
async def process_specialty(callback: types.CallbackQuery):
    """Пользователь выбрал специализацию → показываем врачей"""
    try:
        specialty_key = callback.data.split(':', 1)[1]
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        # Проверяем, есть ли такая специализация
        if specialty_key not in DOCTORS_CONFIG:
            await safe_callback_answer(callback, "❌ Неверная специализация", show_alert=True)
            return
        
        # Сохраняем специализацию в сессии
        session_manager.set_value(user_id, 'specialty_key', specialty_key)
        session_manager.set_value(user_id, 'specialty_name', get_specialty_name(specialty_key, lang))
        
        logger.info(f"User {user_id} selected specialty: {specialty_key}")
        
        # Показываем врачей этой специализации
        specialty_name = get_specialty_name(specialty_key, lang)
        await callback.message.edit_text(
            f"🩺 <b>{specialty_name}</b>\n\n👨‍⚕️ Выберите врача:",
            reply_markup=doctors_inline_keyboard(lang, specialty_key),
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.warning(f"⏰ Specialty selection expired for user {callback.from_user.id}")
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in process_specialty: {e}")


# ========== Callback: Выбор конкретного врача ==========
@router.callback_query(F.data.startswith('doctor:'))
async def process_doctor(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал врача → переходим к дате"""
    try:
        # Парсим: doctor:therapist:ivanov_aa
        parts = callback.data.split(':')
        if len(parts) != 3:
            await safe_callback_answer(callback, "❌ Ошибка данных", show_alert=True)
            return
        
        specialty_key = parts[1]
        doctor_key = parts[2]
        
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        # Получаем данные врача из конфига
        doctor = get_doctor_by_key(specialty_key, doctor_key)
        if not doctor:
            await safe_callback_answer(callback, "❌ Врач не найден", show_alert=True)
            return
        
        doctor_name = doctor['name'].get(lang, doctor['name']['ru'])
        specialty_name = get_specialty_name(specialty_key, lang)
        
        # Сохраняем данные врача
        session_manager.set_value(user_id, 'doctor_key', doctor_key)
        session_manager.set_value(user_id, 'doctor_display', doctor_name)
        session_manager.set_value(user_id, 'doctor', specialty_name)
        session_manager.set_value(user_id, 'specialty_key', specialty_key)
        
        logger.info(f"User {user_id} selected doctor: {doctor_name} ({specialty_name})")
        
        # Переходим к выбору даты
        await state.set_state(AppointmentStates.waiting_for_name)
        
        now = datetime.now()
        await callback.message.edit_text(
            f"✅ <b>Врач:</b> {doctor_name}\n"
            f"🩺 <b>Специализация:</b> {specialty_name}\n\n"
            f"{get_text(lang, 'select_date')}",
            reply_markup=create_calendar(lang, now.year, now.month),
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.warning(f"⏰ Doctor selection expired for user {callback.from_user.id}")
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in process_doctor: {e}")


# ========== Callback: Назад к специализациям ==========
@router.callback_query(F.data == "back_to_specialty")
async def back_to_specialty(callback: types.CallbackQuery):
    """Возврат к выбору специализации"""
    try:
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        # Очищаем выбор врача
        session_manager.set_value(user_id, 'doctor_key', None)
        session_manager.set_value(user_id, 'doctor_display', None)
        
        await callback.message.edit_text(
            "🩺 <b>Выберите специализацию:</b>",
            reply_markup=specialty_inline_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.debug(f"⏰ Back to specialty expired")
        else:
            logger.warning(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in back_to_specialty: {e}")


# ========== Callback: Назад к выбору специализации (обновлённый) ==========
@router.callback_query(F.data == "back_to_doctor")
async def back_to_doctor(callback: types.CallbackQuery, state: FSMContext):
    """
    Возврат к выбору специализации (новая логика).
    Используем этот же callback_data для совместимости со старыми клавиатурами.
    """
    try:
        user_id = callback.from_user.id
        lang = session_manager.get_value(user_id, 'language', 'ru')
        
        # Очищаем данные врача и даты
        session_manager.set_value(user_id, 'doctor_key', None)
        session_manager.set_value(user_id, 'doctor_display', None)
        session_manager.set_value(user_id, 'date', None)
        session_manager.set_value(user_id, 'time', None)
        
        await callback.message.edit_text(
            "🩺 <b>Выберите специализацию:</b>",
            reply_markup=specialty_inline_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.debug(f"⏰ Back to doctor expired")
        else:
            logger.warning(f"Telegram error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in back_to_doctor: {e}")


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
        
        # Проверяем, выбран ли врач (через doctor_key)
        doctor_key = session_manager.get_value(user_id, 'doctor_key')
        if not doctor_key:
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
                f"{get_text(lang, 'error_title')}\n\n"
                f"{get_text(lang, 'session_expired')}",
                reply_markup=error_reply_keyboard(lang),
                parse_mode=ParseMode.HTML
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
                f"{get_text(lang, 'error_title')}\n\n"
                f"{get_text(lang, 'session_expired')}",
                reply_markup=error_reply_keyboard(lang),
                parse_mode=ParseMode.HTML
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
        
        current = session_manager.get_value(user_id, 'phone_temp', "+7")
        if current is None or current == "":
            current = "+7"
        
        logger.debug(f"Phone input: user={user_id}, current={current!r}, action={action}")
        
        # Кнопка "Отправить контакт"
        if action == "contact":
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
        
        # Кнопка "Готово" → переходим к ПОДТВЕРЖДЕНИЮ
        elif action == "done":
            is_valid, error_msg = validate_phone(current)
            if is_valid:
                await show_confirmation_step(current, callback.message, state, lang, user_id)
            else:
                keyboard = numeric_phone_inline_keyboard(lang, current)
                await callback.message.edit_text(
                    f"{get_text(lang, 'error_title')}\n\n"
                    f"{error_msg}\n\n"
                    f"{get_text(lang, 'enter_phone')}\n"
                    f"📱 <b>Текущий номер:</b> <code>{html.escape(current)}</code>",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            await safe_callback_answer(callback)
            return
        
        # Backspace
        elif action == "backspace":
            if len(current) > 2:
                current = current[:-1]
            else:
                current = "+7"
        
        # Кнопка +
        elif action == "+":
            if "+" not in current:
                current = "+" + current.lstrip('+')
        
        # Цифры
        else:
            current_str = str(current) if current else "+7"
            digits = ''.join(c for c in current_str if c.isdigit())
            if len(digits) < 12:
                current = current_str + action
        
        session_manager.set_value(user_id, 'phone_temp', current)
        
        keyboard = numeric_phone_inline_keyboard(lang, current)
        await callback.message.edit_text(
            f"{get_text(lang, 'enter_phone')}\n"
            f"📱 <b>Текущий номер:</b> <code>{html.escape(current)}</code>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "message is not modified" in str(e):
            logger.warning(f"⏰ Phone input expired for user {callback.from_user.id}")
            await callback.message.answer(
                f"{get_text(lang, 'error_title')}\n\n"
                f"{get_text(lang, 'session_expired')}",
                reply_markup=error_reply_keyboard(lang),
                parse_mode=ParseMode.HTML
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
        session_manager.clear_appointment_data(user_id)
        
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


# ========== Callback: Игнор ==========
@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Игнорирует нажатия на неактивные кнопки"""
    await safe_callback_answer(callback)


# ============ 🎯 ФУНКЦИИ ПОДТВЕРЖДЕНИЯ ЗАПИСИ (INLINE) ============

async def show_confirmation_step(
    phone: str,
    message: types.Message,
    state: FSMContext,
    lang: str,
    user_id: int
):
    """Показывает полную сводку данных перед созданием записи"""
    
    # Собираем данные
    state_data = await state.get_data()
    session_data = session_manager.get(user_id) or {}
    
    specialty_name = session_data.get('specialty_name') or session_data.get('doctor', 'Не указана')
    doctor_name = session_data.get('doctor_display', 'Не указан')
    date = session_data.get('date_display') or session_data.get('date', 'Не указана')
    time = session_data.get('time', 'Не указано')
    name = state_data.get('name', 'Не указано')
    
    # 🔒 Экранируем все пользовательские данные для безопасности HTML
    safe_specialty = html.escape(str(specialty_name))
    safe_doctor = html.escape(str(doctor_name))
    safe_date = html.escape(str(date))
    safe_time = html.escape(str(time))
    safe_name = html.escape(str(name))  # ← ИСПРАВЛЕНО: добавлено экранирование имени
    safe_phone = html.escape(str(phone))
    
    # 📝 Формируем сообщение со ВСЕМИ 6 полями
    confirmation_text = f"""
📋 <b>Проверьте запись</b>

🩺 <b>Специализация:</b> {safe_specialty}
👨‍⚕️ <b>Врач:</b> {safe_doctor}
📅 <b>Дата:</b> {safe_date}
🕐 <b>Время:</b> {safe_time}
👤 <b>Имя:</b> {safe_name}
📞 <b>Телефон:</b> <code>{safe_phone}</code>
"""
    
    # Сохраняем данные в state
    await state.update_data(phone=phone, name=name)
    
    # Переходим в состояние подтверждения
    await state.set_state(AppointmentStates.confirmation)
    
    # Отправляем сообщение с INLINE-клавиатурой
    await message.answer(
        confirmation_text,
        reply_markup=confirmation_inline_keyboard(lang),
        parse_mode=ParseMode.HTML
    )
    
    logger.info(f"User {user_id} entered confirmation step with inline keyboard")


async def finalize_appointment_creation(
    message: types.Message,
    state: FSMContext,
    lang: str,
    user_id: int
):
    """Финальное создание записи в БД после подтверждения"""
    state_data = await state.get_data()
    session_data = session_manager.get(user_id) or {}
    
    phone = state_data.get('phone')
    name = state_data.get('name')
    
    if not phone or not name:
        logger.error(f"Missing data for appointment creation: user={user_id}")
        await message.answer(
            f"{get_text(lang, 'error_title')}\n\n"
            f"{get_text(lang, 'database_error')}",
            reply_markup=error_reply_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        return
    
    # 🔒 Экранируем данные
    safe_name = html.escape(str(name))
    safe_phone = html.escape(str(phone))
    
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
            f"{get_text(lang, 'error_title')}\n\n"
            f"❌ Ошибка валидации: {html.escape(str(e))}",
            reply_markup=error_reply_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Вызываем сервис
    result = await appointment_service.create_appointment(user_id, dto)
    
    # Обрабатываем результат
    if result.is_success:
        # 🔒 Экранируем все переменные
        safe_id = html.escape(str(result.appointment_id))
        safe_doctor = html.escape(str(dto.doctor_display or dto.doctor))
        safe_date = html.escape(str(dto.date_display or dto.date))
        safe_time = html.escape(str(dto.time))
        
        success_text = (
            f"{get_text(lang, 'appointment_success')}\n\n"
            f"📋 <b>ID:</b> #{safe_id}\n"
            f"👤 <b>{get_text(lang, 'patient')}:</b> {safe_name}\n"
            f"📞 <b>{get_text(lang, 'phone')}:</b> {safe_phone}\n"
            f"👨‍⚕️ <b>{get_text(lang, 'doctor')}:</b> {safe_doctor}\n"
            f"📅 <b>{get_text(lang, 'date')}:</b> {safe_date}\n"
            f"🕐 <b>{get_text(lang, 'time')}:</b> {safe_time}\n\n"
            f"{get_text(lang, 'thanks')}"
        )
        
        await message.answer(
            success_text,
            reply_markup=main_reply_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        logger.info(f"✅ Appointment created for user {user_id}: ID={result.appointment_id}")
        
    elif result.is_conflict:
        safe_error = html.escape(str(result.error_message)) if result.error_message else ""
        await message.answer(
            f"{get_text(lang, 'error_title')}\n\n"
            f"❌ <b>Конфликт времени!</b>\n\n"
            f"{safe_error}\n\n"
            f"Пожалуйста, выберите другое время.",
            reply_markup=error_reply_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        logger.warning(f"⚠️ Time conflict for user {user_id}")
        
    else:
        safe_error = html.escape(str(result.error_message)) if result.error_message else get_text(lang, 'database_error')
        await message.answer(
            f"{get_text(lang, 'error_title')}\n\n"
            f"{safe_error}\n\n"
            f"<i>Нажмите «🏠 Вернуться в главное меню», чтобы начать заново</i>",
            reply_markup=error_reply_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        logger.error(f"❌ Appointment failed for user {user_id}: {result.error_message}")
    
    # Очищаем состояние
    await state.clear()
    session_manager.clear_appointment_data(user_id)


# ============ ОБРАБОТЧИКИ INLINE-КНОПОК РЕДАКТИРОВАНИЯ ============

@router.callback_query(F.data == "edit:doctor")
async def edit_doctor(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование: показать врачей текущей специализации"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Получаем текущую специализацию
    specialty_key = session_manager.get_value(user_id, 'specialty_key')
    if not specialty_key:
        await callback.message.edit_text(
            "🩺 <b>Выберите специализацию:</b>",
            reply_markup=specialty_inline_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        return
    
    # Очищаем только врача
    session_manager.set_value(user_id, 'doctor_key', None)
    session_manager.set_value(user_id, 'doctor_display', None)
    
    # Показываем врачей этой специализации
    specialty_name = get_specialty_name(specialty_key, lang)
    await callback.message.edit_text(
        f"🩺 <b>{specialty_name}</b>\n\n👨‍⚕️ Выберите врача:",
        reply_markup=doctors_inline_keyboard(lang, specialty_key),
        parse_mode=ParseMode.HTML
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "edit:date")
async def edit_date(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование даты"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Очищаем дату
    session_manager.set_value(user_id, 'date', None)
    session_manager.set_value(user_id, 'date_display', None)
    
    # Проверяем, выбрана ли специализация
    specialty = session_manager.get_value(user_id, 'specialty_key')
    if not specialty:
        await callback.message.edit_text(
            "❌ Сначала выберите специализацию",
            reply_markup=specialty_inline_keyboard(lang),
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        return
    
    # Проверяем, выбран ли врач
    doctor_key = session_manager.get_value(user_id, 'doctor_key')
    if not doctor_key:
        await callback.message.edit_text(
            "❌ Сначала выберите врача",
            reply_markup=doctors_inline_keyboard(lang, specialty),
            parse_mode=ParseMode.HTML
        )
        await safe_callback_answer(callback)
        return
    
    # Показываем календарь
    now = datetime.now()
    await callback.message.edit_text(
        "📅 Выберите дату:",
        reply_markup=create_calendar(lang, now.year, now.month)
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "edit:time")
async def edit_time(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование времени"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Очищаем время
    session_manager.set_value(user_id, 'time', None)
    
    # Проверяем, выбрана ли дата
    date = session_manager.get_value(user_id, 'date')
    if not date:
        await callback.message.answer(
            "❌ Сначала выберите дату",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await safe_callback_answer(callback)
        return
    
    # Показываем выбор времени
    await callback.message.edit_text(
        "🕐 Выберите время:",
        reply_markup=time_inline_keyboard(lang)
    )
    await safe_callback_answer(callback)
    
    logger.info(f"User {user_id} editing time selection")


@router.callback_query(F.data == "edit:name")
async def edit_name(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование имени"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Удаляем старое имя из state
    data = await state.get_data()
    data.pop('name', None)
    await state.set_data(data)
    
    await callback.message.edit_text(
        "👤 Введите ваше имя (фамилия и имя):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await safe_callback_answer(callback)
    
    # Переходим в состояние ожидания имени
    await state.set_state(AppointmentStates.waiting_for_name)
    
    logger.info(f"User {user_id} editing name")


@router.callback_query(F.data == "edit:phone")
async def edit_phone(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование телефона"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    # Сбрасываем телефон
    session_manager.set_value(user_id, 'phone_temp', "+7")
    
    await callback.message.edit_text(
        "📞 Введите номер телефона:",
        reply_markup=numeric_phone_inline_keyboard(lang, "+7")
    )
    await safe_callback_answer(callback)
    
    # Переходим в состояние ожидания телефона
    await state.set_state(AppointmentStates.waiting_for_phone)
    
    logger.info(f"User {user_id} editing phone")


# ============ ОБРАБОТЧИКИ ПОДТВЕРЖДЕНИЯ И ОТМЕНЫ (INLINE) ============

@router.callback_query(F.data == "confirm:yes")
async def confirm_appointment_inline(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь подтвердил запись"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"User {user_id} confirmed appointment via inline button")
    
    # Показываем сообщение о подтверждении
    await callback.message.edit_text(
        "⏳ <b>Создаю запись...</b>",
        parse_mode=ParseMode.HTML
    )
    await safe_callback_answer(callback)
    
    # Создаём запись
    await finalize_appointment_creation(callback.message, state, lang, user_id)


@router.callback_query(F.data == "confirm:cancel")
async def cancel_appointment_inline(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь вышел в главное меню без подтверждения"""
    user_id = callback.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"User {user_id} cancelled appointment (returned to menu)")
    
    # Очищаем всё
    await state.clear()
    session_manager.clear_appointment_data(user_id)
    
    await callback.message.delete()
    await callback.message.answer(
        "⚠️ Запись не создана.\n\nВыберите действие:",
        reply_markup=main_reply_keyboard(lang)
    )
    await safe_callback_answer(callback)