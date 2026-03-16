import calendar
from datetime import datetime

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from locales import get_text
from models.doctors import (
    DOCTORS_CONFIG,
    get_doctors_by_specialty,
    get_specialty_name,
)


def language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка. Названия языков оставляем на родном языке."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")]
    ])


def specialty_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура выбора специализации."""
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
    """Клавиатура выбора врача внутри специализации."""
    doctors = get_doctors_by_specialty(specialty_key)
    
    keyboard = []
    for doctor in doctors:
        doctor_name = doctor['name'].get(lang, doctor['name']['ru'])
        callback_data = f"doctor:{specialty_key}:{doctor['key']}"
        keyboard.append([
            InlineKeyboardButton(text=doctor_name, callback_data=callback_data)
        ])
    
    # ИСПРАВЛЕНО: Используем локализацию для кнопки "Другая специализация"
    keyboard.append([
        InlineKeyboardButton(
            text=get_text(lang, 'btn_other_specialty'), 
            callback_data="back_to_specialty"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def time_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура выбора времени. Время (10:00) универсально, кнопка Назад локализована."""
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
    """Инлайн-клавиатура с цифрами для ввода телефона."""
    btn_done = get_text(lang, 'btn_done')
    btn_contact = get_text(lang, 'btn_send_contact')
    btn_back = get_text(lang, 'btn_back')

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
            InlineKeyboardButton(text=btn_done, callback_data="phone:done"),
            InlineKeyboardButton(text=btn_contact, callback_data="phone:contact")
        ],
        [
            InlineKeyboardButton(text=btn_back, callback_data="back_to_doctor")
        ]
    ])


def create_calendar(lang: str = 'ru', year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """Создаёт календарь для выбора даты."""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    keyboard = []
    month_names = get_text(lang, 'months')
    
    # Защита от IndexError, если в локализации нет месяцев
    if not month_names or len(month_names) < 12:
        month_str = f"{month}.{year}"
    else:
        month_str = f"{month_names[month-1]} {year}"

    keyboard.append([InlineKeyboardButton(text=month_str, callback_data="ignore")])
    
    week_days = get_text(lang, 'week_days')
    # Защита от отсутствия дней недели
    if not week_days or len(week_days) < 7:
        week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"] if lang == 'ru' else ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

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
    ИСПРАВЛЕНО: Все тексты теперь используют get_text().
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Редактирование врача
        [InlineKeyboardButton(text=get_text(lang, 'btn_edit_doctor'), callback_data="edit:doctor")],
        
        # Редактирование даты
        [InlineKeyboardButton(text=get_text(lang, 'btn_edit_date'), callback_data="edit:date")],
        
        # Редактирование времени
        [InlineKeyboardButton(text=get_text(lang, 'btn_edit_time'), callback_data="edit:time")],
        
        # Имя и телефон в одну строку
        [
            InlineKeyboardButton(text=get_text(lang, 'btn_edit_name'), callback_data="edit:name"),
            InlineKeyboardButton(text=get_text(lang, 'btn_edit_phone'), callback_data="edit:phone")
        ],
        
        # Подтверждение (главное действие)
        [InlineKeyboardButton(text=get_text(lang, 'btn_confirm_appointment'), callback_data="confirm:yes")],
        
        # Выход в меню
        [InlineKeyboardButton(text=get_text(lang, 'btn_main_menu'), callback_data="confirm:cancel")],
    ])
    
    return keyboard


def get_confirmation_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """УСТАРЕВШАЯ клавиатура (оставлена для совместимости)."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_yes_confirm'))],
            [KeyboardButton(text=get_text(lang, 'btn_back'))],
            [KeyboardButton(text=get_text(lang, 'btn_main_menu'))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard