from datetime import datetime, timedelta

from apscheduler.triggers.date import DateTrigger

from headers import bot, scheduler

# Словарь для хранения состояния действий пользователей
active_actions = {}


async def cancel_action(chat_id, message_id):
    """
    Действие по таймеру 10 минут: удалить форму ввода.
    """
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        pass


async def timeout_action(chat_id, message_id):
    """
    Действие по таймеру 47ч59м: изменить сообщение на 'Действие прервано'.
    """
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Действие прервано",
        )
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception as e:
        pass


async def collapse_menu(chat_id, message_id):
    """
    Свернуть кнопку 'Меню' по истечении 47ч59м.
    """
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception as e:
        pass


async def start_action(chat_id, main_message_id, form_message_id):
    """
    Запускает новое действие с таймерами.
    """

    # Сохраняем идентификатор действия
    active_actions[chat_id] = {
        "main_message_id": main_message_id,
        "form_message_id": form_message_id,
        "status": "active",
    }

    if form_message_id:
        # Запуск таймера на 10 минут для удаления формы ввода
        scheduler.add_job(
            cancel_action,
            # trigger=DateTrigger(run_date=datetime.now() + timedelta(minutes=10)),
            trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=10)),
            kwargs={"chat_id": chat_id, "message_id": form_message_id},
            id=f"cancel_form_{chat_id}",
            replace_existing=True,
        )

    # Запуск таймера на 47ч59м для изменения сообщения
    if main_message_id:
        scheduler.add_job(
            timeout_action,
            # trigger=DateTrigger(run_date=datetime.now() + timedelta(hours=47, minutes=59)),
            trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=20)),
            kwargs={"chat_id": chat_id, "message_id": main_message_id},
            id=f"timeout_action_{chat_id}",
            replace_existing=True,
        )

        # Запуск таймера на 47ч59м для сворачивания меню
        scheduler.add_job(
            collapse_menu,
            # trigger=DateTrigger(run_date=datetime.now() + timedelta(hours=47, minutes=59)),
            trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=20)),
            kwargs={"chat_id": chat_id, "message_id": main_message_id},
            id=f"collapse_menu_{chat_id}",
            replace_existing=True,
        )


async def finish_action(chat_id):
    """
    Завершает действие и сбрасывает таймеры.
    """

    if chat_id in active_actions and active_actions[chat_id]["status"] == "active":
        active_actions[chat_id]["status"] = "completed"

        # Удаление всех связанных таймеров
        scheduler.remove_job(f"cancel_form_{chat_id}")
        scheduler.remove_job(f"timeout_action_{chat_id}")
        # scheduler.remove_job(f"collapse_menu_{chat_id}")

        del active_actions[chat_id]
