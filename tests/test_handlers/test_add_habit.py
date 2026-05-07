import pytest

from aiogram.types import Message, User as TgUser
from datetime import date, timedelta
from unittest.mock import AsyncMock

from factories import UserFactory, HabitFactory
from handlers.add_habit import cmd_add_habit


@pytest.mark.asyncio
async def test_add_habit_limit_exceeded(session):
    user = UserFactory(telegram_id=555, is_premium=False)
    session.add(user)
    await session.commit()
    # Добавляем две активные привычки
    for _ in range(2):
        h = HabitFactory(user_id=user.id, end_date=date.today() + timedelta(days=1))
        session.add(h)
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=555, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    state = AsyncMock()
    await cmd_add_habit(message, state)

    message.answer.assert_called_with('У вас достигнут лимит активных привычек (2 для бесплатного тарифа). Чтобы добавить новую, приобретите премиум.')
    state.set_state.assert_not_called()
