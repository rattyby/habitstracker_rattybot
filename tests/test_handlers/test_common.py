import pytest

from aiogram.types import Message, User as TgUser
from unittest.mock import AsyncMock

from handlers.user_commands import cmd_start, cmd_help
from messages import HELP_MESSAGE, START_MESSAGE


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
