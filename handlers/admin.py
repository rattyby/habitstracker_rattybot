import logging
import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from db import get_async_session_maker
from models import User


logger = logging.getLogger(__name__)
router = Router()


def get_admin_ids() -> list[int]:
    """Возвращает список ID администраторов из переменной окружения ADMIN_IDS"""
    env_ids = os.getenv('ADMIN_IDS', '')
    if not env_ids:
        return []
    return [int(x.strip()) for x in env_ids.split(',') if x.strip().isdigit()]


def is_admin(user_id: int) -> bool:
    return user_id in get_admin_ids()


@router.message(Command('set_premium'))
async def cmd_set_premium(message: Message):
    """Устанавливает пользователю флаг is_premium = True"""
    if message.from_user is None or not is_admin(message.from_user.id) or not message.text:
        await message.answer('У вас нет прав для этой команды.')
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer('Использование: /set_premium <telegram_id> <days>')
        return

    try:
        target_id = int(args[1])
        days = int(args[2])
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer('ID и количество дней должны быть целыми положительными числами.')
        return

    maker = get_async_session_maker()
    async with maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == target_id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(f'Пользователь с ID {target_id} не найден.')
            return

        expiry_date = (datetime.now(timezone.utc) + timedelta(days=days)).date()
        new_expiry = datetime(expiry_date.year, expiry_date.month, expiry_date.day, 23, 59, 59, tzinfo=timezone.utc)
        user.premium_until = new_expiry
        user.is_premium = True
        await session.commit()
        await message.answer(f'Премиум для пользователя {target_id} продлён до {new_expiry.date()}.')
        logger.info(f'Admin {message.from_user.id} set premium for user {target_id} until {new_expiry.date()}')


@router.message(Command('set_loglevel'))
async def cmd_set_loglevel(message: Message):
    """Динамически меняет уровень логирования (для отладки)"""
    if message.from_user is None or not is_admin(message.from_user.id) or not message.text:
        await message.answer('У вас нет прав для этой команды.')
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer('Использование: /set_loglevel <DEBUG|INFO|WARNING|ERROR>')
        return

    level_name = args[1].upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        await message.answer('Неверный уровень. Допустимые: DEBUG, INFO, WARNING, ERROR')
        return

    # Меняем уровень у корневого логгера и основных логгеров
    logging.getLogger().setLevel(level)

    await message.answer(f'Уровень логирования изменён на {level_name}')
    logger.info(f'Admin {message.from_user.id} changed log level to {level_name}')
