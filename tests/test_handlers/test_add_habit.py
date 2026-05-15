import pytest

from aiogram.types import Message, User as TgUser
from datetime import date, timedelta, time
from unittest.mock import AsyncMock

from messages import HABIT_LIMIT_REACHED
from models import User, Habit
from handlers.add_habit import cmd_add_habit


@pytest.mark.asyncio
async def test_add_habit_limit_exceeded(session):
    user = User(telegram_id=555, is_premium=False)
    session.add(user)
    await session.commit()
    # Добавляем две активные привычки
    for _ in range(2):
        h = Habit(user_id=user.id, name='Test', start_date=date.today(), end_date=date.today() + timedelta(days=1), reminder_time=time(9, 0))
        session.add(h)
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=555, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    state = AsyncMock()
    await cmd_add_habit(message, state)

    message.answer.assert_called_with(HABIT_LIMIT_REACHED)
    state.set_state.assert_not_called()
