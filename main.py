import asyncio
import re

from aiogram import F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, ReactionTypeEmoji

from flags import flag_buttons
from flags_keyboard import flag_router, get_language_keyboard, user_selected_languages
from headers import bot, dp, scheduler
from keyboards import *
from manager import change_bot_name, set_chat_name_direct
from timers import start_action, finish_action

dp.include_router(flag_router)


class MyState(StatesGroup):
    menu = State()
    edit_name = State()
    edit_token = State()
    # edit_avatar = State()
    edit_name_chat_channel = State()
    edit_channel_chat_id = State()

    ended = State()


# Отмена действия
@dp.callback_query(F.data == 'main_menu')
async def cancel_action(call: types.CallbackQuery, state: FSMContext):
    """

    :param call:
    :param state:
    :return:
    """
    await send_main_menu(call.from_user.id, state)


# Главное меню
async def send_main_menu(chat_id, state: FSMContext):
    """

    :param chat_id:
    :param state:
    :return:
    """

    # удаляем старое главное и незавершенные сообщения
    data = await state.get_data()

    old_message_id = data.get("main_message_id", False)
    if old_message_id:
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=old_message_id, text='Действие прервано')
        except:
            pass
    unfinised_form_message_id = data.get('form_message', False)
    if unfinised_form_message_id:
        try:
            await bot.delete_message(chat_id, unfinised_form_message_id)
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

    await state.update_data(main_message_id=sent_message.message_id)


# Обработчик команды /start
@dp.message(Command("start"))
async def handle_start(message: types.Message, state: FSMContext):
    """

    :param message:
    :param state:
    :return:
    """

    chat_id = message.chat.id
    # удаляем это сообщение пользователя
    try:
        await bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass
    await send_main_menu(chat_id, state)


# Форма ввода для изменения названия
@dp.callback_query(F.data == 'edit_name')
async def start_name_change(call: CallbackQuery, state: FSMContext):
    """

    :param call:
    :param state:
    :return:
    """
    chat_id = call.message.chat.id
    keyboard = name_keyboard
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=name_type_question)
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id,
                                                       reply_markup=keyboard)

    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(chat_id, data.get("main_message_id"), None)


# Запрашиваем языки
@dp.callback_query(F.data == 'edit_name_geo')
async def ask_for_lang(call: CallbackQuery, state: FSMContext):
    """

    :param call:
    :param state:
    :return:
    """
    chat_id = call.from_user.id
    keyboard = get_language_keyboard(user_selected_languages.get(chat_id, None))
    data = await state.get_data()

    await bot.edit_message_text(chat_id=chat_id, message_id=data.get('main_message_id'),
                                text=lang_type_question)
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data.get('main_message_id'),
                                                       reply_markup=keyboard)

    # await state.update_data(form_message=sent_message.message_id)
    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(chat_id, data.get("main_message_id"), data.get("message_id"))


# Запрашиваем имя
@dp.callback_query(F.data.in_({"edit_name_simple", "edit_name_chat_channel"}))
async def ask_for_name(call: CallbackQuery, state: FSMContext, user_id=None, false_msg=""):
    """

    :param false_msg:
    :param call:
    :param state:
    :param user_id:
    :return:
    """

    if user_id is None:
        user_id = call.from_user.id

    text = ask_for_new_name
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    sent_message = await bot.send_message(chat_id=user_id, text=false_msg + text, reply_markup=keyboard)
    await state.update_data(form_message=sent_message.message_id)
    if call.data == "edit_name_simple":
        await state.set_state(MyState.edit_name)
    elif call.data == "edit_name_chat_channel":
        await state.set_state(MyState.edit_name_chat_channel)

    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(user_id, data.get("main_message_id"), data.get("message_id"))


# Проверка и сохранение нового названия бота/чата/канала
@dp.message(StateFilter(MyState.edit_name_chat_channel, MyState.edit_name))
async def handle_name_input(message: types.Message, state: FSMContext):
    """

    :param message:
    :param state:
    :return:
    """
    chat_id = message.chat.id
    text = message.text.strip()
    data = await state.get_data()

    if not (1 <= len(text) <= 64):
        await bot.delete_message(chat_id, message.message_id)
        await bot.delete_message(chat_id, data.get("form_message"))
        await ask_for_name(None, state, chat_id, symbol_limit)
        return
    # Успешно! Дальше просим токен

    last_bot_msg = data.get("message_id")

    await bot.delete_message(chat_id, last_bot_msg)
    await bot.delete_message(chat_id, message.message_id)

    await state.update_data(name=text)

    # Запоминаем, для чего нам token
    current_state = await state.get_state()
    if current_state == MyState.edit_name:
        await state.update_data(last_state='name')
        await ask_for_token(chat_id, state)
    elif current_state == MyState.edit_name_chat_channel:
        await state.update_data(last_state='chat_channel_name')
        await ask_for_chat_channel_id(chat_id, state)


