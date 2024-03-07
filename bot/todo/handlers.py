from pyrogram import filters, Client
from pyrogram.types import (
    InlineKeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    CallbackQuery,
)

from database.models import Task, User, StatesUserEnum
from database.repository import Repository
from main.client import app
from main.middleware import get_user
from todo.buttons import REPLY_KEYBOARD
from todo.implementation import RegistrationUser, CreateTask, UpdateTask


@app.on_message(filters.command("start") & filters.private)
async def start_wrapper(_, message: Message) -> None:
    """
    Handle /start command.
    """
    user = await Repository.get_user(tg_id=message.from_user.id)
    if not user:
        await Repository.create_user(tg_id=message.from_user.id)
        await message.reply_text("Hello", reply_markup=REPLY_KEYBOARD)


@app.on_message(filters.command("registration") & filters.private)
@get_user
async def start_registration(client: Client, message: Message, user: User) -> None:
    """
    Handle /registration command.
    """
    text, buttons = await RegistrationUser(user).start_action()
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True) if buttons else None
    await message.reply_text(text, reply_markup=reply_markup)


@app.on_message(filters.command("create") & filters.private)
@get_user
async def start_create(client: Client, message: Message, user: User) -> None:
    """
    Handle /create command.
    """
    text, buttons = await CreateTask(user).start_action()
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True) if buttons else None
    await message.reply_text(text, reply_markup=reply_markup)


@app.on_message(filters.command("show") & filters.private)
@get_user
async def show_tasks(client: Client, message: Message, user: User) -> None:
    """
    Handle /show command.
    """
    tasks = await Repository.get_tasks(user=user, params={"is_visible": True})
    for [task] in tasks:
        text = f"<b>{task.title}</b>\n" \
               f"Description: <i>{task.description}</i>\n" \
               f"Status: <code>{'complite' if task.is_complete else 'not complited'}</code>"
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="update",
                            callback_data=f"updatetask_{task.id}"
                        ),
                        InlineKeyboardButton(
                            text="uncomplite task" if task.is_complete else "complite task",
                            callback_data=f"completetask_{task.id}"
                        ),
                        InlineKeyboardButton(
                            text="delete task",
                            callback_data=f"deletetask_{task.id}"
                        )
                    ]
                ]
            )
        )


@get_user
async def change_status_task(client: Client, call: CallbackQuery, task_id: int, user: User) -> None:
    """
    Change task status based on callback query.
    """
    task: Task = await Repository.get_task(user, task_id)
    task.is_complete = not task.is_complete
    await Repository.save(task)
    await call.message.reply_text(
        f"<b>Task {task.title} status:</b> {'<i>completed</i>' if task.is_complete else '<i>not completed</i>'}"
    )



@get_user
async def delete_task(client: Client, call: CallbackQuery, task_id: int, user: User) -> None:
    """
    Delete task based on callback query.
    """
    await Repository.delete_task(user, task_id)
    await call.message.reply_text(f"<b>Task was deleted</b>")


@get_user
async def start_update_task(client: Client, call: CallbackQuery, task_id: int, user: User) -> None:
    """
    Start updating a task based on callback query.
    """
    user.task_id = task_id
    text, buttons = await UpdateTask(user).start_action()
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True) if buttons else None
    await call.message.reply_text(text, reply_markup=reply_markup)


@app.on_callback_query()
async def command_query(client: Client, call: CallbackQuery) -> None:
    """
    Handle callback queries.
    """
    operation, id = call.data.split('_')
    id = int(id)
    if operation == "updatetask":
        await start_update_task(client, call, task_id=id)
    elif operation == "completetask":
        await change_status_task(client, call, task_id=id)
    elif operation == "deletetask":
        await delete_task(client, call, task_id=id)


@app.on_message(filters.text & filters.private)
@get_user
async def make_action(client: Client, message: Message, user: User) -> None:
    """
    Perform an action based on user input.
    """
    if user.status == StatesUserEnum.FINISH:
        return
    elif user.status < 10:
        text, buttons = await RegistrationUser(user).continue_action(message.text)
    elif user.status < 20:
        text, buttons = await CreateTask(user).continue_action(message.text)
    elif user.status < 30:
        text, buttons = await UpdateTask(user).continue_action(message.text)
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True) if buttons else None
    await message.reply_text(text, reply_markup=reply_markup)
