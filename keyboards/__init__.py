# keyboards/__init__.py

from .main_menu import main_reply_keyboard
from .appointment import (
    specialty_inline_keyboard,
    doctors_inline_keyboard,
    time_inline_keyboard,
    numeric_phone_inline_keyboard,
    create_calendar,
    confirmation_inline_keyboard
)
from .error import error_reply_keyboard, error_inline_keyboard

__all__ = [
    'main_reply_keyboard',
    'specialty_inline_keyboard',
    'doctors_inline_keyboard',
    'time_inline_keyboard',
    'numeric_phone_inline_keyboard',
    'create_calendar',
    'confirmation_inline_keyboard',
    'error_reply_keyboard',
    'error_inline_keyboard'
]