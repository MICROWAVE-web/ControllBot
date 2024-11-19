import asyncio
import os
import re

from aiogram import F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, ReactionTypeEmoji, InlineKeyboardButton

from flags import flag_buttons
from flags_keyboard import flag_router, get_language_keyboard, user_selected_languages
from headers import bot, dp
from keyboards import *
from manager import change_bot_name, change_bot_pic

dp.include_router(flag_router)


class MyState(StatesGroup):
    menu = State()
    edit_name = State()
    edit_token = State()
    edit_avatar = State()
    ended = State()


# Отмена действия
@dp.callback_query(F.data == 'main_menu')
async def cancel_action(call: types.CallbackQuery, state: FSMContext):
    await send_main_menu(call.from_user.id, state)


# Главное меню
async def send_main_menu(chat_id, state: FSMContext, message_id=None):
    # удаляем старое главное и незавершенные сообщения
    data = await state.get_data()
    old_message_id = data.get("main_message_id", False)
    if old_message_id:
        try:
            await bot.delete_message(chat_id, old_message_id)
        except:
            pass

    message_id = data.get("message_id", False)
    # удаляем клавиатуру последнего сообщения
    try:
        if message_id:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,  # Идентификатор предыдущего сообщения
                reply_markup=None
            )
    except Exception:
        pass

    text = start_message
    keyboard = create_inline_keyboard([
        InlineKeyboardButton(text="Название", callback_data="edit_name"),
        # InlineKeyboardButton(text="Аватар", callback_data="edit_avatar")
    ])
    sent_message = await bot.send_message(chat_id, text, reply_markup=keyboard)

    await state.set_state(MyState.menu)

    data = await state.get_data()
    data["main_message_id"] = sent_message.message_id
    await state.set_data(data)


# Обработчик команды /start
@dp.message(Command("start"))
async def handle_start(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    # удаляем это сообщение пользователя
    try:
        await bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass
    # удаляем старое главное сообщение
    data = await state.get_data()
    old_message_id = data.get("main_message_id", False)
    if old_message_id:
        try:
            await bot.delete_message(chat_id, old_message_id)
        except Exception:
            pass

    await send_main_menu(chat_id, state)


# Форма ввода для изменения названия
@dp.callback_query(F.data == 'edit_name')
async def start_name_change(call: CallbackQuery, state: FSMContext):
    chat_id = call.message.chat.id
    keyboard = create_inline_keyboard([
        InlineKeyboardButton(text="Основное", callback_data="edit_name_simple"),
        InlineKeyboardButton(text="МультиГео", callback_data="edit_name_geo")
    ])
    data = await state.get_data()
    message_id = data.get("message_id", call.message.message_id)
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=name_type_question)
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id,
                                                       reply_markup=keyboard)

    data = await state.get_data()
    data["message_id"] = sent_message.message_id
    await state.set_data(data)


# Запрашиваем языки
@dp.callback_query(F.data == 'edit_name_geo')
async def ask_for_lang(call: CallbackQuery, state: FSMContext):
    keyboard = get_language_keyboard(user_selected_languages.get(call.from_user.id, None))
    data = await state.get_data()

    await bot.edit_message_text(chat_id=call.from_user.id, message_id=data.get('message_id'),
                                text="Для каких языков устанавливаем название?")
    sent_message = await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=data.get('message_id'),
                                                       reply_markup=keyboard)

    data = await state.get_data()
    data["message_id"] = sent_message.message_id
    await state.set_data(data)


# Запрашиваем имя
@dp.callback_query(F.data == 'edit_name_simple')
async def ask_for_name(call, state: FSMContext, user_id=None):
    if user_id is None:
        user_id = call.from_user.id
    text = "Пришли новое название:"
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])

    sent_message = await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)

    await state.set_state(MyState.edit_name)

    data = await state.get_data()
    data["message_id"] = sent_message.message_id
    await state.set_data(data)


