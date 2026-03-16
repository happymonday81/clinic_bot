from pydantic import BaseModel, Field, validator
from typing import Optional
import re


class AppointmentCreateDTO(BaseModel):
    """DTO для создания записи"""
    doctor: str = Field(..., min_length=2, description="Врач (RU название)")
    doctor_display: Optional[str] = Field(None, description="Отображаемое имя врача")
    date: str = Field(..., description="Дата в формате YYYY-MM-DD")
    date_display: Optional[str] = Field(None, description="Дата для отображения (DD.MM)")
    time: str = Field(..., description="Время в формате HH:MM")
    phone: str = Field(..., min_length=10, description="Телефон")
    full_name: str = Field(..., min_length=2, max_length=100, description="ФИО пациента")
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('phone')
    def validate_phone(cls, v):
        """Валидация и нормализация телефона"""
        if not v:
            raise ValueError("Phone is required")
        
        # Удаляем все нецифровые символы кроме +
        cleaned = re.sub(r'[^\d+]', '', v)
        
        # Удаляем все кроме цифр для проверки длины
        digits = re.sub(r'\D', '', cleaned)
        
        if len(digits) < 10:
            raise ValueError(f"Phone too short: {len(digits)} digits, minimum 10")
        
        if len(digits) > 15:
            raise ValueError(f"Phone too long: {len(digits)} digits, maximum 15")
        
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
        
        return f"+{digits}"
    
    @validator('date')
    def validate_date(cls, v):
        """Проверка формата даты YYYY-MM-DD"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        return v
    
    @validator('time')
    def validate_time(cls, v):
        """Проверка формата времени HH:MM"""
        if not re.match(r'^\d{2}:\d{2}$', v):
            raise ValueError(f"Invalid time format: {v}. Expected HH:MM")
        
        hours, minutes = map(int, v.split(':'))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError(f"Invalid time: {v}")
        
        return v
    
    @validator('full_name')
    def validate_name(cls, v):
        """Проверка имени"""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if not re.match(r'^[\w\s\-\']+$', v, re.UNICODE):
            raise ValueError("Name contains invalid characters")
        return v


class AppointmentResult(BaseModel):
    """Результат операции создания записи"""
    success: bool
    appointment_id: Optional[int] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None  # "conflict", "validation", "database"
    
    @classmethod
    def success_result(cls, appointment_id: int):
        return cls(success=True, appointment_id=appointment_id)
    
    @classmethod
    def conflict(cls, message: str = "Time slot unavailable"):
        return cls(
            success=False,
            error_message=message,
            error_code="conflict"
        )
    
    @classmethod
    def validation_error(cls, message: str):
        return cls(
            success=False,
            error_message=message,
            error_code="validation"
        )
    
    @classmethod
    def database_error(cls, message: str):
        return cls(
            success=False,
            error_message=message,
            error_code="database"
        )
    
    @property
    def is_conflict(self) -> bool:
        return self.error_code == "conflict"
    
    @property
    def is_success(self) -> bool:
        return self.success