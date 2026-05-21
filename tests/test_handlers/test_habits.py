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
