from pyrogram.types import KeyboardButton, ReplyKeyboardMarkup

BUTTONS_AFTER_REGISTRATION = [
    [
        KeyboardButton(
            text="/create task",
        ),
        KeyboardButton(
            text="/show tasks",
        ),
    ]
]

REPLY_KEYBOARD = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(
            text="/registration",
        )
    ],
], resize_keyboard=True, one_time_keyboard=True, placeholder="Press any button")
