import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from db import save_appointment, get_user_appointments
from datetime import datetime
import calendar
import asyncio

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Временное хранилище данных пользователей
user_data = {}


def main_reply_keyboard():
    """Создаёт основную клавиатуру с кнопками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Записаться на приём"), KeyboardButton(text="📋 Мои записи")],
            [KeyboardButton(text="ℹ️ О клинике"), KeyboardButton(text="📞 Контакты")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard


def doctor_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍⚕️ Терапевт", callback_data="doctor:Терапевт")],
        [InlineKeyboardButton(text="🦷 Стоматолог", callback_data="doctor:Стоматолог")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")]
    ])
    return keyboard


def time_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10:00", callback_data="time:10:00"), InlineKeyboardButton(text="11:00", callback_data="time:11:00")],
        [InlineKeyboardButton(text="12:00", callback_data="time:12:00"), InlineKeyboardButton(text="13:00", callback_data="time:13:00")],
        [InlineKeyboardButton(text="14:00", callback_data="time:14:00"), InlineKeyboardButton(text="15:00", callback_data="time:15:00")],
        [InlineKeyboardButton(text="16:00", callback_data="time:16:00"), InlineKeyboardButton(text="17:00", callback_data="time:17:00")],
        [InlineKeyboardButton(text="18:00", callback_data="time:18:00"), InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_doctor")]
    ])
    return keyboard


def create_calendar(year=None, month=None):
    """Создаёт инлайн-клавиатуру с календарём"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    keyboard = []
    month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    
    # Заголовок
    keyboard.append([InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="ignore")])
    
    # Дни недели
    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
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
                        row.append(InlineKeyboardButton(text=f"✅{day}", callback_data=f"calendar_date:{date_str}"))
                    else:
                        row.append(InlineKeyboardButton(text=f"{day}", callback_data=f"calendar_date:{date_str}"))
        keyboard.append(row)
    
    # Навигация
    nav_row = []
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"calendar:{prev_year}:{prev_month}"))
    
    nav_row.append(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_doctor"))
    
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"calendar:{next_year}:{next_month}"))
    
    keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def validate_full_name(name: str) -> bool:
    """Проверяет имя и фамилию"""
    words = name.strip().split()
    return len(words) >= 2 and all(word.isalpha() for word in words)


@dp.message(CommandStart())
async def start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = (
        "🏥 **Вас приветствует бот записи к врачам в клинике CMD!**\n\n"
        "📌 **Что я умею:**\n"
        "• Записывать вас на приём к специалистам\n"
        "• Показывать ваши активные записи\n"
        "• Давать информацию о клинике\n\n"
        "👇 **Для записи нажмите кнопку «Записаться на приём»**\n"
        "📋 **Для просмотра своих записей нажмите «Мои записи»**"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=main_reply_keyboard(),
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == "📝 Записаться на приём")
async def book_appointment(message: types.Message):
    """Начинает процесс записи"""
    await message.answer(
        "👨‍⚕️ **Выберите специалиста:**",
        reply_markup=doctor_inline_keyboard(),
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == "📋 Мои записи")
async def my_appointments(message: types.Message):
    """Показывает записи пользователя"""
    user_id = message.from_user.id
    appointments = get_user_appointments(user_id)
    
    if not appointments:
        await message.answer(
            "📭 У вас пока нет активных записей.\n\n"
            "Хотите записаться? Нажмите кнопку «Записаться на приём»"
        )
        return
    
    text = "📋 Ваши актуальные записи:\n\n"
    
    for apt in appointments:
        date_obj = datetime.strptime(apt[5], "%Y-%m-%d")
        date_display = date_obj.strftime("%d.%m.%Y")
        
        text += f"🆔 #{apt[0]}\n"
        text += f"👤 {apt[3]}\n"
        text += f"👨‍⚕️ {apt[4]}\n"
        text += f"📅 {date_display} в {apt[6]}\n"
        text += "———————————————\n"
    
    await message.answer(text)


@dp.message(lambda message: message.text == "ℹ️ О клинике")
async def about_clinic(message: types.Message):
    """Информация о клинике"""
    about_text = (
        "🏥 **Клиника CMD**\n\n"
        "Мы заботимся о вашем здоровье уже более 10 лет!\n\n"
        "🕒 **Часы работы:**\n"
        "Пн-Пт: 8:00 - 20:00\n"
        "Сб: 9:00 - 18:00\n"
        "Вс: 9:00 - 16:00\n\n"
        "📍 **Адрес:**\n"
        "г. Москва, ул. Примерная, д. 123\n\n"
        "🌟 **Наши преимущества:**\n"
        "• Современное оборудование\n"
        "• Опытные специалисты\n"
        "• Комфортные условия"
    )
    await message.answer(about_text, parse_mode="Markdown")


