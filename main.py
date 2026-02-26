import os
import sys
import asyncio
import re
import calendar
import tempfile
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from dotenv import load_dotenv
from db import save_appointment, get_user_appointments, get_all_appointments
from openpyxl import Workbook
from locales import get_text

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [988615428]  # ⚠️ ЗАМЕНИТЕ НА СВОЙ TELEGRAM ID

# ========== Файл-блокировка для предотвращения двойного запуска ==========
LOCK_FILE = os.path.join(tempfile.gettempdir(), f"bot_{BOT_TOKEN[-10:] if BOT_TOKEN else 'unknown'}.lock")

def is_already_running():
    """Проверяет, не запущен ли уже бот"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = f.read()
            # Проверяем, существует ли процесс с таким PID
            os.kill(int(pid), 0)
            return True
        except (ProcessLookupError, ValueError, FileNotFoundError):
            # Процесс не существует или файл повреждён
            try:
                os.remove(LOCK_FILE)
            except:
                pass
            return False
    return False

def create_lock():
    """Создаёт файл-блокировку с текущим PID"""
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def remove_lock():
    """Удаляет файл-блокировку"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

# Проверяем при запуске
if is_already_running():
    print("❌ Бот уже запущен! Завершите другой экземпляр и попробуйте снова.")
    print(f"   Если уверены, что бот не запущен, удалите файл: {LOCK_FILE}")
    sys.exit(1)
create_lock()

# ========== Инициализация бота ==========
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== Хранилища ==========
user_languages = {}
user_data = {}

# ========== FSM States ==========
class AppointmentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

# ========== Клавиатуры ==========
def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")]
    ])

def main_reply_keyboard(lang='ru'):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_appointment')), 
             KeyboardButton(text=get_text(lang, 'btn_my_appointments'))],
            [KeyboardButton(text=get_text(lang, 'btn_about')), 
             KeyboardButton(text=get_text(lang, 'btn_contacts'))]
        ],
        resize_keyboard=True,
        input_field_placeholder="..."
    )

def doctor_inline_keyboard(lang='ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👨‍⚕️ {get_text(lang, 'therapist')}", callback_data="doctor:Терапевт")],
        [InlineKeyboardButton(text=f"🦷 {get_text(lang, 'dentist')}", callback_data="doctor:Стоматолог")],
        [InlineKeyboardButton(text=get_text(lang, 'btn_back_to_menu'), callback_data="back_to_menu")]
    ])

def time_inline_keyboard(lang='ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10:00", callback_data="time:10:00"), 
         InlineKeyboardButton(text="11:00", callback_data="time:11:00")],
        [InlineKeyboardButton(text="12:00", callback_data="time:12:00"), 
         InlineKeyboardButton(text="13:00", callback_data="time:13:00")],
        [InlineKeyboardButton(text="14:00", callback_data="time:14:00"), 
         InlineKeyboardButton(text="15:00", callback_data="time:15:00")],
        [InlineKeyboardButton(text="16:00", callback_data="time:16:00"), 
         InlineKeyboardButton(text="17:00", callback_data="time:17:00")],
        [InlineKeyboardButton(text="18:00", callback_data="time:18:00"), 
         InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="back_to_doctor")]
    ])

def phone_keyboard(lang='ru'):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_send_contact'), request_contact=True)],
            [KeyboardButton(text=get_text(lang, 'btn_back'))]
        ],
        resize_keyboard=True
    )

def create_calendar(lang='ru', year=None, month=None):
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
    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date_obj = datetime(year, month, day).date()
                today = now.date()
                if date_obj < today:
                    row.append(InlineKeyboardButton(text=f" {day} ", callback_data="ignore"))
                else:
                    date_str = date_obj.strftime("%d.%m.%Y")
                    if date_obj == today:
                        row.append(InlineKeyboardButton(text=f"✅{day}", callback_data=f"calendar_date:{date_str}"))
                    else:
                        row.append(InlineKeyboardButton(text=f"{day}", callback_data=f"calendar_date:{date_str}"))
        keyboard.append(row)

    # Навигация
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    keyboard.append([
        InlineKeyboardButton(text="◀️", callback_data=f"calendar:{prev_year}:{prev_month}"),
        InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="back_to_doctor"),
        InlineKeyboardButton(text="▶️", callback_data=f"calendar:{next_year}:{next_month}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    return bool(re.match(r'^\+?[\d]{10,15}$', cleaned))

# ========== Основные хэндлеры ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🌐 Please select your language / 请选择语言 / Выберите язык:",
        reply_markup=language_keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith('lang:'))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split(':')[1]
    user_id = callback.from_user.id
    user_languages[user_id] = lang
    await callback.message.delete()
    await callback.message.answer(
        get_text(lang, 'welcome'),
        reply_markup=main_reply_keyboard(lang)
    )
    await callback.answer()

# --- Админ-панель ---
@dp.message(lambda m: m.text == "/admin")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ У вас нет доступа к админ-панели")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Экспорт Excel", callback_data="admin_export_excel")]
    ])
    await message.answer("🛠 Админ-панель:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "admin_export_excel")
async def export_excel(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещён")
        return
    
    # Получаем путь к папке Загрузки
    downloads_path = str(Path.home() / "Downloads")
    
    appointments = get_all_appointments()
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "User ID", "Username", "Full Name", "Phone", "Doctor", "Date", "Time"])
    
    for apt in appointments:
        ws.append(list(apt))
    
    # Формируем имя файла на русском
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H.%M")
    filename = f"Записи через бот {date_str} {time_str}.xlsx"
    filepath = os.path.join(downloads_path, filename)
    
    wb.save(filepath)
    
    document = FSInputFile(filepath)
    await callback.message.answer_document(
        document,
        caption=f"📊 Выгрузка от {now.strftime('%d.%m.%Y %H:%M')}"
    )
    
    await callback.answer(f"✅ Файл сохранён в Загрузки")

