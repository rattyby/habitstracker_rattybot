import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import InaccessibleMessage, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date
from sqlalchemy import select

from db import get_async_session_maker
from messages import HABIT_ALREADY_COMPLETED, HABIT_COMPLETED, NO_HABITS_MESSAGE, USER_NOT_REGISTERED
from models import User, Habit


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command('my_habits'))
async def cmd_my_habits(message: Message):
    """Показывает список привычек пользователя"""
    if message.from_user is None:
        logger.warning(f'Message {message} has no from_user')
        return

    maker = get_async_session_maker()
    async with maker() as session:
        # Находим пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(USER_NOT_REGISTERED)
            return

        # Получаем привычки пользователя, сортируем: сначала активные, потом завершённые
        habits = await session.execute(
            select(Habit).where(Habit.user_id == user.id).order_by(Habit.is_active.desc(), Habit.end_date.desc())
        )
        habits = habits.scalars().all()

        if not habits:
            await message.answer(NO_HABITS_MESSAGE)
            return

        # Формируем сообщение
        today = date.today()
        active_habits = [h for h in habits if h.is_active and h.end_date >= today]
        completed_habits = [h for h in habits if not h.is_active or h.end_date < today]

        lines = ['📋 Ваши привычки:\n']
        if active_habits:
            lines.append('✅ *Активные:*')
            for h in active_habits:
                period = f'{h.start_date} – {h.end_date}'
                reminder = h.reminder_time.strftime('%H:%M')
                lines.append(f'• {h.name} | {reminder} | {period}')
        if completed_habits:
            lines.append('\n🔴 *Завершённые:*')
            for h in completed_habits[:5]:  # последние 5
                lines.append(f'• {h.name} (до {h.end_date})')

        # Клавиатура для активных привычек
        if active_habits:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f'❌ Завершить {h.name}', callback_data=f'complete_habit_{h.id}')]
                for h in active_habits
            ])
        else:
            kb = None

        await message.answer('\n'.join(lines), reply_markup=kb, parse_mode='Markdown')


@router.callback_query(F.data.startswith('complete_habit_'))
async def complete_habit_early(callback: CallbackQuery):
    if callback.data is None or callback.from_user is None or callback.message is None:
        logger.warning(f'Callback {callback} has no data of from_user')
        return
    habit_id = int(callback.data.split('_')[2])
    maker = get_async_session_maker()
    async with maker() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            await callback.answer('Привычка не найдена.', show_alert=True)
            return
        if not habit.is_active:
            await callback.answer(HABIT_ALREADY_COMPLETED, show_alert=True)
            return
        habit.is_active = False
        await session.commit()
        if not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(HABIT_COMPLETED.format(habit.name), show_alert=True)
        else:
            await callback.answer(HABIT_COMPLETED.format(habit.name), show_alert=True)
    await callback.answer()
