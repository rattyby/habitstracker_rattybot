import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime, timezone
from sqlalchemy import select

from db import get_async_session_maker
from messages import PREMIUM_ACTIVE, PREMIUM_NOT_ACTIVE, USER_NOT_REGISTERED
from models import User


logger = logging.getLogger(__name__)
router = Router()


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
            days_left = (user.premium_until - datetime.now(timezone.utc)).days
            await message.answer(PREMIUM_ACTIVE.format(days_left=days_left, premium_until=user.premium_until.date()))
        else:
            await message.answer(PREMIUM_NOT_ACTIVE)
        return
