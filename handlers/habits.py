import html
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
                [InlineKeyboardButton(text=f'❌ Завершить {html.escape(h.name)}', callback_data=f'complete_habit_{h.id}')]
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
            try:
                if not isinstance(callback.message, InaccessibleMessage):
                    await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            return

        habit.is_active = False
        await session.commit()

    # Получаем обновлённый список привычек
    text, kb = await get_habits_display(callback.from_user.id)
    try:
        if not isinstance(callback.message, InaccessibleMessage):
            await callback.message.edit_text(text, reply_markup=kb, parse_mode='HTML')
            await callback.answer(HABIT_COMPLETED.format(habit.name))
    except Exception as e:
        # Если редактирование не удалось (старое сообщение, удалено и т.п.)
        logger.warning(f'Failed to edit message: {e}')
        await callback.answer(HABIT_COMPLETED.format(habit.name), show_alert=False)
