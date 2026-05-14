import pytest

from aiogram.types import Message, CallbackQuery, User as TgUser
from unittest.mock import AsyncMock, ANY

from models import User
from handlers.timezone import cmd_set_timezone, process_timezone_callback


@pytest.mark.asyncio
async def test_cmd_set_timezone():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    await cmd_set_timezone(message)
    message.answer.assert_called_with(
        'Выберите ваш часовой пояс (по городу):',
        reply_markup=ANY
    )


@pytest.mark.asyncio
async def test_process_timezone_callback_existing_user(session):
    from db import get_async_session_maker

    user = User(telegram_id=666, timezone='UTC')
    session.add(user)
    await session.commit()
    await session.close()

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = 'tz_Europe/Minsk'
    callback.from_user = TgUser(id=666, is_bot=False, first_name='Test')
    callback.message = AsyncMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await process_timezone_callback(callback)

    # Проверим обновление в БД
    maker = get_async_session_maker()
    async with maker() as new_session:
        from sqlalchemy import select
        result = await new_session.execute(select(User).where(User.telegram_id == 666))
        new_user = result.scalar_one()
        assert new_user.timezone == 'Europe/Minsk'

    callback.message.edit_text.assert_called_with('Часовой пояс установлен: Europe/Minsk')
    callback.answer.assert_called_once()
