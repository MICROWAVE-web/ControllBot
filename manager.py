import traceback

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import InputFile, FSInputFile

from flags import flag_buttons


async def change_bot_name(token, name, selected):
    try:
        async with Bot(token=token) as bot:
            errors = []
            reason = 'unknown'
            if len(selected) > 0:
                for lang in selected:
                    try:
                        await bot.set_my_name(
                            name=name,
                            language_code=lang
                        )
                    except TelegramRetryAfter:
                        errors.append(errors)
                        reason = 'wait'
                    except Exception:
                        errors.append(errors)
            else:
                await bot.set_my_name(name=name)
            if len(errors) == 0:
                return True, ""
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
        print(f"Ошибка с ботом {token}")
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
        print(f"Ошибка с ботом {token}")
        traceback.print_exc()
        return False, ""
