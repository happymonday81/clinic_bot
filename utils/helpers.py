import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def validate_name(name: str, min_length: int = 2, max_length: int = 100) -> bool:
    """
    Валидирует имя пользователя
    
    Args:
        name: Имя для проверки
        min_length: Минимальная длина
        max_length: Максимальная длина
    
    Returns:
        True если имя валидно
    """
    if not name:
        return False
    
    name = name.strip()
    
    if len(name) < min_length or len(name) > max_length:
        return False
    
    # Разрешаем буквы, цифры, пробелы, дефисы и апострофы
    if not re.match(r'^[\w\s\-\']+$', name, re.UNICODE):
        return False
    
    return True


def format_phone_to_international(phone: str) -> str:
    """
    Приводит номер телефона к международному формату (+7...)
    
    Args:
        phone: Номер телефона в любом формате
    
    Returns:
        Номер в формате +7XXXXXXXXXX
    """
    if not phone:
        return ""
    
    # Удаляем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', phone)
    digits = re.sub(r'\D', '', cleaned)
    
    # Пустой номер
    if not digits:
        return "+7"
    
    # Российские номера
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    
    if len(digits) == 10:
        # Добавляем код страны +7
        return f"+7{digits}"
    
    if digits.startswith('7') and len(digits) == 11:
        return f"+{digits}"
    
    # Если уже с +, оставляем как есть
    if cleaned.startswith('+'):
        return cleaned
    
    # Для других стран просто добавляем +
    return f"+{digits}"


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    Валидирует номер телефона
    
    Args:
        phone: Номер для проверки
    
    Returns:
        (is_valid, error_message)
    """
    if not phone:
        return False, "Номер телефона не может быть пустым"
    
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) < 10:
        return False, f"Номер слишком короткий: {len(digits)} цифр (минимум 10)"
    
    if len(digits) > 15:
        return False, f"Номер слишком длинный: {len(digits)} цифр (максимум 15)"
    
    return True, ""


def sanitize_username(username: Optional[str], user_id: int) -> str:
    """
    Получает username или создаёт дефолтный
    
    Args:
        username: Username из Telegram (может быть None)
        user_id: Telegram user ID
    
    Returns:
        Безопасный username
    """
    if username:
        # Удаляем опасные символы
        sanitized = re.sub(r'[^\w\-]', '', username)
        return sanitized if sanitized else f"User_{user_id}"
    
    return f"User_{user_id}"


def format_date_for_display(date_str: str, lang: str = 'ru') -> str:
    """
    Форматирует дату из YYYY-MM-DD в DD.MM.YYYY
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        lang: Язык (пока не используется, для будущего)
    
    Returns:
        Дата в формате DD.MM.YYYY
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        logger.error(f"Invalid date format: {date_str}")
        return date_str


# Импортируем datetime здесь чтобы избежать circular import
from datetime import datetime