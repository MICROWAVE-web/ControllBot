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
from manager import change_bot_data, set_chat_name_direct
from timers import start_action, finish_action

dp.include_router(flag_router)


class MyState(StatesGroup):
    menu = State()

    edit_name = State()
    edit_description = State()
    edit_commands = State()

    edit_token = State()
    # edit_avatar = State()
    edit_name_chat_channel = State()
    edit_channel_chat_id = State()

    ended = State()


# Назад к меню
@dp.callback_query(F.data == 'back_to_menu')
async def back_to_menu(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("main_message_id", False)
    if message_id is False:
        return

    text = start_message
    keyboard = create_keyboard_menu()
    await bot.edit_message_text(chat_id=call.from_user.id, message_id=message_id, text=text, parse_mode='html')
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=message_id,
                                        reply_markup=keyboard)


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
    keyboard = create_keyboard_menu()
    sent_message = await bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='html')

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


# Форма ввода для изменения описания
@dp.callback_query(F.data == 'edit_description')
async def start_desc_change(call: CallbackQuery, state: FSMContext):
    """

    :param call:
    :param state:
    :return:
    """
    chat_id = call.message.chat.id
    keyboard = desc_keyboard
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=desc_type_question)
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id,
                                                       reply_markup=keyboard)

    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(chat_id, data.get("main_message_id"), None)


# Форма ввода для изменения описания
@dp.callback_query(F.data == 'edit_commands')
async def start_command_change(call: CallbackQuery, state: FSMContext):
    """

    :param call:
    :param state:
    :return:
    """
    chat_id = call.message.chat.id
    keyboard = command_keyboard
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=commands_type_question)
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id,
                                                       reply_markup=keyboard)

    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(chat_id, data.get("main_message_id"), None)


# Запрашиваем команды
@dp.callback_query(F.data.in_({"edit_commands_simple"}))
async def ask_for_commands(call: CallbackQuery, state: FSMContext, user_id=None, false_msg=""):
    """

    :param false_msg:
    :param call:
    :param state:
    :param user_id:
    :return:
    """

    if user_id is None:
        user_id = call.from_user.id

    await state.set_state(MyState.edit_commands)

    text = ask_for_new_commands
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    sent_message = await bot.send_message(chat_id=user_id, text=false_msg + text, reply_markup=keyboard)
    await state.update_data(form_message=sent_message.message_id)
    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(user_id, data.get("main_message_id"), data.get("message_id"))


# Запрашиваем языки
@dp.callback_query(F.data.in_({"edit_name_geo", "edit_description_geo"}))
async def ask_for_lang(call: CallbackQuery, state: FSMContext):
    """

    :param call:
    :param state:
    :return:
    """
    chat_id = call.from_user.id

    if 'name' in call.data:
        change_type = 'name'
    else:
        change_type = 'description'

    user_id = call.from_user.id
    keyboard = get_language_keyboard(user_id, user_selected_languages.get(chat_id, None), change_type)

    data = await state.get_data()

    await bot.edit_message_text(chat_id=chat_id, message_id=data.get('main_message_id'),
                                text=lang_type_question(change_type))
    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data.get('main_message_id'),
                                                       reply_markup=keyboard)

    # await state.update_data(form_message=sent_message.message_id)
    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(chat_id, data.get("main_message_id"), None)


# Запрашиваем описание
@dp.callback_query(F.data.in_({"edit_description_simple"}))
async def ask_for_desc(call: CallbackQuery, state: FSMContext, user_id=None, false_msg=""):
    """

    :param false_msg:
    :param call:
    :param state:
    :param user_id:
    :return:
    """

    if user_id is None:
        user_id = call.from_user.id

    await state.set_state(MyState.edit_description)

    text = ask_for_new_desc
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    sent_message = await bot.send_message(chat_id=user_id, text=false_msg + text, reply_markup=keyboard)
    await state.update_data(form_message=sent_message.message_id)
    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(user_id, data.get("main_message_id"), data.get("message_id"))


# Запрашиваем имя
@dp.callback_query(F.data.in_({"edit_name_simple", "edit_name_chat_channel"}))
async def ask_for_name(call, state: FSMContext, user_id=None, false_msg="", current_state=None):
    """

    :param false_msg:
    :param call:
    :param state:
    :param user_id:
    :return:
    """

    if user_id is None:
        user_id = call.from_user.id

    if current_state is None:
        if call.data == "edit_name_simple":
            await state.set_state(MyState.edit_name)
        elif call.data == "edit_name_chat_channel":
            await state.set_state(MyState.edit_name_chat_channel)
    else:
        await state.set_state(current_state)

    text = ask_for_new_name
    keyboard = create_inline_keyboard([InlineKeyboardButton(text=cancel_text, callback_data="cancel")])
    sent_message = await bot.send_message(chat_id=user_id, text=false_msg + text, reply_markup=keyboard)
    await state.update_data(form_message=sent_message.message_id)
    await state.update_data(message_id=sent_message.message_id)

    data = await state.get_data()
    await start_action(user_id, data.get("main_message_id"), data.get("message_id"))


