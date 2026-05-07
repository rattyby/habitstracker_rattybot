import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import date
from sqlalchemy import select

from db import get_async_session_maker
from models import User, Habit


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command('my_habits'))
async def cmd_my_habits(message: Message):
    """Показывает список привычек пользователя"""
    if message.from_user is None:
        logger.warning('Message has no from_user')
        return

    maker = get_async_session_maker()
    async with maker() as session:
        # Находим пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer('Вы не зарегистрированы. Напишите /start, чтобы начать.')
            return

        # Получаем привычки пользователя, сортируем: сначала активные, потом завершённые
        habits = await session.execute(
            select(Habit).where(Habit.user_id == user.id).order_by(Habit.is_active.desc(), Habit.end_date)
        )
        habits = habits.scalars().all()

        if not habits:
            await message.answer('У вас пока нет привычек. Добавьте первую через /add_habit.')
            return

        # Формируем сообщение
        lines = ['📋 Ваши привычки:\n']
        today = date.today()
        for h in habits:
            status = '✅ Активна' if h.is_active and h.end_date >= today else '🔴 Завершена'
            period = f'{h.start_date} – {h.end_date}'
            reminder = h.reminder_time.strftime('%H:%M')
            lines.append(
                f'• {h.name}\n'
                f'  Статус: {status}\n'
                f'  Период: {period}\n'
                f'  Напоминание: {reminder}\n'
            )
        await message.answer('\n'.join(lines))
