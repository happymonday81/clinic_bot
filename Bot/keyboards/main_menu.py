from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from locales import get_text


def language_keyboard():
    """Клавиатура выбора языка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh")]
    ])

def main_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Главное меню бота"""
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

def main_reply_keyboard(lang='ru'):
    """Основная клавиатура меню"""
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