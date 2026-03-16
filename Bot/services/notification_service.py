import logging
from datetime import datetime, timedelta

from aiogram import Bot
from db import get_db_connection

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def check_and_send_reminders(self):
        """
        Основной метод проверки. Запускается каждую минуту.
        """
        now = datetime.now()
        # Целевые окна (±5 минут погрешности, чтобы не пропустить при перезапуске)
        target_24h_min = now + timedelta(hours=24, minutes=-5)
        target_24h_max = now + timedelta(hours=24, minutes=5)
        
        target_3h_min = now + timedelta(hours=3, minutes=-5)
        target_3h_max = now + timedelta(hours=3, minutes=5)

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем ВСЕ активные записи с новыми полями
                # Важно: порядок колонок должен совпадать с тем, что в SELECT
                cursor.execute("""
                    SELECT id, user_id, full_name, doctor, date, time, 
                           reminder_24h_sent, reminder_3h_sent
                    FROM appointments 
                    WHERE status = 'confirmed'
                """)
                
                rows = cursor.fetchall()

                for row in rows:
                    appt_id, user_id, full_name, doctor, date_str, time_str, sent_24, sent_3 = row
                    
                    # Парсим дату и время записи
                    try:
                        appt_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    except ValueError:
                        logger.error(f"Invalid date format for appointment {appt_id}: {date_str} {time_str}")
                        continue

                    # --- Проверка 24 часа ---
                    if not sent_24 and target_24h_min <= appt_datetime <= target_24h_max:
                        await self._send_reminder(conn, appt_id, user_id, full_name, doctor, appt_datetime, type='24h')
                    
                    # --- Проверка 3 часа ---
                    elif not sent_3 and target_3h_min <= appt_datetime <= target_3h_max:
                        await self._send_reminder(conn, appt_id, user_id, full_name, doctor, appt_datetime, type='3h')

        except Exception as e:
            logger.error(f"❌ Error in notification service loop: {e}", exc_info=True)

    async def _send_reminder(self, conn, appt_id: int, user_id: int, full_name: str, doctor: str, appt_datetime: datetime, type: str):
        """Отправляет сообщение и обновляет флаг в БД"""
        try:
            time_str = appt_datetime.strftime("%d.%m.%Y в %H:%M")
            
            if type == '24h':
                text = (
                    f"🔔 <b>Напоминание о записи</b>\n\n"
                    f"Здравствуйте, {full_name}!\n"
                    f"Напоминаем, что завтра ({time_str}) у вас прием к врачу ({doctor}).\n\n"
                    f"Пожалуйста, подтвердите присутствие или отмените запись, если планы изменились."
                )
                # Обновляем флаг 24ч
                cursor = conn.cursor()
                cursor.execute("UPDATE appointments SET reminder_24h_sent = 1 WHERE id = ?", (appt_id,))
                conn.commit()
                
            else: # 3h
                text = (
                    f"⏰ <b>Скоро прием!</b>\n\n"
                    f"{full_name}, ждем вас через 3 часа ({time_str}) к врачу {doctor}.\n"
                    f"Не опаздывайте!"
                )
                # Обновляем флаг 3ч
                cursor = conn.cursor()
                cursor.execute("UPDATE appointments SET reminder_3h_sent = 1 WHERE id = ?", (appt_id,))
                conn.commit()

            # Отправка в Telegram
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML"
                # Позже можно добавить кнопки "Подтвердить/Отменить" под этим сообщением
            )
            
            logger.info(f"✅ Reminder ({type}) sent to user {user_id} (Appt ID: {appt_id})")

        except Exception as e:
            logger.error(f"❌ Failed to send reminder to {user_id}: {e}", exc_info=True)