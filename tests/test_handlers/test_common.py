import pytest

from aiogram.types import Message, User as TgUser
from unittest.mock import AsyncMock

from handlers.common import cmd_start, cmd_help


@pytest.mark.asyncio
async def test_cmd_start():
    message = AsyncMock(spec=Message)
    message.from_user = TgUser(id=999, is_bot=False, first_name='Test')
    message.answer = AsyncMock()
    await cmd_start(message)
    message.answer.assert_called_with(
        'Привет! Я трекер привычек.\n'
        'Доступные команды:\n'
        '/add_habit – добавить новую привычку\n'
        '/my_habits – посмотреть мои привычки\n'
        '/set_timezone – установить часовой пояс\n'
        '/help – помощь'
    )


@pytest.mark.asyncio
async def test_cmd_help():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    await cmd_help(message)
    message.answer.assert_called_with(
        'Я помогаю внедрять полезные привычки.\n'
        'Чтобы добавить привычку – /add_habit\n'
        'Покажу ваши привычки – /my_habits\n'
        'Установить часовой пояс – /set_timezone'
    )
