from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class AppointmentStatus(str, Enum):
    """Статусы записей"""
    CONFIRMED = "confirmed"      # Подтверждена (активна)
    CANCELLED = "cancelled"      # Отменена пользователем
    COMPLETED = "completed"      # Завершена (дата прошла)
    NO_SHOW = "no_show"          # Пациент не пришёл
    RESCHEDULED = "rescheduled"  # Перенесена

@dataclass
class Appointment:
    """Модель записи на приём"""
    id: Optional[int]
    user_id: int
    username: str
    full_name: str
    phone: str
    doctor: str
    date: str
    time: str
    status: str = AppointmentStatus.CONFIRMED
    created_at: Optional[datetime] = None
    notes: str = ""

@dataclass
class AppointmentData:
    """Временные данные для создания записи"""
    doctor: str
    doctor_display: str
    date: Optional[str] = None
    date_display: Optional[str] = None
    time: Optional[str] = None

class Doctor:
    """Константы врачей"""
    THERAPIST_RU = "Терапевт"
    DENTIST_RU = "Стоматолог"
    
    @classmethod
    def get_display_name(cls, doctor_ru: str, lang: str) -> str:
        """Получает отображаемое название врача по языку"""
        from locales import get_text
        if doctor_ru == cls.THERAPIST_RU:
            return get_text(lang, 'therapist')
        else:
            return get_text(lang, 'dentist')

# Временные слоты
TIME_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]