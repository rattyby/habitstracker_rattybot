import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InaccessibleMessage, Message
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db import get_async_session_maker
from handlers.habits import get_habits_display
from messages import COMPLETION_CONFIRMATION, HABIT_ALREADY_COMPLETED, HABIT_COMPLETED_EARLY, HABIT_NOT_FOUND, REMINDER_INACIVE, USER_NOT_REGISTERED
from models import Habit, HabitLog, User
from scheduler import reschedule_user_reminders


logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith('stop_'))
async def stop_habit(callback: CallbackQuery):
    if callback.data is None or callback.from_user is None or callback.message is None:
        logger.warning(f'Callback {callback.data} has no data of from_user')
        return

    try:
        habit_id = int(callback.data.split('_')[1])
    except ValueError:
        logger.warning(f'Callback {callback.data} has invalid identifier')
        await callback.answer('Неверный идентификатор.')
        return

    maker = get_async_session_maker()
    async with maker() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            logger.warning(f'Failed to complete habit {habit_id} via /my_habits')
            await callback.answer(HABIT_NOT_FOUND)
            return
        if not habit.is_active:
            await callback.answer(HABIT_ALREADY_COMPLETED)
            return

        habit.is_active = False
        await session.commit()

    # Перепланируем напоминания пользователя (удаляем задачи для завершённой привычки)
    await reschedule_user_reminders(callback.from_user.id)

    # Обновляем сообщение со списком привычек
    new_text, new_kb = await get_habits_display(callback.from_user.id)
    try:
        if not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(new_text, reply_markup=new_kb, parse_mode='HTML')
        else:
            await callback.answer(HABIT_COMPLETED_EARLY.format(habit.name))
    except Exception as e:
        logger.error(f'Failed to edit message: {e}')
        await callback.answer(HABIT_COMPLETED_EARLY.format(habit.name))

    await callback.answer()


@router.callback_query(F.data.startswith('complete_'))
async def complete_habit(callback: CallbackQuery):
    if callback.data is None or callback.from_user is None or callback.message is None:
        logger.warning(f'Callback {callback.data} has no data of from_user')
        return

    _, habit_id, log_id = callback.data.split('_')
    try:
        habit_id = int(habit_id)
        log_id = int(log_id)
    except ValueError:
        logger.warning(f'Callback {callback.data} has invalid identifiers')
        await callback.answer('Неверные идентификаторы.')
        return

    maker = get_async_session_maker()
    async with maker() as session:
        log = await session.get(HabitLog, log_id, options=[selectinload(HabitLog.habit)])
        if not log or log.status != 'pending':
            await callback.answer(REMINDER_INACIVE)
            return

        # Дополнительно убедимся, что привычка существует
        habit = log.habit
        if not habit:
            await callback.answer(HABIT_NOT_FOUND)
            return

        log.status = 'completed'
        log.completed_at = datetime.now(timezone.utc)
        await session.commit()

        text = COMPLETION_CONFIRMATION.format(habit.name)
        try:
            if not isinstance(callback.message, InaccessibleMessage):
                await callback.message.edit_text(text)
            else:
                await callback.answer(text)
        except Exception as e:
            logger.error(f'Failed to edit message: {e}')
            await callback.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith('tz_'))
async def process_timezone_callback(callback: CallbackQuery):
    if callback.data is None or callback.from_user is None or callback.message is None:
        logger.warning('Callback has no data of from_user')
        return
    tz = callback.data[3:]  # убираем 'tz_'
    # Сохраняем в БД
    maker = get_async_session_maker()
    async with maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.timezone = tz
            await session.commit()
            if isinstance(callback.message, Message):
                await callback.message.edit_text(f'Часовой пояс установлен: {tz}')
            else:
                logger.error('Callback message is not a Message for user {}'.format(callback.from_user.id))
        else:
            if isinstance(callback.message, Message):
                await callback.message.edit_text(USER_NOT_REGISTERED)
            else:
                logger.error('Callback message is not a Message for user {}'.format(callback.from_user.id))
    await callback.answer()
