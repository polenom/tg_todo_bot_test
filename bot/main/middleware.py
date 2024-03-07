from pyrogram import Client
from pyrogram.types import Message

from database.repository import Repository


def get_user(func):
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        user = await Repository.get_user(tg_id=message.from_user.id)
        if user:
            return await func(client, message, *args, user=user, **kwargs)
        else:
            await message.reply_text("Введите команду /start для начала работы")
    return wrapper
