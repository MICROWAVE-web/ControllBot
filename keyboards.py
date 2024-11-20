from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Помощник для создания инлайн-кнопок
def create_inline_keyboard(buttons):
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


name_keyboard = create_inline_keyboard([
    InlineKeyboardButton(text="Основное", callback_data="edit_name_simple"),
    InlineKeyboardButton(text="МультиГео", callback_data="edit_name_geo"),
    InlineKeyboardButton(text="Канал · Чат", callback_data="edit_name_chat_channel")
])

start_message = "Я могу помочь тебе управлять твоими Telegram ботами, каналами и чатами удаленно.\n\nHelp · FAQ · Tools"

cancel_text = 'Отменить 🚫'

name_type_question = "Какое название редактируем?"

lang_type_question = "Для каких языков устанавливаем название?"

ask_for_new_name = "Пришли новое название:"

symbol_limit = "Некорректное название! Используй только текст до 64 символов.\n\n"

ask_for_chat_or_channel_id = "Пришли id чата, канала:"

incorrect_token = "Некорректный токен! Актуальный можно получить в @Botfather.\n\n"

incorrect_id = "Некорректный ID! Формат: 123456789 или -100123456789\n\n"


what_emodji = '🤔'

ask_bot_token = "Пришли токен бота:"
