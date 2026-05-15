import logging

from aiogram import Router, types
from aiogram.filters import Command

from messages import START_MESSAGE, HELP_MESSAGE

router = Router()

logger = logging.getLogger(__name__)


@router.message(Command('start'))
async def cmd_start(message: types.Message):
    """Ответ на команду /start"""
    if message.from_user is None:
        logger.warning('Message has no from_user')
        return
    logger.info(f'User {message.from_user.id} started bot')
    await message.answer(START_MESSAGE)


@router.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(HELP_MESSAGE)