@dp.message(lambda message: message.text == "📞 Контакты")
async def contacts(message: types.Message):
    """Контакты клиники"""
    contacts_text = (
        "📞 **Контакты клиники CMD**\n\n"
        "☎️ Телефон: +7 (495) 123-45-67\n"
        "📧 Email: info@cmd-clinic.ru\n"
        "🌐 Сайт: www.cmd-clinic.ru\n\n"
        "💬 **Мы в соцсетях:**\n"
        "📱 Telegram: @cmd_clinic\n"
        "📷 Instagram: @cmd_clinic\n\n"
        "🚑 **Экстренная помощь:** 103"
    )
    await message.answer(contacts_text, parse_mode="Markdown")


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await callback.message.delete()
    await callback.message.answer(
        "🏥 **Главное меню**\n\nВыберите действие:",
        reply_markup=main_reply_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_doctor")
async def back_to_doctor(callback: types.CallbackQuery):
    """Возврат к выбору врача"""
    user_id = callback.from_user.id
    if user_id in user_data and "doctor" in user_data[user_id]:
        user_data[user_id] = {"doctor": user_data[user_id]["doctor"]}
    
    await callback.message.edit_text(
        "👨‍⚕️ **Выберите специалиста:**",
        reply_markup=doctor_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('doctor:'))
async def process_doctor(callback: types.CallbackQuery):
    doctor = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    
    user_data[user_id] = {"doctor": doctor}
    
    now = datetime.now()
    await callback.message.edit_text(
        f"👨‍⚕️ **Вы выбрали врача:** {doctor}\n\n"
        f"📅 **Выберите дату визита:**",
        reply_markup=create_calendar(now.year, now.month),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('calendar:'))
async def process_calendar_navigation(callback: types.CallbackQuery):
    """Обработка навигации по календарю"""
    _, year, month = callback.data.split(':')
    year, month = int(year), int(month)
    
    await callback.message.edit_text(
        "📅 **Выберите дату визита:**",
        reply_markup=create_calendar(year, month),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('calendar_date:'))
async def process_calendar_date(callback: types.CallbackQuery):
    """Обработка выбора даты из календаря"""
    date_str = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    
    if user_id not in user_data or "doctor" not in user_data[user_id]:
        await callback.message.edit_text(
            "❌ **Что-то пошло не так.**\n"
            "Начните запись заново: /start"
        )
        await callback.answer()
        return
    
    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
    date_for_db = date_obj.strftime("%Y-%m-%d")
    date_display = date_obj.strftime("%d.%m")
    
    user_data[user_id]["date"] = date_for_db
    user_data[user_id]["date_display"] = date_display
    
    await callback.message.edit_text(
        f"📅 **Вы выбрали дату:** {date_display}\n\n"
        f"🕐 **Выберите удобное время:**",
        reply_markup=time_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('time:'))
async def process_time(callback: types.CallbackQuery):
    time_str = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id
    
    if user_id not in user_data or "date" not in user_data[user_id]:
        await callback.message.edit_text(
            "❌ **Что-то пошло не так.**\n"
            "Начните запись заново: /start"
        )
        await callback.answer()
        return
    
    user_data[user_id]["time"] = time_str
    
    await callback.message.edit_text(
        f"🕐 **Вы выбрали время:** {time_str}\n\n"
        f"📝 **Пожалуйста, введите ваши имя и фамилию:**\n"
        f"_(например: Иван Петров)_",
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Игнорируем нажатия на пустые кнопки"""
    await callback.answer()


@dp.message()
async def handle_message(message: types.Message):
    """Обработчик текстовых сообщений (для ввода имени/фамилии)"""
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_data:
        return

    if "time" in user_data[user_id] and "full_name" not in user_data[user_id]:
        if validate_full_name(text):
            user_data[user_id]["full_name"] = text
            
            doctor = user_data[user_id]['doctor']
            date = user_data[user_id]['date']
            time_str = user_data[user_id]['time']
            full_name = user_data[user_id]['full_name']
            date_display = user_data[user_id].get('date_display', date)
            
            username = message.from_user.username or message.from_user.full_name or f"User_{user_id}"
            
            processing_msg = await message.answer("⏳ **Сохраняем вашу запись...**")
            
            appointment_id = save_appointment(
                user_id=user_id,
                username=username,
                full_name=full_name,
                doctor=doctor,
                date=date,
                time=time_str
            )
            
            if appointment_id:
                await processing_msg.delete()
                
                confirm_text = (
                    "✅ **Запись успешно создана!**\n\n"
                    f"**Номер записи:** #{appointment_id}\n"
                    f"**Пациент:** {full_name}\n"
                    f"**Врач:** {doctor}\n"
                    f"**Дата:** {date_display}\n"
                    f"**Время:** {time_str}\n\n"
                    "💚 **Спасибо! Мы ждём вас в клинике CMD.**"
                )
                
                await message.answer(
                    confirm_text,
                    reply_markup=main_reply_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await processing_msg.edit_text(
                    "❌ **Произошла ошибка при сохранении записи.**"
                )
            
            del user_data[user_id]
            
        else:
            await message.answer(
                "❌ **Пожалуйста, введите имя и фамилию через пробел.**\n"
                "Например: Венцеслав Венгржановский"
            )


async def main():
    print("🤖 Бот запущен...")
    print("Команды:")
    print("/start - главное меню")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())