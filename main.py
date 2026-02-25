import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from db import save_appointment, get_user_appointments
from datetime import datetime
import calendar
import asyncio
from locales import get_text

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Хранилище языков пользователей
user_languages = {}

# Временное хранилище данных пользователей
user_data = {}


def language_keyboard():
    """Клавиатура выбора языка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")]
    ])
    return keyboard


def main_reply_keyboard(lang: str = 'ru'):
    """Создаёт основную клавиатуру с кнопками на выбранном языке"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_appointment')), 
             KeyboardButton(text=get_text(lang, 'btn_my_appointments'))],
            [KeyboardButton(text=get_text(lang, 'btn_about')), 
             KeyboardButton(text=get_text(lang, 'btn_contacts'))]
        ],
        resize_keyboard=True,
        input_field_placeholder="..."
    )
    return keyboard


def doctor_inline_keyboard(lang: str = 'ru'):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👨‍⚕️ {get_text(lang, 'therapist')}", callback_data="doctor:Терапевт")],
        [InlineKeyboardButton(text=f"🦷 {get_text(lang, 'dentist')}", callback_data="doctor:Стоматолог")],
        [InlineKeyboardButton(text=get_text(lang, 'btn_back_to_menu'), callback_data="back_to_menu")]
    ])
    return keyboard


def time_inline_keyboard(lang: str = 'ru'):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10:00", callback_data="time:10:00"), InlineKeyboardButton(text="11:00", callback_data="time:11:00")],
        [InlineKeyboardButton(text="12:00", callback_data="time:12:00"), InlineKeyboardButton(text="13:00", callback_data="time:13:00")],
        [InlineKeyboardButton(text="14:00", callback_data="time:14:00"), InlineKeyboardButton(text="15:00", callback_data="time:15:00")],
        [InlineKeyboardButton(text="16:00", callback_data="time:16:00"), InlineKeyboardButton(text="17:00", callback_data="time:17:00")],
        [InlineKeyboardButton(text="18:00", callback_data="time:18:00"), 
         InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="back_to_doctor")]
    ])
    return keyboard