# Запрос id чата, канала
async def ask_for_chat_channel_id(chat_id, state: FSMContext, false_msg=""):
    """

    :param false_msg:
    :param chat_id:
    :param state:
    :return:
    """
    text = ask_for_chat_or_channel_id
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    sent_message = await bot.send_message(chat_id, false_msg + text, reply_markup=keyboard)

    await state.set_state(MyState.edit_channel_chat_id)

    await state.update_data(form_message=sent_message.message_id)
    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(chat_id, data.get("main_message_id"), data.get("message_id"))


@dp.message(StateFilter(MyState.edit_channel_chat_id))
async def handle_id_input(message: types.Message, state: FSMContext):
    """

    :param message:
    :param state:
    :return:
    """
    chat_id = message.chat.id

    targer_chat_id = message.text.strip()

    data = await state.get_data()
    new_name = data.get("name")

    await bot.delete_message(chat_id, message.message_id)

    last_bot_msg = data.get("message_id")
    if last_bot_msg:
        await bot.delete_message(chat_id, last_bot_msg)

    result, msg = await set_chat_name_direct(bot, targer_chat_id, new_name)
    if result is False:
        await ask_for_chat_channel_id(chat_id, state, incorrect_id)
        return

    keyboard = create_inline_keyboard([InlineKeyboardButton(text="Меню", callback_data="main_menu")])

    await bot.edit_message_text(chat_id=chat_id, message_id=data['main_message_id'], text=msg)
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data['main_message_id'],
                                                       reply_markup=keyboard)
    await state.update_data(message_id=sent_message.message_id)

    # Стираем id старого главного сообщения
    await state.update_data(main_message_id=None)
    await state.set_state(MyState.ended)

    await finish_action(chat_id)


# Запрос токена
async def ask_for_token(chat_id, state: FSMContext, false_msg=""):
    """

    :param chat_id:
    :param state:
    :return:
    """
    text = ask_bot_token
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    sent_message = await bot.send_message(chat_id, false_msg + text, reply_markup=keyboard)

    await state.set_state(MyState.edit_token)

    await state.update_data(form_message=sent_message.message_id)
    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(chat_id, data.get("main_message_id"), data.get("message_id"))


# Проверка токена
@dp.message(StateFilter(MyState.edit_token))
async def handle_token_input(message: types.Message, state: FSMContext):
    """

    :param message:
    :param state:
    :return:
    """
    chat_id = message.chat.id
    token = message.text.strip()
    data = await state.get_data()

    if not re.match(r'^\d{10}:[A-Za-z0-9_-]{35}$', token):
        await bot.delete_message(chat_id, message.message_id)
        await bot.delete_message(chat_id, data.get("form_message"))
        # await message.reply(incorrect_token)
        await ask_for_token(chat_id, state, incorrect_token)
        return

    # last_state = data.get("last_state")

    # if last_state == 'name':

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
        result_text = f"✅ Успех! Название <a href='{result[0][1]}'>бота</a> обновлено на: {bot_name}" + addition

    else:

        result_text = f"❌ Ошибка! Попробуйте ещё раз чуть позже. {result[0][1]}"
    keyboard = create_inline_keyboard([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
    user_selected_languages[chat_id] = []

    await bot.delete_message(chat_id, message.message_id)

    await bot.edit_message_text(chat_id=chat_id, message_id=data['main_message_id'], text=result_text, parse_mode="html")
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data['main_message_id'],
                                                       reply_markup=keyboard)

    await state.update_data(message_id=sent_message.message_id)

    # Стираем id старого главного сообщения
    await state.update_data(main_message_id=None)
    await state.set_state(MyState.ended)

    #
    await finish_action(chat_id)
    '''elif last_state == 'avatar':
        pass
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
        await state.set_state(MyState.ended)'''


# Отмена действия
@dp.callback_query(F.data == 'cancel')
async def cancel_action(callback_query: types.CallbackQuery, state: FSMContext):
    """

    :param callback_query:
    :param state:
    :return:
    """
    chat_id = callback_query.message.chat.id
    data = await state.get_data()
    message_id = data.get("message_id", False)
    if message_id:
        await bot.delete_message(chat_id, message_id)
    await state.set_state(MyState.ended)
    # await send_main_menu(chat_id, state)


# Обработчик произвольных сообщений
@dp.message()
async def handle_any_message(message: types.Message, state: FSMContext):
    """

    :param message:
    :param state:
    :return:
    """
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

    emoji = ReactionTypeEmoji(emoji=what_emodji)
    await message.react([emoji])
    await send_main_menu(chat_id, state)


# Запуск таймеров через APScheduler
async def local_startup():
    scheduler.start()
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
