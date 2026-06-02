import pytest

from aiogram.types import Message, CallbackQuery, User as TgUser
from unittest.mock import AsyncMock, ANY

from handlers.callbacks import process_timezone_callback
from handlers.user_commands import cmd_start, cmd_help, cmd_set_timezone
from messages import HELP_MESSAGE, START_MESSAGE, TIMEZONE_PROMPT, TIMEZONE_SET_SUCCESS
from models import User


@pytest.mark.asyncio
async def test_cmd_start():
    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=999, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_start(message)
    message.answer.assert_called_with(START_MESSAGE)


@pytest.mark.asyncio
async def test_cmd_help():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    await cmd_help(message)
    message.answer.assert_called_with(HELP_MESSAGE)


@pytest.mark.asyncio
async def test_cmd_set_timezone():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    await cmd_set_timezone(message)
    message.answer.assert_called_with(TIMEZONE_PROMPT, reply_markup=ANY
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

    callback.message.edit_text.assert_called_with(TIMEZONE_SET_SUCCESS.format(new_user.timezone))
    callback.answer.assert_called_once()
