import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
from sqlalchemy import select

from db import get_async_session_maker
from messages import HELP_MESSAGE, PREMIUM_ACTIVE, PREMIUM_NOT_ACTIVE, START_MESSAGE, TIMEZONE_PROMPT, USER_NOT_REGISTERED
from models import User
from services.manage_user import get_or_create_user


logger = logging.getLogger(__name__)
router = Router()


COMMON_TIMEZONES = [
    'Europe/London',
    'Europe/Minsk',
    'Europe/Moscow',
    'Europe/Kiev',
    'Asia/Yekaterinburg',
    'Asia/Novosibirsk',
    'Asia/Vladivostok',
    'UTC'
]


@router.message(Command('start'))
async def cmd_start(message: Message):
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
async def cmd_help(message: Message):
    await message.answer(HELP_MESSAGE)


@router.message(Command('premium'))
async def cmd_premium(message: Message):
    if message.from_user is None:
        return

    maker = get_async_session_maker()
    async with maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(USER_NOT_REGISTERED)
            return

        if user.is_premium:
            now = datetime.now(timezone.utc)
            days_left = (user.premium_until.date() - now.date()).days
            await message.answer(PREMIUM_ACTIVE.format(days_left=days_left, premium_until=user.premium_until.date()))
        else:
            await message.answer(PREMIUM_NOT_ACTIVE)
        return


@router.message(Command('set_timezone'))
async def cmd_set_timezone(message: Message):
    """Начинаем процесс выбора часового пояса"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tz, callback_data=f'tz_{tz}')]
            for tz in COMMON_TIMEZONES
        ]
    )
    await message.answer(TIMEZONE_PROMPT, reply_markup=kb)
