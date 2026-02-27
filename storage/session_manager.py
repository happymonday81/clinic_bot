from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading
import logging  # ✅ ДОБАВЛЕНО

logger = logging.getLogger(__name__)  # ✅ ДОБАВЛЕНО


class UserSessionManager:
    """
    Менеджер сессий пользователей с TTL (time-to-live)
    Заменяет глобальные словари user_data, user_languages и т.д.
    """
    
    def __init__(self, ttl_minutes: int = 30):
        self._data: Dict[int, Dict[str, Any]] = {}
        self._timestamps: Dict[int, datetime] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._lock = threading.Lock()
    
    def set(self, user_id: int, data: Dict[str, Any]):
        """Устанавливает данные для пользователя"""
        with self._lock:
            self._data[user_id] = data
            self._timestamps[user_id] = datetime.now()
    
    def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает данные для пользователя
        Автоматически удаляет просроченные сессии
        """
        with self._lock:
            if user_id not in self._timestamps:
                return None
            
            # Проверяем TTL
            if datetime.now() - self._timestamps[user_id] > self._ttl:
                self.delete(user_id)
                return None
            
            return self._data.get(user_id)
    
    def get_value(self, user_id: int, key: str, default: Any = None) -> Any:
        """Получает конкретное значение из сессии"""
        data = self.get(user_id)
        if data is None:
            return default
        return data.get(key, default)
    
    def set_value(self, user_id: int, key: str, value: Any):
        """Устанавливает конкретное значение в сессии"""
        data = self.get(user_id) or {}
        data[key] = value
        self.set(user_id, data)
    
    def delete(self, user_id: int):
        """Удаляет сессию пользователя"""
        with self._lock:
            self._data.pop(user_id, None)
            self._timestamps.pop(user_id, None)
    
    def clear_all(self):
        """Очищает все сессии"""
        with self._lock:
            self._data.clear()
            self._timestamps.clear()
    
    def cleanup_expired(self) -> int:
        """
        Очищает все просроченные сессии
        Возвращает количество удалённых
        """
        with self._lock:
            now = datetime.now()
            expired_users = [
                user_id for user_id, timestamp in self._timestamps.items()
                if now - timestamp > self._ttl
            ]
            
            for user_id in expired_users:
                self.delete(user_id)
            
            return len(expired_users)
    
    def clear_appointment_data(self, user_id: int):
        """ 
        Очищает данные записи, но сохраняет язык и другие настройки 
        """
        # ✅ ИСПРАВЛЕНО: отступ внутри метода
        with self._lock:
            data = self._data.get(user_id, {})
            
            # Удаляем только поля записи
            appointment_keys = [
                'doctor', 'doctor_display', 'date', 'date_display', 
                'time', 'phone_temp', 'phone_message_id', 'username'
            ]
            
            for key in appointment_keys:
                data.pop(key, None)
            
            # Обновляем данные и timestamp
            self._data[user_id] = data
            self._timestamps[user_id] = datetime.now()
            
            logger.debug(f"Cleared appointment data for user {user_id}, kept language")