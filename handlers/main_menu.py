from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import logging

from locales import get_text
from keyboards.main_menu import main_reply_keyboard
from db import get_user_appointments
from datetime import datetime

logger = logging.getLogger(__name__)

router = Router()

# Глобальная переменная для инициализации
from storage.session_manager import UserSessionManager
session_manager: UserSessionManager = None


def init_main_menu(manager: UserSessionManager):
    """Инициализация модуля"""
    global session_manager
    session_manager = manager
    logger.info("Main menu handler initialized")


# ========== Кнопка "Мои записи" ==========
@router.message(F.text.in_([
    get_text('ru', 'btn_my_appointments'),
    get_text('en', 'btn_my_appointments'),
    get_text('zh', 'btn_my_appointments')
]))
async def my_appointments(message: types.Message):
    """Показывает записи пользователя"""
    user_id = message.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"📋 User {user_id} clicked: Мои записи")
    
    appointments = get_user_appointments(user_id)
    
    if not appointments:
        await message.answer(
            get_text(lang, 'no_appointments'),
            reply_markup=main_reply_keyboard(lang)
        )
        return
    
    text_response = get_text(lang, 'my_appointments') + "\n\n"
    
    for apt in appointments:
        try:
            date_obj = datetime.strptime(apt[6], "%Y-%m-%d")
            date_display = date_obj.strftime("%d.%m.%Y")
        except:
            date_display = apt[6]
        
        from models.appointment import Doctor
        doctor_display = Doctor.get_display_name(apt[5], lang)
        
        text_response += f"🆔 #{apt[0]}\n"
        text_response += f"👤 {get_text(lang, 'patient')} {apt[3]}\n"
        text_response += f"📞 {get_text(lang, 'phone')} {apt[4]}\n"
        text_response += f"👨‍️ {get_text(lang, 'doctor')} {doctor_display}\n"
        text_response += f"📅 {get_text(lang, 'date')} {date_display}\n"
        text_response += f"🕐 {get_text(lang, 'time')} {apt[7]}\n"
        text_response += "———————————————\n"
    
    await message.answer(text_response, reply_markup=main_reply_keyboard(lang))


# ========== Кнопка "О клинике" ==========
@router.message(F.text.in_([
    get_text('ru', 'btn_about'),
    get_text('en', 'btn_about'),
    get_text('zh', 'btn_about')
]))
async def about_clinic(message: types.Message):
    """Показывает информацию о клинике"""
    user_id = message.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"ℹ️ User {user_id} clicked: О клинике")
    
    await message.answer(
        get_text(lang, 'about'),
        reply_markup=main_reply_keyboard(lang)
    )


# ========== Кнопка "Контакты" ==========
@router.message(F.text.in_([
    get_text('ru', 'btn_contacts'),
    get_text('en', 'btn_contacts'),
    get_text('zh', 'btn_contacts')
]))
async def contacts(message: types.Message):
    """Показывает контакты клиники"""
    user_id = message.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"📞 User {user_id} clicked: Контакты")
    
    await message.answer(
        get_text(lang, 'contacts'),
        reply_markup=main_reply_keyboard(lang)
    )


# ========== Кнопка "Записаться" ==========
@router.message(F.text.in_([
    get_text('ru', 'btn_appointment'),
    get_text('en', 'btn_appointment'),
    get_text('zh', 'btn_appointment')
]))
async def book_appointment_menu(message: types.Message):
    """Начинает процесс записи"""
    user_id = message.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"📝 User {user_id} clicked: Записаться")
    
    from handlers.appointment import book_appointment
    await book_appointment(message)


# ========== Кнопка "Вернуться в меню" (из ошибки) ==========
@router.message(F.text.in_([
    get_text('ru', 'btn_back_to_menu'),
    get_text('en', 'btn_back_to_menu'),
    get_text('zh', 'btn_back_to_menu')
]))
async def back_to_menu_from_error(message: types.Message):
    """Возврат в меню из состояния ошибки"""
    user_id = message.from_user.id
    lang = session_manager.get_value(user_id, 'language', 'ru')
    
    logger.info(f"User {user_id} clicked: Back to menu from error")
    
    # Очищаем FSM state
    state = FSMContext(
        storage=message.bot.storage,
        key=(user_id, message.chat.id, message.from_user.id)
    )
    await state.clear()
    
    # ✅ Очищаем данные записи (но сохраняем язык!)
    session_manager.clear_appointment_data(user_id)
    
    await message.answer(
        get_text(lang, 'welcome'),
        reply_markup=main_reply_keyboard(lang)
    )