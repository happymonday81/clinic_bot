import asyncio
from aiogram.types import Message, User, Chat
from datetime import datetime


class FakeBot:
    async def send_message(self, chat_id, text, **kwargs):
        print(f"\n🤖 BOT: {text}\n")


async def simulate_message(dp, text: str):
    user = User(
        id=1,
        is_bot=False,
        first_name="Test",
        username="dev_user"
    )

    chat = Chat(
        id=1,
        type="private"
    )

    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text=text
    )

    bot = FakeBot()

    await dp.feed_update(bot, {"message": message})


async def run_console(dp):
    print("\n🧪 DEV MODE — Console testing started")
    print("Введите сообщение (exit для выхода)\n")

    while True:
        text = input("👤 YOU: ")

        if text == "exit":
            break

        await simulate_message(dp, text)