# Проверка и сохранение новых команд бота
@dp.message(StateFilter(MyState.edit_commands))
async def handle_commands_input(message: types.Message, state: FSMContext):
    """

    :param message:
    :param state:
    :return:
    """

    def validate_commands(commands_message: str):
        # Разделяем сообщение на строки
        lines = commands_message.split("\n")
        # Проверяем количество команд
        if not (1 <= len(lines) <= 100):
            return False, f"Количество команд должно быть от 1 до 100, найдено: {len(lines)}"

        # Регулярное выражение для проверки строки
        pattern = r"^[a-z]{1,32}\s-\s.{1,256}$"

        for index, line in enumerate(lines, start=1):
            if not re.match(pattern, line):
                return False, "Ошибка формата!\n"

        # Если все строки валидны
        return True, ""

    chat_id = message.chat.id
    text = message.text.strip()
    data = await state.get_data()

    is_valid, validate_message = validate_commands(text)

    if not is_valid:
        await bot.delete_message(chat_id, message.message_id)
        await bot.delete_message(chat_id, data.get("form_message"))
        await ask_for_commands(None, state, chat_id, validate_message)
        return

    # Успешно! Дальше просим токен

    last_bot_msg = data.get("message_id")

    await bot.delete_message(chat_id, last_bot_msg)
    await bot.delete_message(chat_id, message.message_id)

    await state.update_data(commands=text)

    # Запоминаем, для чего нам token
    await state.update_data(last_state='commands')
    await ask_for_token(chat_id, state)


# Проверка и сохранение нового названия бота/чата/канала
@dp.message(StateFilter(MyState.edit_description))
async def handle_desc_input(message: types.Message, state: FSMContext):
    """

    :param message:
    :param state:
    :return:
    """
    chat_id = message.chat.id
    text = message.text.strip()
    data = await state.get_data()

    if not (1 <= len(text) <= 512):
        await bot.delete_message(chat_id, message.message_id)
        await bot.delete_message(chat_id, data.get("form_message"))
        await ask_for_desc(None, state, chat_id, symbol_limit(512))
        return

    # Успешно! Дальше просим токен

    last_bot_msg = data.get("message_id")

    await bot.delete_message(chat_id, last_bot_msg)
    await bot.delete_message(chat_id, message.message_id)

    await state.update_data(desc=text)

    # Запоминаем, для чего нам token
    await state.update_data(last_state='desc')
    await ask_for_token(chat_id, state)


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
    current_state = await state.get_state()

    if current_state == MyState.edit_name and not (1 <= len(text) <= 64):
        await bot.delete_message(chat_id, message.message_id)
        await bot.delete_message(chat_id, data.get("form_message"))
        await ask_for_name(None, state, chat_id, symbol_limit(64), current_state)
        return
    elif current_state == MyState.edit_name_chat_channel and not (1 <= len(text) <= 255):
        await bot.delete_message(chat_id, message.message_id)
        await bot.delete_message(chat_id, data.get("form_message"))
        await ask_for_name(None, state, chat_id, symbol_limit(255), current_state)
        return

    # Успешно! Дальше просим токен

    last_bot_msg = data.get("message_id")

    await bot.delete_message(chat_id, last_bot_msg)
    await bot.delete_message(chat_id, message.message_id)

    await state.update_data(name=text)

    # Запоминаем, для чего нам token
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
        await ask_for_chat_channel_id(chat_id, state, msg)
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

    last_state = data.get("last_state")

    await bot.delete_message(chat_id, data.get("message_id"))
    selected = user_selected_languages.get(chat_id, [])
    if len(selected) > 0:
        lang_addition = f' Для языков {", ".join(list(filter(lambda x: x[1] == lang, flag_buttons))[0][0] for lang in selected)}'
    else:
        lang_addition = ''

    if last_state == 'name':
        change_type = 'Название'
        changed_value = data.get("name")
        end_symb = 'о'
        task = asyncio.create_task(change_bot_data(token, changed_value, selected, type='name'))

    elif last_state == 'desc':
        change_type = 'Описание'
        changed_value = data.get("desc")
        end_symb = 'о'
        task = asyncio.create_task(change_bot_data(token, changed_value, selected, type='desc'))

    elif last_state == 'commands':
        change_type = 'Команды'
        changed_value = data.get("commands")
        end_symb = 'ы'
        task = asyncio.create_task(change_bot_data(token, changed_value, selected, type='commands'))

    # Ожидаем завершения задач
    result = await asyncio.gather(task)

    if result[0][0]:
        result_text = f"✅ Успех! {change_type} <a href='{result[0][1]}'>бота</a> обновлен{end_symb} на: {changed_value}" + lang_addition

    else:

        result_text = f"❌ Ошибка! Попробуйте ещё раз чуть позже. {result[0][1]}"
    keyboard = create_inline_keyboard([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
    user_selected_languages[chat_id] = []

    await bot.delete_message(chat_id, message.message_id)

    await bot.edit_message_text(chat_id=chat_id, message_id=data['main_message_id'], text=result_text,
                                parse_mode="html")

    sent_message = await bot.edit_message_reply_markup(chat_id=chat_id, message_id=data['main_message_id'],
                                                       reply_markup=keyboard)

    await state.update_data(message_id=sent_message.message_id)

    # Стираем id старого главного сообщения
    await state.update_data(main_message_id=None)
    await state.set_state(MyState.ended)

    await finish_action(chat_id)


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
