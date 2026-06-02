import pytest

from aiogram.types import Message, User as TgUser
from datetime import date, datetime, timedelta, time, timezone
from unittest.mock import AsyncMock

from handlers.user_commands import cmd_premium
from messages import PREMIUM_ACTIVE, PREMIUM_NOT_ACTIVE, USER_NOT_REGISTERED
from models import User, Habit
from services.premium import check_habits_limit


@pytest.mark.asyncio
async def test_limit_free_user_under_limit(session):
    user = User(telegram_id=122, is_premium=False)
    session.add(user)
    await session.commit()

    # Одна активная привычка
    habit =  Habit(user_id=user.id, name='Test', start_date=date.today(), end_date=date.today() + timedelta(days=5), reminder_time=time(9, 0))
    session.add(habit)
    await session.commit()

    assert await check_habits_limit(user.id, session) is True


@pytest.mark.asyncio
async def test_limit_free_user_exactly_limit(session):
    user =  User(telegram_id=124, is_premium=False)
    session.add(user)
    await session.commit()
    for _ in range(2):
        h = Habit(user_id=user.id, name='Test', start_date=date.today(), end_date=date.today() + timedelta(days=5), reminder_time=time(9, 0))
        session.add(h)
    await session.commit()

    assert await check_habits_limit(user.id, session) is False  # лимит 2, уже 2


@pytest.mark.asyncio
async def test_limit_premium_user_no_limit(session):
    user = User(telegram_id=125, is_premium=True)
    session.add(user)
    await session.commit()
    for _ in range(5):
        h = Habit(user_id=user.id, name='Test', start_date=date.today(), end_date=date.today() + timedelta(days=5), reminder_time=time(9, 0))
        session.add(h)
    await session.commit()

    assert await check_habits_limit(user.id, session) is True


@pytest.mark.asyncio
async def test_premium_no_user():
    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=990, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_premium(message)
    message.answer.assert_called_with(USER_NOT_REGISTERED)


@pytest.mark.asyncio
async def test_premium_inactive(session):
    user = User(telegram_id=880, is_premium=False)
    session.add(user)
    await session.commit()
    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=880, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_premium(message)
    message.answer.assert_called_with(PREMIUM_NOT_ACTIVE)


@pytest.mark.asyncio
async def test_premium_active(session):
    expiry = datetime.now(timezone.utc) + timedelta(days=10)
    user = User(telegram_id=770, is_premium=True, premium_until=expiry)
    session.add(user)
    await session.commit()
    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=770, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_premium(message)
    args, _ = message.answer.call_args
    text = args[0]
    assert 'активен премиум' in text
    assert str(expiry.date()) in text
