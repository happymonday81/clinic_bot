import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Tuple

from models.appointment import AppointmentStatus

logger = logging.getLogger(__name__)

DB_PATH = "clinic.db"


@contextmanager
def get_db_connection():
    """Контекстный менеджер для безопасной работы с БД"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        yield conn
    finally:
        if conn:
            conn.close()


def init_db():
    """Инициализация БД с расширенной схемой"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Основная таблица записей
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            doctor TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        """)
        
        # Создаём индексы для ускорения поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON appointments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date_time ON appointments(date, time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date_time ON appointments(doctor, date, time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
        
        # Проверяем наличие колонок
        cursor.execute("PRAGMA table_info(appointments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем status если нет
        if 'status' not in columns:
            cursor.execute("ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT 'confirmed'")
            logger.info("✅ Added 'status' column")
        
        # Добавляем created_at если нет
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE appointments ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            logger.info("✅ Added 'created_at' column")
        
        # Добавляем notes если нет
        if 'notes' not in columns:
            cursor.execute("ALTER TABLE appointments ADD COLUMN notes TEXT")
            logger.info("✅ Added 'notes' column")
        
        conn.commit()
        logger.info("✅ Database initialized successfully")


# Инициализируем при загрузке модуля
init_db()


def is_time_slot_available(doctor: str, date: str, time: str) -> bool:
    """
    Проверяет, свободно ли время у врача
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM appointments 
                WHERE doctor = ? AND date = ? AND time = ? AND status IN ('confirmed', 'completed')
            """, (doctor, date, time))
            
            count = cursor.fetchone()[0]
            is_available = count == 0
            
            if not is_available:
                logger.warning(f"Time slot NOT available: {doctor} at {date} {time}")
            else:
                logger.debug(f"Time slot available: {doctor} at {date} {time}")
            
            return is_available
            
    except Exception as e:
        logger.error(f"Error checking time slot availability: {e}", exc_info=True)
        return False


def save_appointment(
    user_id: int,
    username: str,
    full_name: str,
    phone: str,
    doctor: str,
    date: str,
    time: str,
    status: str = AppointmentStatus.CONFIRMED.value,  # ✅ Теперь это строка 'confirmed'
    notes: str = "",
    max_retries: int = 5
) -> Optional[int]:
    """
    Сохраняет запись в БД с повторными попытками
    
    Returns:
        ID записи или None если ошибка
    """
    # ✅ Логгируем тип status для отладки
    logger.debug(f"Saving appointment: status={status!r}, type={type(status)}")
    
    if hasattr(status, 'value'):
        status = status.value  # Конвертируем Enum в строку
    status = str(status)  # Гарантируем строку
    logger.debug(f"Saving appointment: status={status!r}, type={type(status)}")
    
    for attempt in range(max_retries):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO appointments 
                    (user_id, username, full_name, phone, doctor, date, time, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username, full_name, phone, doctor, date, time, status, notes))
                
                conn.commit()
                appointment_id = cursor.lastrowid
                
                logger.info(
                    f"✅ Appointment saved: ID={appointment_id}, "
                    f"user={user_id}, doctor={doctor}, date={date} {time}"
                )
                
                return appointment_id
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                wait_time = 0.1 * (attempt + 1)
                logger.warning(
                    f"⚠️ Database locked, retry {attempt + 1}/{max_retries} in {wait_time}s..."
                )
                import time
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Database operational error: {e}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"❌ Error saving appointment: {e}", exc_info=True)
            return None
    
    return None


def get_user_appointments(user_id: int, status: str = None) -> List[Tuple]:
    """Получает записи пользователя"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            
            if status:
                cursor.execute("""
                    SELECT id, user_id, username, full_name, phone, 
                           doctor, date, time, status, created_at
                    FROM appointments WHERE user_id = ? AND status = ?
                    ORDER BY date, time
                """, (user_id, status))
            else:
                cursor.execute("""
                    SELECT id, user_id, username, full_name, phone, 
                           doctor, date, time, status, created_at
                    FROM appointments 
                    WHERE user_id = ? AND date >= ? AND status IN ('confirmed', 'completed')
                    ORDER BY date, time
                """, (user_id, today))
            
            return cursor.fetchall()
            
    except Exception as e:
        logger.error(f"❌ Error getting user appointments: {e}", exc_info=True)
        return []


def get_all_appointments(status: str = None, limit: int = None) -> List[Tuple]:
    """Получает все записи (для админа)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM appointments"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY date, time"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            return cursor.fetchall()
            
    except Exception as e:
        logger.error(f"❌ Error getting all appointments: {e}", exc_info=True)
        return []


def cancel_appointment(appointment_id: int, user_id: int = None) -> bool:
    """Отменяет запись"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    UPDATE appointments SET status = 'cancelled'
                    WHERE id = ? AND user_id = ? AND status = 'confirmed'
                """, (appointment_id, user_id))
            else:
                cursor.execute("""
                    UPDATE appointments SET status = 'cancelled'
                    WHERE id = ? AND status = 'confirmed'
                """, (appointment_id,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"✅ Appointment cancelled: ID={appointment_id}")
                return True
            else:
                logger.warning(f"⚠️ Appointment not found or already cancelled: ID={appointment_id}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error cancelling appointment: {e}", exc_info=True)
        return False


def get_appointment_by_id(appointment_id: int) -> Optional[Tuple]:
    """Получает запись по ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"❌ Error getting appointment by ID: {e}", exc_info=True)
        return None