import pytest

from aiogram.types import Message, User as TgUser
from datetime import date, timedelta, time
from unittest.mock import AsyncMock

from messages import NO_HABITS_MESSAGE, STATS_HEADER, USER_NOT_REGISTERED
from models import User, Habit, HabitLog
from handlers.habits import cmd_my_habits, cmd_stats


@pytest.mark.asyncio
async def test_my_habits_no_habits(session):
    user = User(telegram_id=777)
    session.add(user)
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=777, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_my_habits(message)

    args, _ = message.answer.call_args
    assert args[0] == NO_HABITS_MESSAGE


@pytest.mark.asyncio
async def test_my_habits_with_habits(session):
    user = User(telegram_id=888)
    session.add(user)
    await session.commit()

    # Активная привычка (end_date в будущем)
    habit1 = Habit(
        user_id=user.id,
        name='Зарядка',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=10),
        reminder_time=time(9, 0),
        is_active=True
    )
    # Завершённая привычка (is_active=False)
    habit2 = Habit(
        user_id=user.id,
        name='Чтение',
        start_date=date.today(),
        end_date=date.today(),
        reminder_time=time(9, 0),
        is_active=False
    )
    # Просроченная активная привычка (end_date в прошлом)
    habit3 = Habit(
        user_id=user.id,
        name='Бег',
        start_date=date.today() - timedelta(days=20),
        end_date=date.today() - timedelta(days=1),
        reminder_time=time(8, 0),
        is_active=True   # Формально активна, но период истёк
    )
    session.add_all([habit1, habit2, habit3])
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=888, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_my_habits(message)

    args, kwargs = message.answer.call_args
    response_text = args[0]

    # Проверяем, что клавиатура передана (только для активных не просроченных)
    assert kwargs.get('reply_markup') is not None

    # Проверяем названия привычек
    assert 'Зарядка' in response_text
    assert 'Чтение' in response_text
    assert 'Бег' in response_text

    # Проверяем заголовки секций
    assert '<b>✅ Активные:</b>' in response_text
    assert '<b>🔴 Завершённые:</b>' in response_text

    # Убедимся, что просроченная привычка попала в завершённые
    # (В списке завершённых отображается как "Бег (до ...)")
    assert 'Бег' in response_text.split('<b>🔴 Завершённые:</b>')[1]


@pytest.mark.asyncio
async def test_stats_no_user(session):
    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=999, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_stats(message)
    message.answer.assert_called_with(USER_NOT_REGISTERED)


@pytest.mark.asyncio
async def test_stats_empty(session):
    user = User(telegram_id=889)
    session.add(user)
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=889, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_stats(message)
    args, kwargs = message.answer.call_args
    text = args[0]
    assert STATS_HEADER in text
    assert '0 из 0' in text
    assert '0.0%' in text


@pytest.mark.asyncio
async def test_stats_with_data(session):
    user = User(telegram_id=778)
    session.add(user)
    await session.commit()
    habit = Habit(user_id=user.id, name='Test', start_date=date.today() - timedelta(days=10), end_date=date.today() + timedelta(days=10), reminder_time=time(9,0), is_active=True)
    session.add(habit)
    await session.commit()
    # Создаём логи: 5 completed, 5 pending за последние 7 дней
    for i in range(7):
        log = HabitLog(habit_id=habit.id, date=date.today() - timedelta(days=i), status='completed' if i < 5 else 'pending')
        session.add(log)
    await session.commit()

    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=778, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_stats(message)
    args, kwargs = message.answer.call_args
    text = args[0]
    assert 'Выполнено: 5 из 7' in text
    assert '71.4%' in text
