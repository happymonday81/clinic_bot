import sqlite3
from datetime import datetime

conn = sqlite3.connect("clinic.db", check_same_thread=False)
cursor = conn.cursor()

# Инициализация БД
def init_db():
    # Создаём таблицу с базовой структурой
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        doctor TEXT,
        date TEXT,
        time TEXT
    )
    """)
    
    # Проверяем и добавляем колонку full_name, если её нет
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'full_name' not in columns:
        try:
            cursor.execute("ALTER TABLE appointments ADD COLUMN full_name TEXT")
            print("✅ Колонка full_name добавлена в таблицу")
        except:
            print("Колонка full_name уже существует")
    
    conn.commit()

# Инициализируем при загрузке
init_db()


def save_appointment(user_id, username, full_name, doctor, date, time):
    """Сохраняет запись в БД (дата в формате ГГГГ-ММ-ДД)"""
    try:
        cursor.execute(
            "INSERT INTO appointments (user_id, username, full_name, doctor, date, time) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, doctor, date, time)
        )
        conn.commit()
        print(f"✅ Запись сохранена: {full_name}, {doctor}, {date}, {time}")
        return cursor.lastrowid
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        conn.rollback()
        return None


def get_user_appointments(user_id):
    """
    Получает актуальные записи пользователя (дата >= сегодня)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute(
        "SELECT id, user_id, username, full_name, doctor, date, time FROM appointments WHERE user_id = ? AND date >= ? ORDER BY date, time",
        (user_id, today)
    )
    return cursor.fetchall()


def get_all_appointments():
    """Получает все записи"""
    cursor.execute("SELECT * FROM appointments ORDER BY date, time")
    return cursor.fetchall()


def close_connection():
    """Закрывает соединение с БД"""
    conn.close()