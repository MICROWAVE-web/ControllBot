from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ___ Клавиатуры ___

# Menu keyboard
def create_keyboard_menu():
    return create_inline_keyboard([
        InlineKeyboardButton(text="Название", callback_data="edit_name"),
        InlineKeyboardButton(text="Описание", callback_data="edit_description"),
        InlineKeyboardButton(text="Команды", callback_data="edit_commands"),
        # InlineKeyboardButton(text="Аватар", callback_data="edit_avatar")
    ])


# Помощник для создания инлайн-кнопок
def create_inline_keyboard(buttons):
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.row(
        *buttons,
        width=3
    )
    # return InlineKeyboardMarkup(inline_keyboard=[buttons])
    return keyboard_builder.as_markup()


name_keyboard = create_inline_keyboard(
    [
        InlineKeyboardButton(text="Основное", callback_data="edit_name_simple"),
        InlineKeyboardButton(text="МультиГео", callback_data="edit_name_geo"),
        InlineKeyboardButton(text="Канал · Чат", callback_data="edit_name_chat_channel"),
        InlineKeyboardButton(text="< Назад", callback_data="back_to_menu"),
    ]
)

desc_keyboard = create_inline_keyboard(
    [
        InlineKeyboardButton(text="Основное", callback_data="edit_description_simple"),
        InlineKeyboardButton(text="МультиГео", callback_data="edit_description_geo"),
        InlineKeyboardButton(text="< Назад", callback_data="back_to_menu"),
    ]
)

command_keyboard = create_inline_keyboard(
    [
        InlineKeyboardButton(text="Изменить", callback_data="edit_commands_simple"),
        InlineKeyboardButton(text="< Назад", callback_data="back_to_menu"),
    ]
)

# ___ Текста ___


start_message = "Я могу помочь тебе управлять твоими Telegram ботами, каналами и чатами удаленно.\n<a href='google.com'>Help</a> · <a href='google.com'>FAQ</a> · <a href='google.com'>Tools</a>"

cancel_text = 'Отменить 🚫'

name_type_question = "Какое название редактируем?"

desc_type_question = "Какое описание редактируем?"

commands_type_question = "Изменяем команды?"

ask_for_new_name = "Пришли новое название:"

ask_for_new_desc = "Пришли новое описание:"

ask_for_new_commands = "Пришли команды:\n\nКоманда1 - Описание1\nКоманда2 - Описание2"

ask_for_chat_or_channel_id = "Пришли id чата, канала:"

incorrect_token = "Некорректный токен! Актуальный можно получить в @Botfather.\n\n"

incorrect_id = "Некорректный ID! Формат: 123456789 или -100123456789\n\n"

what_emodji = '🤔'

ask_bot_token = "Пришли токен бота:"


def lang_type_question(change_type):
    if change_type == 'name':
        change_type = 'название'
    elif change_type == 'description':
        change_type = 'описание'
    return f"Для каких языков устанавливаем {change_type}?"


def symbol_limit(limit):
    return f"Некорректное название! Используй только текст до {limit} символов.\n\n"
