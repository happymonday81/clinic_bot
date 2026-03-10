import re
import logging

logger = logging.getLogger(__name__)


def validate_name(name: str) -> bool:
    """
    Проверяет, что имя содержит только буквы (кириллица/латиница)
    
    Требования:
    - Только буквы (а-я, A-Z, включая ёЁ)
    - Минимум 2 символа
    - Максимум 50 символов
    - Пробелы разрешены (для фамилии)
    - Дефис разрешён (для двойных имён)
    
    Args:
        name: Имя для проверки
    
    Returns:
        True если валидно, False если нет
    """
    if not name:
        return False
    
    # Удаляем ведущие/конечные пробелы
    name = name.strip()
    
    # Проверяем длину
    if len(name) < 2 or len(name) > 50:
        return False
    
    # Проверяем, что содержит только буквы, пробелы и дефис
    # \u0400-\u04FF — кириллица, A-Za-z — латиница
    pattern = r'^[\u0400-\u04FFA-Za-z\s\-]+$'
    
    if not re.match(pattern, name):
        return False
    
    # Проверяем, что есть хотя бы одна буква (не только пробелы/дефисы)
    if not re.search(r'[\u0400-\u04FFA-Za-z]', name):
        return False
    
    return True


def validate_phone(phone: str) -> tuple:
    """
    Проверяет формат телефона
    
    Требования:
    - Должен начинаться с +
    - После + только цифры
    - Минимум 11 цифр (для +7XXXXXXXXXX)
    - Максимум 15 цифр
    
    Args:
        phone: Телефон для проверки
    
    Returns:
        (True, '') если валидно
        (False, 'сообщение об ошибке') если нет
    """
    if not phone:
        return False, "Телефон не может быть пустым"
    
    # Удаляем пробелы
    phone = phone.strip()
    
    # Должен начинаться с +
    if not phone.startswith('+'):
        return False, "Телефон должен начинаться с +"
    
    # После + только цифры
    digits = phone[1:]
    if not digits.isdigit():
        return False, "После + должны быть только цифры"
    
    # Проверяем длину (11-15 цифр)
    if len(digits) < 11:
        return False, "Слишком короткий номер (минимум 11 цифр)"
    
    if len(digits) > 15:
        return False, "Слишком длинный номер (максимум 15 цифр)"
    
    return True, ""


def format_phone_to_international(phone: str) -> str:
    """
    Форматирует телефон в международный формат
    
    Args:
        phone: Телефон в любом формате
    
    Returns:
        Телефон в формате +7XXXXXXXXXX
    """
    # Удаляем всё кроме цифр и +
    digits = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Если нет +, добавляем
    if not digits.startswith('+'):
        digits = '+' + digits
    
    # Если начинается с +8 и длина 12, заменяем на +7
    if digits.startswith('+8') and len(digits) == 12:
        digits = '+7' + digits[2:]
    
    return digits