# --- Кнопки главного меню ---
@dp.message(lambda message: message.text == get_text('ru', 'btn_appointment') or 
                            message.text == get_text('en', 'btn_appointment') or 
                            message.text == get_text('zh', 'btn_appointment'))
async def book_appointment(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    if user_id in user_data:
        del user_data[user_id]
    
    await message.answer(
        get_text(lang, 'select_doctor'),
        reply_markup=doctor_inline_keyboard(lang)
    )

@dp.message(lambda message: message.text == get_text('ru', 'btn_my_appointments') or 
                            message.text == get_text('en', 'btn_my_appointments') or 
                            message.text == get_text('zh', 'btn_my_appointments'))
async def my_appointments(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    appointments = get_user_appointments(user_id)
    
    if not appointments:
        await message.answer(get_text(lang, 'no_appointments'))
        return
    
    text_response = get_text(lang, 'my_appointments') + "\n\n"
    
    for apt in appointments:
        date_obj = datetime.strptime(apt[6], "%Y-%m-%d")
        date_display = date_obj.strftime("%d.%m.%Y")
        
        doctor_ru = apt[5]
        if doctor_ru == "Терапевт":
            doctor_display = get_text(lang, 'therapist')
        else:
            doctor_display = get_text(lang, 'dentist')
        
        text_response += f"🆔 #{apt[0]}\n"
        text_response += f"👤 {get_text(lang, 'patient')} {apt[3]}\n"
        text_response += f"📞 {get_text(lang, 'phone')} {apt[4]}\n"
        text_response += f"👨‍⚕️ {get_text(lang, 'doctor')} {doctor_display}\n"
        text_response += f"📅 {get_text(lang, 'date')} {date_display}\n"
        text_response += f"🕐 {get_text(lang, 'time')} {apt[7]}\n"
        text_response += "———————————————\n"
    
    await message.answer(text_response)

@dp.message(lambda message: message.text == get_text('ru', 'btn_about') or 
                            message.text == get_text('en', 'btn_about') or 
                            message.text == get_text('zh', 'btn_about'))
async def about_clinic(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    await message.answer(get_text(lang, 'about'))

@dp.message(lambda message: message.text == get_text('ru', 'btn_contacts') or 
                            message.text == get_text('en', 'btn_contacts') or 
                            message.text == get_text('zh', 'btn_contacts'))
async def contacts(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    await message.answer(get_text(lang, 'contacts'))

# --- Callback handlers ---
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    await state.clear()
    if user_id in user_data:
        del user_data[user_id]
    
    await callback.message.delete()
    await callback.message.answer(
        get_text(lang, 'welcome'),
        reply_markup=main_reply_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_doctor")
async def back_to_doctor(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    await state.clear()
    
    if user_id in user_data and "doctor" in user_data[user_id]:
        doctor_ru = user_data[user_id]["doctor"]
        user_data[user_id] = {"doctor": doctor_ru}
    
    await callback.message.edit_text(
        get_text(lang, 'select_doctor'),
        reply_markup=doctor_inline_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('doctor:'))
async def process_doctor(callback: types.CallbackQuery):
    doctor_ru = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    if doctor_ru == "Терапевт":
        doctor_display = get_text(lang, 'therapist')
    else:
        doctor_display = get_text(lang, 'dentist')
    
    user_data[user_id] = {
        "doctor": doctor_ru,
        "doctor_display": doctor_display
    }
    
    now = datetime.now()
    await callback.message.edit_text(
        get_text(lang, 'you_selected_doctor', doctor=doctor_display) + "\n\n" + get_text(lang, 'select_date'),
        reply_markup=create_calendar(lang, now.year, now.month)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('calendar:'))
async def process_calendar_navigation(callback: types.CallbackQuery):
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
async def process_calendar_date(callback: types.CallbackQuery, state: FSMContext):
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
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    time_str = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    if user_id not in user_data or "date" not in user_data[user_id]:
        await callback.message.edit_text("❌ Error. Start over: /start")
        await callback.answer()
        return
    
    user_data[user_id]["time"] = time_str
    
    await state.update_data(appointment_data=user_data[user_id])
    await state.set_state(AppointmentStates.waiting_for_name)
    
    await callback.message.edit_text(
        get_text(lang, 'you_selected_time', time=time_str) + "\n\n" + get_text(lang, 'enter_name')
    )
    await callback.answer()

# --- FSM handlers ---
@dp.message(AppointmentStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    name = message.text.strip()
    
    if not name:
        await message.answer(get_text(lang, 'name_error'))
        return
    
    await state.update_data(name=name)
    await state.set_state(AppointmentStates.waiting_for_phone)
    
    await message.answer(
        get_text(lang, 'enter_phone'),
        reply_markup=phone_keyboard(lang)
    )

@dp.message(AppointmentStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
    
    if not validate_phone(phone):
        await message.answer(get_text(lang, 'phone_error'))
        return
    
    data = await state.get_data()
    appointment_data = data.get('appointment_data', {})
    name = data.get('name')
    
    if not appointment_data and user_id in user_data:
        appointment_data = user_data[user_id]
    
    doctor = appointment_data.get('doctor')
    date = appointment_data.get('date')
    time_str = appointment_data.get('time')
    date_display = appointment_data.get('date_display', date)
    doctor_display = appointment_data.get('doctor_display', doctor)
    
    username = message.from_user.username or message.from_user.full_name or f"User_{user_id}"
    
    processing_msg = await message.answer(get_text(lang, 'saving'))
    
    appointment_id = save_appointment(
        user_id=user_id,
        username=username,
        full_name=name,
        phone=phone,
        doctor=doctor,
        date=date,
        time=time_str
    )
    
    if appointment_id:
        await processing_msg.delete()
        
        success_text = (
            get_text(lang, 'appointment_success') + "\n" +
            f"📋 ID: #{appointment_id}\n" +
            f"👤 {get_text(lang, 'patient')} {name}\n" +
            f"📞 {get_text(lang, 'phone')} {phone}\n" +
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
    
    await state.clear()
    if user_id in user_data:
        del user_data[user_id]

# --- Кнопка "Назад" ---
@dp.message(lambda message: message.text == get_text('ru', 'btn_back') or 
                            message.text == get_text('en', 'btn_back') or 
                            message.text == get_text('zh', 'btn_back'))
async def back_button(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    await state.clear()
    
    if user_id in user_data and "doctor" in user_data[user_id]:
        doctor_ru = user_data[user_id]["doctor"]
        user_data[user_id] = {"doctor": doctor_ru}
        await message.answer(
            get_text(lang, 'select_doctor'),
            reply_markup=doctor_inline_keyboard(lang)
        )
    else:
        await message.answer(
            get_text(lang, 'welcome'),
            reply_markup=main_reply_keyboard(lang)
        )

# --- Обработчик пустых кнопок ---
@dp.callback_query(lambda c: c.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    await callback.answer()

# --- Обработчик всех остальных сообщений ---
@dp.message()
async def handle_other_messages(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    
    # Если пользователь в процессе записи, игнорируем (обрабатывается FSM)
    if any([user_id in user_data, 
            await dp.fsm.get_state(bot, user_id, message.chat.id) is not None]):
        return
    
    # Показываем меню на любое сообщение
    await message.answer(
        get_text(lang, 'welcome'),
        reply_markup=main_reply_keyboard(lang)
    )

# ========== Запуск ==========
async def main():
    # Полная очистка перед запуском
    try:
        # Удаляем вебхук (на всякий случай)
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Вебхук очищен")
        
        # Получаем информацию о вебхуке для проверки
        webhook_info = await bot.get_webhook_info()
        print(f"ℹ️ Информация о вебхуке: {webhook_info.url if webhook_info.url else 'не установлен'}")
        
    except Exception as e:
        print(f"⚠️ Ошибка при очистке вебхука: {e}")
    
    print("🤖 Мультиязычный бот с админ-панелью запущен...")
    print(f"✅ Admin IDs: {ADMIN_IDS}")
    print("✅ Поддерживаемые языки: Русский, English, 中文")
    print("✅ Добавлен сбор имени и телефона")
    print("✅ Команда /admin для админ-панели")
    print(f"✅ Файл блокировки: {LOCK_FILE}")
    
    # Небольшая пауза для гарантии
    await asyncio.sleep(1)
    
    # Запускаем поллинг
    try:
        await dp.start_polling(bot)
    finally:
        # При выходе удаляем файл блокировки
        remove_lock()
        print("🛑 Бот остановлен, файл блокировки удалён")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем")
        remove_lock()
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        remove_lock()