import asyncio
from pathlib import Path

from pyrogram import Client
from importlib import import_module

from database.models import async_engine, Base
from main.variables import APP_ID, API_HASH, BOT_TOKEN


class ToDoApp(Client):
    """
    Custom Client class for the ToDo app.
    """

    async def start(self: "pyrogram.Client"):
        """
        Start the ToDo app.
        """
        await asyncio.gather(self.create_table())
        await super().start()

    async def create_table(self):
        """
        Create database tables.
        """
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"Error creating database tables: {e}")

app = ToDoApp(
    "todo_bot",
    api_id=APP_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

for file_handlers in Path("./").rglob("handlers.py"):
    module_path = ".".join(file_handlers.parts[1:-1])+ ".handlers"

    print(module_path)
    import_module(module_path)
