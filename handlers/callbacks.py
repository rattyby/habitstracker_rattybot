import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InaccessibleMessage
from datetime import datetime, timezone

from db import get_async_session_maker
from models import HabitLog


router = Router()
logger = logging.getLogger(__name__)


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
        log = await session.get(HabitLog, log_id)
        if not log or log.status != 'pending':
            await callback.answer('Это напоминание уже неактивно.')
            return
        log.status = 'completed'
        log.completed_at = datetime.now(timezone.utc)
        await session.commit()
        if not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(f'✅ Отлично! Привычка "{log.habit.name}" выполнена.')
        else:
            await callback.answer(f'✅ Отлично! Привычка "{log.habit.name}" выполнена.')
    await callback.answer()
