from typing import Optional
from datetime import datetime
import logging

from models.appointment import AppointmentStatus
from models.dto import AppointmentCreateDTO, AppointmentResult
from db import save_appointment, is_time_slot_available
from storage.session_manager import UserSessionManager

logger = logging.getLogger(__name__)


class AppointmentService:
    """Сервис для управления записями"""
    
    def __init__(self, session_manager: UserSessionManager, db_repository=None):
        self.session_manager = session_manager
        self.db_repository = db_repository
        logger.info("AppointmentService initialized")
    
    async def create_appointment(self, user_id: int, data: AppointmentCreateDTO) -> AppointmentResult:
        """Создаёт запись на приём"""
        logger.info(f"Creating appointment for user {user_id}: {data}")
        
        try:
            # 1. Проверяем доступность слота
            is_available = await self._check_slot_availability(
                doctor=data.doctor,
                date=data.date,
                time=data.time
            )
            
            if not is_available:
                logger.warning(f"Time slot conflict: {data.doctor} at {data.date} {data.time}")
                return AppointmentResult.conflict(
                    "Это время уже занято. Пожалуйста, выберите другое"
                )
            
            # 2. Получаем username
            username = self.session_manager.get_value(user_id, 'username', f"User_{user_id}")
            
            # 3. Сохраняем в БД
            appointment_id = save_appointment(
                user_id=user_id,
                username=username,
                full_name=data.full_name,
                phone=data.phone,
                doctor=data.doctor,
                date=data.date,
                time=data.time,
                status=AppointmentStatus.CONFIRMED.value,
                notes=""
            )
            
            if appointment_id:
                logger.info(f"Appointment created successfully: ID={appointment_id}")
                
                # 4. Очищаем временные данные сессии (НО НЕ ЯЗЫК!)
                self.session_manager.clear_appointment_data(user_id)
                
                return AppointmentResult.success_result(appointment_id)
            else:
                logger.error(f"Failed to save appointment for user {user_id}")
                return AppointmentResult.database_error(
                    "Не удалось сохранить запись в базу данных"
                )
        
        except Exception as e:
            logger.exception(f"Unexpected error creating appointment: {e}")
            return AppointmentResult.database_error(f"Внутренняя ошибка: {str(e)}")
    
    async def _check_slot_availability(self, doctor: str, date: str, time: str) -> bool:
        """Проверяет, свободно ли время"""
        return is_time_slot_available(doctor, date, time)