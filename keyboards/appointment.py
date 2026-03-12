from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from datetime import datetime
import calendar
from locales import get_text
from config.doctors import (
    DOCTORS_CONFIG,
    get_specialty_name,
    get_doctors_by_specialty,
    get_doctor_by_key
)

def language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")]
    ])


def specialty_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Клавиатура выбора специализации.
    Первый шаг записи.
    """
    keyboard = []
    
    for specialty_key in DOCTORS_CONFIG.keys():
        specialty_name = get_specialty_name(specialty_key, lang)
        keyboard.append([
            InlineKeyboardButton(
                text=specialty_name, 
                callback_data=f"specialty:{specialty_key}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text(lang, 'btn_back_to_menu'), 
            callback_data="back_to_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def doctors_inline_keyboard(lang: str = 'ru', specialty_key: str = 'therapist') -> InlineKeyboardMarkup:
    """
    Клавиатура выбора врача внутри специализации.
    Автоматически подгружает врачей из config/doctors.py
    """
    doctors = get_doctors_by_specialty(specialty_key)
    
    keyboard = []
    for doctor in doctors:
        doctor_name = doctor['name'].get(lang, doctor['name']['ru'])
        callback_data = f"doctor:{specialty_key}:{doctor['key']}"
        keyboard.append([
            InlineKeyboardButton(text=doctor_name, callback_data=callback_data)
        ])
    
    # Кнопка "Назад к специализациям"
    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Другая специализация", 
            callback_data="back_to_specialty"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def time_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура выбора времени"""
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


def numeric_phone_inline_keyboard(lang: str = 'ru', current_number: str = "+7") -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с цифрами для ввода телефона"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=" 1 ", callback_data="phone:1"),
            InlineKeyboardButton(text=" 2 ", callback_data="phone:2"),
            InlineKeyboardButton(text=" 3 ", callback_data="phone:3")
        ],
        [
            InlineKeyboardButton(text=" 4 ", callback_data="phone:4"),
            InlineKeyboardButton(text=" 5 ", callback_data="phone:5"),
            InlineKeyboardButton(text=" 6 ", callback_data="phone:6")
        ],
        [
            InlineKeyboardButton(text=" 7 ", callback_data="phone:7"),
            InlineKeyboardButton(text=" 8 ", callback_data="phone:8"),
            InlineKeyboardButton(text=" 9 ", callback_data="phone:9")
        ],
        [
            InlineKeyboardButton(text=" + ", callback_data="phone:+"),
            InlineKeyboardButton(text=" 0 ", callback_data="phone:0"),
            InlineKeyboardButton(text=" ⌫ ", callback_data="phone:backspace")
        ],
        [
            InlineKeyboardButton(text="✅ Готово", callback_data="phone:done"),
            InlineKeyboardButton(text="📱 Отправить контакт", callback_data="phone:contact")
        ],
        [
            InlineKeyboardButton(text="       🔙 Назад          ", callback_data="back_to_doctor")
        ]
    ])


def create_calendar(lang: str = 'ru', year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """Создаёт календарь для выбора даты"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    keyboard = []
    month_names = get_text(lang, 'months')
    
    keyboard.append([InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="ignore")])
    
    week_days = get_text(lang, 'week_days')
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in week_days])

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


def confirmation_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Inline-клавиатура для подтверждения записи.
    Позволяет редактировать каждое поле отдельно.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Редактирование врача
        [InlineKeyboardButton(text="✏️ Изменить врача", callback_data="edit:doctor")],
        
        # Редактирование даты
        [InlineKeyboardButton(text="✏️ Изменить дату", callback_data="edit:date")],
        
        # Редактирование времени
        [InlineKeyboardButton(text="✏️ Изменить время", callback_data="edit:time")],
        
        # Имя и телефон в одну строку
        [
            InlineKeyboardButton(text="✏️ Имя", callback_data="edit:name"),
            InlineKeyboardButton(text="✏️ Телефон", callback_data="edit:phone")
        ],
        
        # Подтверждение (главное действие)
        [InlineKeyboardButton(text="✅ Подтвердить запись", callback_data="confirm:yes")],
        
        # Выход в меню (вместо "Отменить")
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="confirm:cancel")],
    ])
    
    return keyboard


def get_confirmation_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    УСТАРЕВШАЯ клавиатура (оставлена для совместимости).
    Теперь используем confirmation_inline_keyboard.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, подтверждаю")],
            [KeyboardButton(text="⬅️ Назад")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard