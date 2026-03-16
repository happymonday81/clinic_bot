from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from locales import get_text


def error_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Клавиатура для сообщений об ошибках
    Показывает кнопку возврата в главное меню
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_back_to_menu'))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def error_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Инлайн-клавиатура для ошибок (когда нужно edit_text)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'btn_back_to_menu'), callback_data="back_to_menu")]
    ])