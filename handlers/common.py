import logging

from aiogram import Router, types
from aiogram.filters import Command

from db import get_async_session_maker
from messages import START_MESSAGE, HELP_MESSAGE
from services.manage_user import get_or_create_user


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command('start'))
async def cmd_start(message: types.Message):
    """Ответ на команду /start"""
    if message.from_user is None:
        logger.warning(f'Message {message} has no from_user')
        return

    logger.info(f'User {message.from_user.id} started bot')

    maker = get_async_session_maker()
    async with maker() as session:
        await get_or_create_user(session, message.from_user.id)
    await message.answer(START_MESSAGE)


@router.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(HELP_MESSAGE)