# Проверка и сохранение нового названия
@dp.message(StateFilter(MyState.edit_name))
async def handle_name_input(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    text = message.text.strip()
    if not (1 <= len(text) <= 64):
        await message.reply("Некорректное название! Используй только текст до 64 символов.")
        await ask_for_name(None, state, chat_id)
        return
    # Успешно! Дальше просим токен

    data = await state.get_data()
    last_bot_msg = data.get("message_id")

    await bot.delete_message(chat_id, last_bot_msg)
    await bot.delete_message(chat_id, message.message_id)

    data = await state.get_data()
    data["name"] = text
    await state.set_data(data)

    # Запоминаем, для чего нам token
    data = await state.get_data()
    data["last_state"] = 'name'
    await state.set_data(data)

    await ask_for_token(chat_id, state)


# Запрос токена
async def ask_for_token(chat_id, state: FSMContext):
    text = "Пришли токен бота:"
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    sent_message = await bot.send_message(chat_id, text, reply_markup=keyboard)

    await state.set_state(MyState.edit_token)

    data = await state.get_data()
    data["message_id"] = sent_message.message_id
    await state.set_data(data)


# Проверка токена
@dp.message(StateFilter(MyState.edit_token))
async def handle_token_input(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    token = message.text.strip()
    if not re.match(r'^\d{10}:[A-Za-z0-9_-]{35}$', token):
        await message.reply("Некорректный токен! Актуальный можно получить в @Botfather.")
        await ask_for_token(chat_id, state)
        return

    data = await state.get_data()

    last_state = data.get("last_state")

    if last_state == 'name':

        bot_name = data.get("name")
        await bot.delete_message(chat_id, data.get("message_id"))
        selected = user_selected_languages.get(chat_id, [])
        if len(selected) > 0:
            addition = f' Для языков {", ".join(list(filter(lambda x: x[1] == lang, flag_buttons))[0][0] for lang in selected)}'
        else:
            addition = ''

        task = asyncio.create_task(change_bot_name(token, bot_name, selected))

        # Ожидаем завершения задач
        result = await asyncio.gather(task)

        if result[0][0]:
            result_text = f"✅ Успех! Название бота обновлено на: {bot_name}" + addition

        else:

            result_text = f"❌ Ошибка! Попробуйте ещё раз чуть позже. {result[0][1]}"
        keyboard = create_inline_keyboard([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
        user_selected_languages[chat_id] = []

        await bot.delete_message(chat_id, message.message_id)

        data = await state.get_data()
        await bot.edit_message_text(chat_id=chat_id, message_id=data['main_message_id'], text=result_text)
        sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data['main_message_id'],
                                                           reply_markup=keyboard)

        data = await state.get_data()
        data["message_id"] = sent_message.message_id
        await state.set_data(data)

        await state.set_state(MyState.ended)

    elif last_state == 'avatar':
        photo_id = data.get("photo")
        file = await bot.get_file(photo_id)
        file_name = os.path.basename(file.file_path)
        # Скачиваем файл во временную папку
        folder = './downloads'
        if not os.path.exists(folder):
            os.makedirs(folder)
        download_path = f'{folder}/{file_name}'
        await bot.download_file(file.file_path, download_path)
        task = asyncio.create_task(change_bot_pic(token, download_path, message.chat.id))

        # Ожидаем завершения задач
        result = await asyncio.gather(task)
        print(result)
        await state.set_state(MyState.ended)


# Отмена действия
@dp.callback_query(F.data == 'cancel')
async def cancel_action(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    data = await state.get_data()
    message_id = data.get("message_id", False)
    if message_id:
        await bot.delete_message(chat_id, message_id)
    await state.set_state(MyState.ended)
    await send_main_menu(chat_id, state)


# Обработчик произвольных сообщений
@dp.message()
async def handle_any_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    current_state = await state.get_state()
    if current_state in [MyState.edit_name.state, MyState.edit_token.state]:
        return  # Если активна форма ввода, не реагируем

    data = await state.get_data()
    message_id = data.get("message_id", False)
    # удаляем клавиатуру последнего сообщения
    try:
        if message_id:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,  # Идентификатор предыдущего сообщения
                reply_markup=None
            )
    except:
        pass

    emoji = ReactionTypeEmoji(emoji='🤔')
    await message.react([emoji])
    await send_main_menu(chat_id, state)


# Запуск таймеров через APScheduler
async def local_startup():
    await dp.start_polling(bot)


'''@dp.callback_query(F.data == 'edit_avatar')
# Форма ввода для изменения названия
async def start_avatar_change(call: CallbackQuery, state: FSMContext):
    chat_id = call.message.chat.id
    data = await state.get_data()
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    await bot.edit_message_text(chat_id=chat_id, message_id=data['main_message_id'], text="Пришли новый аватар:")
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data['main_message_id'],
                                                       reply_markup=keyboard)

    await state.set_state(MyState.edit_avatar)

    data = await state.get_data()
    data["message_id"] = sent_message.message_id
    await state.set_data(data)


@dp.message(StateFilter(MyState.edit_avatar))
async def handle_photo(message: Message, state: FSMContext):
    try:

        data = await state.get_data()
        message_id = data.get("message_id", False)
        if message_id is False:
            await send_main_menu(message.chat.id, state)
            return
            # Проверяем, есть ли фото в сообщении
        if not message.photo:
            await bot.delete_message(message.from_user.id, message.message_id)
            await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                        text="Я не вижу изображение. Пожалуйста, отправьте фото. Попробуйте отправить ещё раз.")
            return

        # Берём наибольшее разрешение фотографии
        photo = message.photo[-1]

        # Проверяем размер файла
        file_info = await bot.get_file(photo.file_id)
        if file_info.file_size > 5 * 1024 * 1024:  # Ограничение 5 МБ
            await bot.delete_message(message.from_user.id, message.message_id)
            await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                        text="Извините, файл слишком большой. Максимальный размер — 5 МБ. Попробуйте отправить ещё раз.")
            return

        # Проверяем формат файла (если нужно, можно добавить дополнительные проверки)
        file_path = file_info.file_path
        if not file_path.endswith(('.jpg', '.jpeg', '.png')):
            await bot.delete_message(message.from_user.id, message.message_id)
            await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                        text="Формат изображения не поддерживается. Отправьте JPG или PNG. Попробуйте отправить ещё раз.")
            return

        last_bot_msg = data.get("message_id")

        # await bot.delete_message(message.from_user.id, message.message_id) TODO
        await bot.delete_message(message.chat.id, last_bot_msg)

        # Сохраняем file_id в состоянии
        await state.update_data(photo=photo.file_id)

        # Запоминаем, для чего нам token
        data = await state.get_data()
        data["last_state"] = 'avatar'
        await state.set_data(data)

        await ask_for_token(message.chat.id, state)
    except Exception as e:
        await message.reply(f"Произошла ошибка при обработке фото, попробуйте ещё раз.")'''

# Запуск бота
if __name__ == "__main__":
    asyncio.run(local_startup())
