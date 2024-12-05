import traceback

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from aiogram.types import FSInputFile, BotCommand

from flags import flag_buttons


async def change_bot_data(token, data, selected, type=None):
    def extract_commands(commands_message):
        lines = commands_message.split("\n")

        commands = []
        for line in lines:
            command, description = line.split(" - ")
            commands.append(BotCommand(command=command, description=description))
        return commands

    try:
        async with Bot(token=token) as bot:
            bot_info = await bot.get_me()
            bot_link = f"https://t.me/{bot_info.username}"

            errors = []
            reason = 'unknown'
            if len(selected) > 0:
                for lang in selected:
                    try:
                        if type == 'name':
                            await bot.set_my_name(
                                name=data,
                                language_code=lang
                            )
                        elif type == 'desc':
                            await bot.set_my_description(
                                description=data,
                                language_code=lang
                            )
                    except TelegramRetryAfter:
                        errors.append(errors)
                        reason = 'wait'
                    except Exception:
                        errors.append(errors)
            else:
                if type == 'name':
                    await bot.set_my_name(
                        name=data,
                    )
                elif type == 'desc':
                    await bot.set_my_description(
                        description=data,
                    )
                elif type == 'commands':
                    await bot.set_my_commands(
                        commands=extract_commands(data),
                    )
            if len(errors) == 0:
                return True, bot_link
            elif 0 < len(errors) < len(selected):
                if reason == 'wait':
                    msg = f'Не удалось для: {", ".join(list(filter(lambda x: x[1] == lang, flag_buttons))[0][0] for lang in errors)}. Вам нужно подождать 24 часа, прежде чем снова менять имя этого бота'
                else:
                    msg = "Неизвестная ошибка"
                return True, msg
            else:
                return False, reason
    except TelegramRetryAfter:
        return False, "Вам нужно подождать 24 часа, прежде чем снова менять имя этого бота"
    except Exception:
        traceback.print_exc()
        return False, ""


async def change_bot_pic(token, file_path, chat_id):
    try:

        async with Bot(token=token) as bot:
            await bot.set_chat_photo(photo=FSInputFile(path=file_path), chat_id=chat_id)
            return True
    except TelegramRetryAfter:
        return False, "Вам нужно подождать 24 часа, прежде чем снова менять фото этого бота"
    except Exception:
        traceback.print_exc()
        return False, ""


async def is_bot_admin(bot, chat_id: int) -> bool:
    """
    Проверяет, является ли бот администратором указанного чата.
    """
    try:
        bot_info = await bot.get_me()
        chat_member = await bot.get_chat_member(chat_id, bot_info.id)
        return chat_member.status == "administrator"
    except Exception:
        return False


async def set_chat_name_direct(bot, chat_id, new_name):
    if not chat_id.isdigit():
        return False, "Некорректный ID! Формат: 123456789 или -100123456789\n\n"

    try:

        # Проверяем, является ли бот администратором в указанном чате
        if not await is_bot_admin(bot, chat_id):
            return False, "Я не администратор в указанном чате или у меня нет прав изменять информацию.\n\n"

        # Пытаемся изменить название
        await bot.set_chat_title(chat_id, new_name)
        return True, f"✅ Успех! Название чата с ID `{chat_id}` успешно изменено на: {new_name}"

    except ValueError:
        return False, "ID чата должен быть числом. Проверьте ввод.\n\n"
    except TelegramBadRequest:
        return False, f"Не удалось изменить название\n\n"
    except TelegramForbiddenError:
        return False, "У меня нет доступа к указанному чату. Убедитесь, что бот добавлен и является администратором.\n\n"
    except Exception:
        return False, f"Неизвестная ошибка\n\n"
