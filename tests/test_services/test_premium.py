import pytest

from datetime import date, timedelta, time

from models import User, Habit
from services.premium import check_habits_limit


@pytest.mark.asyncio
async def test_limit_free_user_under_limit(session):
    user = User(telegram_id=123, is_premium=False)
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
