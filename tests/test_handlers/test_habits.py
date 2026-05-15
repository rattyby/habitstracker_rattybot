import pytest

from aiogram.types import Message, User as TgUser
from datetime import date, timedelta, time
from unittest.mock import AsyncMock

from messages import NO_HABITS_MESSAGE
from models import User, Habit
from handlers.habits import cmd_my_habits


@pytest.mark.asyncio
async def test_my_habits_no_habits(session):
    user = User(telegram_id=777)
    session.add(user)
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=777, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_my_habits(message)
    message.answer.assert_called_with(NO_HABITS_MESSAGE)


@pytest.mark.asyncio
async def test_my_habits_with_habits(session):
    user = User(telegram_id=888)
    session.add(user)
    await session.commit()

    habit1 = Habit(user_id=user.id, name='Зарядка', start_date=date.today(), end_date=date.today() + timedelta(days=10), reminder_time=time(9, 0), is_active=True)
    habit2 = Habit(user_id=user.id, name='Чтение', start_date=date.today(), end_date=date.today(), reminder_time=time(9, 0), is_active=False)
    session.add_all([habit1, habit2])
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=888, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_my_habits(message)

    # Проверяем, что в ответе есть названия
    args, _ = message.answer.call_args
    response_text = args[0]
    assert 'Зарядка' in response_text
    assert 'Чтение' in response_text
    assert '✅ Активна' in response_text
    assert '🔴 Завершена' in response_text
