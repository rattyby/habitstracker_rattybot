import pytest

from aiogram.types import Message, CallbackQuery, User as TgUser
from unittest.mock import AsyncMock

from models import User
from handlers.timezone import cmd_set_timezone, process_timezone_callback


@pytest.mark.asyncio
async def test_cmd_set_timezone():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    await cmd_set_timezone(message)
    message.answer.assert_called_with(
        'Выберите ваш часовой пояс (по городу):',
        reply_markup=pytest.approx({'inline_keyboard': [[{'text': 'UTC', 'callback_data': 'tz_UTC'}]]})
    )


@pytest.mark.asyncio
async def test_process_timezone_callback_existing_user(session):
    user = User(telegram_id=666, timezone='UTC')
    session.add(user)
    await session.commit()

    callback = AsyncMock(spec=CallbackQuery)
    callback.data = 'tz_Europe/Minsk'
    callback.from_user = TgUser(id=666, is_bot=False, first_name='Test')
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await process_timezone_callback(callback)

    # Проверим обновление в БД
    await session.refresh(user)
    assert user.timezone == 'Europe/Minsk'
    callback.message.edit_text.assert_called_with('Часовой пояс установлен: Europe/Minsk')
    callback.answer.assert_called_once()
