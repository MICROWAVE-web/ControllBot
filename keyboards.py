from aiogram.types import InlineKeyboardMarkup


# Помощник для создания инлайн-кнопок
def create_inline_keyboard(buttons):
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


start_message = "Я могу помочь тебе управлять твоими Telegram ботами, каналами и чатами удаленно.\n\nHelp · FAQ · Tools"

cancel_text = 'Отменить 🚫'

name_type_question = "Какое название редактируем?"
