import asyncio
import logging
from datetime import datetime
from aiogram import Dispatcher, Bot
from aiogram.types import Update, Message, Chat, User, CallbackQuery
from aiogram.enums import ChatType
from middleware.dev_mode_middleware import patch_bot_for_dev_mode

logger = logging.getLogger(__name__)

# Фейковый токен для работы объектов Bot в оффлайне
FAKE_TOKEN = "0000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

async def run_console(dp: Dispatcher):
    """
    Консольный режим для тестирования хендлеров без подключения к Telegram.
    """
    print("\n" + "="*50)
    print("🧪 DEV CONSOLE MODE")
    print("="*50)
    print("Доступные команды:")
    print("  /start              - Начать диалог")
    print("  /admin              - Админ панель")
    print("  📝 Записаться...    - (введи текст кнопки меню)")
    print("  exit                - Выход из режима")
    print("  help                - Список команд")
    print("-" * 50)
    print("Вводи команды ниже (текст или callback_data):\n")

    # Создаем фейкового бота (нужен для контекста, но не ходит в сеть)
    fake_bot = Bot(token=FAKE_TOKEN, validate_token=False)
    patch_bot_for_dev_mode(fake_bot)
    
    # Фейковый пользователь (ты)
    fake_user = User(
        id=999999,
        is_bot=False,
        first_name="Dev",
        last_name="User",
        username="developer",
        language_code="ru"
    )
    
    # Фейковый чат
    fake_chat = Chat(
        id=999999,
        type=ChatType.PRIVATE,
        first_name="Dev",
        username="developer"
    )

    # Хранилище последних сообщений для эмуляции ответа на callback
    last_message_id = 1

    while True:
        try:
            # Читаем ввод пользователя
            user_input = input(">>> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Exiting dev console...")
                await fake_bot.session.close()
                break
            
            if user_input.lower() == "help":
                print("   /start, /admin, /book (пример)")
                print("   cb:specialty:therapist (эмуляция callback)")
                continue

            last_message_id += 1
            current_time = datetime.now()

            # Определяем тип ввода: команда/текст или callback
            if user_input.startswith("cb:"):
                # Эмуляция нажатия кнопки (CallbackQuery)
                callback_data = user_input[3:] # Убираем префикс "cb:"
                logger.info(f" Emulating Callback: {callback_data}")
                
                # Создаем фейковое сообщение, к которому привязана кнопка
                fake_msg = Message(
                    message_id=last_message_id,
                    date=current_time,
                    chat=fake_chat,
                    from_user=fake_user,
                    text="Fake message with buttons"
                )
                
                callback_query = CallbackQuery(
                    id=str(last_message_id),
                    from_user=fake_user,
                    chat_instance="123456789",
                    data=callback_data,
                    message=fake_msg
                )
                
                update = Update(update_id=last_message_id, callback_query=callback_query)
                
            else:
                # Эмуляция текстового сообщения
                logger.info(f"💬 Emulating Message: {user_input}")
                
                message = Message(
                    message_id=last_message_id,
                    date=current_time,
                    chat=fake_chat,
                    from_user=fake_user,
                    text=user_input
                )
                
                update = Update(update_id=last_message_id, message=message)

            # --- ОТПРАВЛЯЕМ СОБЫТИЕ В ДИСПЕТЧЕР ---
            # Мы перехватываем ответы через middleware или просто смотрим логи,
            # так как напрямую вернуть ответ в консоль сложно без кастомного бота.
            # Но мы можем запустить обработку:
            
            try:
                await dp.feed_update(bot=fake_bot, update=update)
                print("   [Update processed. Check logs for bot answers.]")
            except Exception as e:
                print(f"   ❌ Error processing update: {e}")
                logger.error(f"Dev console error: {e}", exc_info=True)

        except KeyboardInterrupt:
            print("\n👋 Stopped by user")
            await fake_bot.session.close()
            break
        except EOFError:
            break