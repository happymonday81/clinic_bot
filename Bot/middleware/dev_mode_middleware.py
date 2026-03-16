# Bot/middleware/dev_mode_middleware.py
import logging
from aiogram import Bot
from aiogram.methods import TelegramMethod
from aiogram.types import User, Message, Chat

logger = logging.getLogger(__name__)

def patch_bot_for_dev_mode(bot: Bot):
    """
    Подменяет метод отправки запросов у бота на заглушку.
    Вместо реального HTTP-запроса в Telegram, просто логирует действие.
    """
    
    async def fake_make_request(
        call: TelegramMethod,
        request_timeout: int = None,
        **kwargs  # <-- Добавили kwargs для безопасности
    ):
        """
        Фейковая реализация make_request.
        Возвращает мокированные ответы, чтобы код не падал.
        """
        method_name = call.__class__.__name__
        
        # 1. Логируем намерение бота
        logger.info(f" [DEV MOCK] Bot attempted to call: {method_name}")
        
        # 2. Пытаемся вытащить полезную информацию (текст, caption)
        content = getattr(call, 'text', None) or getattr(call, 'caption', None)
        if content:
            preview = content[:100] + "..." if len(content) > 100 else content
            print(f"   💬 Bot says: {preview}")
        
        # 3. Возвращаем фейковые успешные ответы
        
        if method_name == "GetMe":
            return User(id=999, is_bot=True, first_name="DevBot", username="dev_bot")
        
        if method_name == "DeleteWebhook":
            return True
            
        if method_name == "SendMessage":
            return Message(
                message_id=99999,
                date=None,
                chat=Chat(id=999, type="private"),
                from_user=User(id=999, is_bot=True, first_name="DevBot"),
                text=content
            )
            
        if method_name == "SendPhoto":
            return Message(
                message_id=99999,
                date=None,
                chat=Chat(id=999, type="private"),
                from_user=User(id=999, is_bot=True, first_name="DevBot"),
                caption=content,
                photo=[]
            )

        if method_name == "EditMessageText":
             return True
        
        if method_name == "SendChatAction":
             return True

        # Для всех остальных методов возвращаем True
        return True

    # Применяем подмену: важно, что теперь функция принимает те же аргументы, что и оригинал
    # В aiogram session вызывает make_request(call, timeout=...)
    # Поэтому мы явно назвали аргумент request_timeout и добавили **kwargs
    bot.session.make_request = fake_make_request
    logger.info("✅ DevModeMiddleware applied: Bot is now offline-safe.")