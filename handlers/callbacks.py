import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InaccessibleMessage
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db import get_async_session_maker
from models import Habit, HabitLog


logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith('complete_'))
async def complete_habit(callback: CallbackQuery):
    if callback.data is None or callback.from_user is None or callback.message is None:
        logger.warning(f'Callback {callback.data} has no data of from_user')
        return
    _, habit_id, log_id = callback.data.split('_')
    habit_id = int(habit_id)
    log_id = int(log_id)

    maker = get_async_session_maker()
    async with maker() as session:
        log = await session.get(HabitLog, log_id, options=[selectinload(HabitLog.habit)])
        if not log or log.status != 'pending':
            await callback.answer('Это напоминание уже неактивно.')
            return

        # Дополнительно убедимся, что привычка существует
        habit = log.habit
        if not habit:
            await callback.answer('Привычка не найдена.')
            return

        log.status = 'completed'
        log.completed_at = datetime.now(timezone.utc)
        await session.commit()

        text = f'✅ Отлично! Привычка "{habit.name}" выполнена.'
        try:
            if not isinstance(callback.message, InaccessibleMessage):
                await callback.message.edit_text(text)
            else:
                await callback.answer(text)
        except Exception as e:
            logger.error(f'Failed to edit message: {e}')
            await callback.answer(text)
    await callback.answer()
