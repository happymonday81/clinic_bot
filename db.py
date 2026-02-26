import sqlite3
from datetime import datetime

conn = sqlite3.connect("clinic.db", check_same_thread=False)
cursor = conn.cursor()

# Инициализация БД
def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        phone TEXT,
        doctor TEXT,
        date TEXT,
        time TEXT
    )
    """)
    conn.commit()

init_db()

def save_appointment(user_id, username, full_name, phone, doctor, date, time):
    try:
        cursor.execute(
            "INSERT INTO appointments (user_id, username, full_name, phone, doctor, date, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, phone, doctor, date, time)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при сохранении: {e}")
        return None

def get_user_appointments(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT id, user_id, username, full_name, phone, doctor, date, time FROM appointments WHERE user_id = ? AND date >= ? ORDER BY date, time",
        (user_id, today)
    )
    return cursor.fetchall()

def get_all_appointments():
    cursor.execute(
        "SELECT id, user_id, username, full_name, phone, doctor, date, time FROM appointments ORDER BY date, time"
    )
    return cursor.fetchall()

def close_connection():
    conn.close()
