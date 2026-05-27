import html
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, timedelta
from sqlalchemy import Integer, cast, select, func

from db import get_async_session_maker
from messages import NO_HABITS_MESSAGE, STATS_HEADER, STATS_MONTH, STATS_WEEK, USER_NOT_REGISTERED
from models import User, Habit, HabitLog


logger = logging.getLogger(__name__)
router = Router()


async def get_habits_display(telegram_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    """
    Возвращает (текст, клавиатуру) для списка привычек пользователя.
    """
    maker = get_async_session_maker()
    async with maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return USER_NOT_REGISTERED, None

        habits = await session.execute(
            select(Habit).where(Habit.user_id == user.id)
            .order_by(Habit.is_active.desc(), Habit.end_date.desc())
        )
        habits = habits.scalars().all()

        if not habits:
            return NO_HABITS_MESSAGE, None

        today = date.today()
        active_habits = [h for h in habits if h.is_active and h.end_date >= today]
        completed_habits = [h for h in habits if not h.is_active or h.end_date < today]

        lines = ['📋 Ваши привычки:\n']
        if active_habits:
            lines.append('<b>✅ Активные:</b>')
            for h in active_habits:
                escaped_name = html.escape(h.name)
                period = f'{h.start_date} – {h.end_date}'
                reminder = h.reminder_time.strftime('%H:%M')
                lines.append(f'• {escaped_name} | {reminder} | {period}')
        if completed_habits:
            lines.append('\n<b>🔴 Завершённые:</b>')
            for h in completed_habits[:5]:
                escaped_name = html.escape(h.name)
                lines.append(f'• {escaped_name} (до {h.end_date})')

        if active_habits:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f'❌ Завершить {html.escape(h.name)}', callback_data=f'stop_{h.id}')]
                for h in active_habits
            ])
        else:
            kb = None

        return '\n'.join(lines), kb


@router.message(Command('my_habits'))
async def cmd_my_habits(message: Message):
    """Показывает список привычек пользователя"""
    if message.from_user is None:
        logger.warning(f'Message {message} has no from_user')
        return

    text, kb = await get_habits_display(message.from_user.id)
    logger.debug(f'Response text: {text}')
    logger.debug(f'Keyboard: {kb}')
    await message.answer(text, reply_markup=kb, parse_mode='HTML')


@router.message(Command('stats'))
async def cmd_stats(message: Message):
    if message.from_user is None:
        logger.warning(f'Message {message} has no from_user')
        return

    maker = get_async_session_maker()
    async with maker() as session:
        user = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = user.scalar_one_or_none()
        if not user:
            await message.answer(USER_NOT_REGISTERED)
            return

        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Статистика за неделю
        week_result = await session.execute(
            select(
                func.count(HabitLog.id).label('total'),
                func.sum((HabitLog.status == 'completed').cast(Integer)).label('completed')
            ).where(
                HabitLog.habit.has(user_id=user.id),
                HabitLog.date >= week_ago
            )
        )
        week = week_result.one()
        week_total = week.total or 0
        week_completed = week.completed or 0
        week_percent = (week_completed / week_total * 100) if week_total else 0

        # Статистика за месяц
        month_result = await session.execute(
            select(
                func.count(HabitLog.id).label('total'),
                func.sum((HabitLog.status == 'completed').cast(Integer)).label('completed')
            ).where(
                HabitLog.habit.has(user_id=user.id),
                HabitLog.date >= month_ago
            )
        )
        month = month_result.one()
        month_total = month.total or 0
        month_completed = month.completed or 0
        month_percent = (month_completed / month_total * 100) if month_total else 0

        text = (
            STATS_HEADER
            + STATS_WEEK.format(completed=week_completed, total=week_total, percent=week_percent)
            + STATS_MONTH.format(completed=month_completed, total=month_total, percent=month_percent)
        )
        await message.answer(text, parse_mode='HTML')
