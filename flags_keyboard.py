from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from flags import flag_buttons
from headers import bot
from keyboards import name_keyboard, desc_keyboard, name_type_question, desc_type_question

# Состояние для хранения выбранных языков
user_selected_languages = {}

flag_router = Router()


# Функция для создания клавиатуры
def get_language_keyboard(selected_languages=None, change_type=None):
    if selected_languages is None:
        selected_languages = []

    # Create InlineKeyboardBuilder
    keyboard_builder = InlineKeyboardBuilder()

    # Добавляем кнопки с языками
    for i in range(0, len(flag_buttons), 3):  # Step by 3
        row_buttons = []
        for flag, code in flag_buttons[i:i + 3]:
            is_selected = code in selected_languages
            button_text = f"{flag} ✅" if is_selected else flag
            row_buttons.append(InlineKeyboardButton(text=button_text, callback_data=f"toggle_lang:{code}"))
        keyboard_builder.row(*row_buttons)  # Add row of buttons

    # Кнопки управления
    keyboard_builder.row(
        InlineKeyboardButton(text="Очистить выбор", callback_data="clear_selection"),
        InlineKeyboardButton(text="Выбрать все", callback_data="select_all")
    )
    if len(selected_languages) > 0:
        keyboard_builder.row(
            InlineKeyboardButton(text="‹ Назад", callback_data=f"go_back_{change_type}"),
            InlineKeyboardButton(text="Далее ››", callback_data="edit_name_simple") if change_type == 'name' else InlineKeyboardButton(text="Далее ››", callback_data="edit_description_simple")
        )
    else:
        keyboard_builder.row(
            InlineKeyboardButton(text="‹ Назад", callback_data=f"go_back_{change_type}"),
        )

    return keyboard_builder.as_markup()


# Обработчик переключения языков
@flag_router.callback_query(F.data.startswith("toggle_lang:"))
async def toggle_language(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang_code = callback_query.data.split(":")[1]

    # Инициализируем состояние для пользователя
    if user_id not in user_selected_languages:
        user_selected_languages[user_id] = []

    # Переключаем состояние выбранного языка
    if lang_code in user_selected_languages[user_id]:
        user_selected_languages[user_id].remove(lang_code)
    else:
        user_selected_languages[user_id].append(lang_code)

    # Обновляем клавиатуру
    keyboard = get_language_keyboard(user_selected_languages[user_id])
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


# Очистить выбор
@flag_router.callback_query(F.data == "clear_selection")
async def clear_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_selected_languages[user_id] = []
    keyboard = get_language_keyboard(user_selected_languages[user_id])
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


# Выбрать все
@flag_router.callback_query(F.data == "select_all")
async def select_all(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_selected_languages[user_id] = [code for _, code in flag_buttons]
    keyboard = get_language_keyboard(user_selected_languages[user_id])
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


# Кнопки назад/далее
@flag_router.callback_query(F.data.startswith("go_back"))
async def go_back(callback_query: types.CallbackQuery, state: FSMContext):
    change_type = callback_query.data.split("_")[-1]
    chat_id = callback_query.from_user.id
    data = await state.get_data()
    if change_type == 'name':
        keyboard = name_keyboard
        prase = name_type_question
    else:
        keyboard = desc_keyboard
        prase = desc_type_question
    await bot.edit_message_text(chat_id=chat_id, message_id=data['main_message_id'], text=prase)
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data['main_message_id'],
                                        reply_markup=keyboard)


@flag_router.callback_query(F.data == "proceed")
async def proceed(callback_query: types.CallbackQuery):
    selected = user_selected_languages.get(callback_query.from_user.id, [])
    await callback_query.message.edit_text(f"Вы выбрали языки: {', '.join(selected)}")
