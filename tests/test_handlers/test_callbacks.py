import pytest

from aiogram.types import CallbackQuery, User as TgUser, Message
from datetime import date, timedelta, time
from unittest.mock import AsyncMock

from handlers.callbacks import complete_habit
from messages import COMPLETION_CONFIRMATION
from models import User, Habit, HabitLog


@pytest.mark.asyncio
async def test_complete_habit(session):
    user = User(telegram_id=123)
    session.add(user)
    await session.commit()
    habit = Habit(user_id=user.id, name='Test', start_date=date.today(), end_date=date.today() + timedelta(days=1), reminder_time=time(9,0), is_active=True)
    session.add(habit)
    await session.commit()
    log = HabitLog(habit_id=habit.id, date=date.today(), status='pending')
    session.add(log)
    await session.commit()

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = f'complete_{habit.id}_{log.id}'
    callback.from_user = TgUser(id=123, is_bot=False, first_name='Test')
    callback.message = AsyncMock(spec=Message)
    callback.message.message_id = 1
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await complete_habit(callback)

    # Проверяем, что лог обновлён
    await session.refresh(log)
    assert log.status == 'completed'
    callback.message.edit_text.assert_called_once()
    args, _ = callback.message.edit_text.call_args
    assert args[0] == COMPLETION_CONFIRMATION.format(name=habit.name)