def create_calendar(lang: str = 'ru', year=None, month=None):
    """Создаёт инлайн-клавиатуру с календарём на выбранном языке"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    keyboard = []
    month_names = get_text(lang, 'months')
    
    # Заголовок
    keyboard.append([InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="ignore")])
    
    # Дни недели
    week_days = get_text(lang, 'week_days')
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in week_days])
    
    # Календарь
    month_calendar = calendar.monthcalendar(year, month)
    today = now.date()
    
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date = datetime(year, month, day).date()
                if date < today:
                    row.append(InlineKeyboardButton(text=f" {day} ", callback_data="ignore"))
                else:
                    date_str = date.strftime("%d.%m.%Y")
                    if date == today:
                        # Сегодняшний день с отметкой
                        day_text = get_text(lang, 'today', day=day)
                        row.append(InlineKeyboardButton(text=day_text, callback_data=f"calendar_date:{date_str}"))
                    else:
                        row.append(InlineKeyboardButton(text=f"{day}", callback_data=f"calendar_date:{date_str}"))
        keyboard.append(row)
    
    # Навигация
    nav_row = []
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"calendar:{prev_year}:{prev_month}"))
    
    nav_row.append(InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="back_to_doctor"))
    
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"calendar:{next_year}:{next_month}"))
    
    keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def validate_full_name(name: str, lang: str = 'ru') -> bool:
    """
    Простая проверка - только что поле не пустое
    """
    return bool(name and len(name.strip()) >= 1)


@dp.message(CommandStart())
async def start(message: types.Message):
    """При старте сначала спрашиваем язык"""
    await message.answer(
        "🌐 Please select your language / 请选择语言 / Выберите язык:",
        reply_markup=language_keyboard()
    )


@dp.callback_query(lambda c: c.data.startswith('lang:'))
async def set_language(callback: types.CallbackQuery):
    """Устанавливает язык пользователя"""
    lang = callback.data.split(':')[1]
    user_id = callback.from_user.id
    
    # Сохраняем язык пользователя
    user_languages[user_id] = lang
    
    # Удаляем сообщение с выбором языка
    await callback.message.delete()
    
    # Показываем приветствие на выбранном языке
    welcome_text = get_text(lang, 'welcome')
    
    await callback.message.answer(
        welcome_text,
        reply_markup=main_reply_keyboard(lang)
    )
    await callback.answer()


@dp.message()
async def handle_all_messages(message: types.Message):
    """Обработчик всех сообщений"""
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    text = message.text.strip()

    # Проверяем, находится ли пользователь в процессе записи
    if user_id in user_data:
        if "time" in user_data[user_id] and "full_name" not in user_data[user_id]:
            # Ввод имени и фамилии
            if validate_full_name(text, lang):
                user_data[user_id]["full_name"] = text
                
                doctor = user_data[user_id]['doctor']  # русское название для БД
                date = user_data[user_id]['date']
                time_str = user_data[user_id]['time']
                full_name = user_data[user_id]['full_name']
                date_display = user_data[user_id].get('date_display', date)
                
                # Получаем отображаемое название врача
                doctor_display = user_data[user_id].get('doctor_display', doctor)
                
                username = message.from_user.username or message.from_user.full_name or f"User_{user_id}"
                
                processing_msg = await message.answer(get_text(lang, 'saving'))
                
                appointment_id = save_appointment(
                    user_id=user_id,
                    username=username,
                    full_name=full_name,
                    doctor=doctor,  # сохраняем русское название в БД
                    date=date,
                    time=time_str
                )
                
                if appointment_id:
                    await processing_msg.delete()
                    
                    # Формируем сообщение об успехе
                    success_text = (
                        get_text(lang, 'appointment_success') + "\n" +
                        f"📋 ID: #{appointment_id}\n" +
                        f"👤 {get_text(lang, 'patient')} {full_name}\n" +
                        f"👨‍⚕️ {get_text(lang, 'doctor')} {doctor_display}\n" +
                        f"📅 {get_text(lang, 'date')} {date_display}\n" +
                        f"🕐 {get_text(lang, 'time')} {time_str}\n\n" +
                        get_text(lang, 'thanks')
                    )
                    
                    await message.answer(
                        success_text,
                        reply_markup=main_reply_keyboard(lang)
                    )
                else:
                    await processing_msg.edit_text(get_text(lang, 'appointment_error'))
                
                del user_data[user_id]
            else:
                await message.answer(get_text(lang, 'name_error'))
            return
    
    # Если пользователь не в процессе записи, проверяем нажатие кнопок
    if text == get_text('ru', 'btn_appointment') or text == get_text('en', 'btn_appointment') or text == get_text('zh', 'btn_appointment'):
        # Кнопка записи
        if user_id in user_data:
            del user_data[user_id]
        
        await message.answer(
            get_text(lang, 'select_doctor'),
            reply_markup=doctor_inline_keyboard(lang)
        )
    
    elif text == get_text('ru', 'btn_my_appointments') or text == get_text('en', 'btn_my_appointments') or text == get_text('zh', 'btn_my_appointments'):
        # Кнопка "Мои записи"
        appointments = get_user_appointments(user_id)
        
        if not appointments:
            await message.answer(get_text(lang, 'no_appointments'))
            return
        
        text_response = get_text(lang, 'my_appointments') + "\n\n"
        
        for apt in appointments:
            date_obj = datetime.strptime(apt[5], "%Y-%m-%d")
            date_display = date_obj.strftime("%d.%m.%Y")
            
            # Преобразуем название врача на язык пользователя
            doctor_ru = apt[4]  # В БД хранится русское название
            if doctor_ru == "Терапевт":
                doctor_display = get_text(lang, 'therapist')
            else:
                doctor_display = get_text(lang, 'dentist')
            
            text_response += f"🆔 #{apt[0]}\n"
            text_response += f"👤 {get_text(lang, 'patient')} {apt[3]}\n"
            text_response += f"👨‍⚕️ {get_text(lang, 'doctor')} {doctor_display}\n"
            text_response += f"📅 {get_text(lang, 'date')} {date_display}\n"
            text_response += f"🕐 {get_text(lang, 'time')} {apt[6]}\n"
            text_response += "———————————————\n"
        
        await message.answer(text_response)
    
    elif text == get_text('ru', 'btn_about') or text == get_text('en', 'btn_about') or text == get_text('zh', 'btn_about'):
        # Кнопка "О клинике"
        await message.answer(
            get_text(lang, 'about')
        )
    
    elif text == get_text('ru', 'btn_contacts') or text == get_text('en', 'btn_contacts') or text == get_text('zh', 'btn_contacts'):
        # Кнопка "Контакты"
        await message.answer(
            get_text(lang, 'contacts')
        )
    
    else:
        # Если сообщение не распознано как кнопка
        await message.answer(
            get_text(lang, 'welcome'),
            reply_markup=main_reply_keyboard(lang)
        )


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    if user_id in user_data:
        del user_data[user_id]
    
    await callback.message.delete()
    await callback.message.answer(
        get_text(lang, 'welcome'),
        reply_markup=main_reply_keyboard(lang)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_doctor")
async def back_to_doctor(callback: types.CallbackQuery):
    """Возврат к выбору врача"""
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    if user_id in user_data and "doctor" in user_data[user_id]:
        # Сохраняем только врача, очищаем остальное
        doctor_ru = user_data[user_id]["doctor"]
        user_data[user_id] = {"doctor": doctor_ru}
    
    await callback.message.edit_text(
        get_text(lang, 'select_doctor'),
        reply_markup=doctor_inline_keyboard(lang)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('doctor:'))
async def process_doctor(callback: types.CallbackQuery):
    doctor_ru = callback.data.split(':', 1)[1]  # Терапевт или Стоматолог
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    # Сохраняем врача на языке пользователя
    if doctor_ru == "Терапевт":
        doctor_display = get_text(lang, 'therapist')
    else:
        doctor_display = get_text(lang, 'dentist')
    
    user_data[user_id] = {
        "doctor": doctor_ru,  # Сохраняем русское название для БД
        "doctor_display": doctor_display  # Сохраняем отображаемое название
    }
    
    now = datetime.now()
    await callback.message.edit_text(
        get_text(lang, 'you_selected_doctor', doctor=doctor_display) + "\n\n" + get_text(lang, 'select_date'),
        reply_markup=create_calendar(lang, now.year, now.month)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('calendar:'))
async def process_calendar_navigation(callback: types.CallbackQuery):
    """Обработка навигации по календарю"""
    _, year, month = callback.data.split(':')
    year, month = int(year), int(month)
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    await callback.message.edit_text(
        get_text(lang, 'select_date'),
        reply_markup=create_calendar(lang, year, month)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('calendar_date:'))
async def process_calendar_date(callback: types.CallbackQuery):
    """Обработка выбора даты из календаря"""
    date_str = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    if user_id not in user_data or "doctor" not in user_data[user_id]:
        await callback.message.edit_text("❌ Error. Start over: /start")
        await callback.answer()
        return
    
    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
    date_for_db = date_obj.strftime("%Y-%m-%d")
    date_display = date_obj.strftime("%d.%m")
    
    user_data[user_id]["date"] = date_for_db
    user_data[user_id]["date_display"] = date_display
    
    await callback.message.edit_text(
        get_text(lang, 'you_selected_date', date=date_display) + "\n\n" + get_text(lang, 'select_time'),
        reply_markup=time_inline_keyboard(lang)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('time:'))
async def process_time(callback: types.CallbackQuery):
    time_str = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    if user_id not in user_data or "date" not in user_data[user_id]:
        await callback.message.edit_text("❌ Error. Start over: /start")
        await callback.answer()
        return
    
    user_data[user_id]["time"] = time_str
    
    await callback.message.edit_text(
        get_text(lang, 'you_selected_time', time=time_str) + "\n\n" + get_text(lang, 'enter_name')
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Игнорируем нажатия на пустые кнопки"""
    await callback.answer()


async def main():
    print("🤖 Мультиязычный бот запущен...")
    print("Поддерживаемые языки: Русский, English, 中文")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())