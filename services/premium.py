from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Habit, User


async def check_habits_limit(user_id: int, session: AsyncSession) -> bool:
    """Проверяет, может ли пользователь добавить новую привычку. Бесплатный лимит: 2 активные привычки одновременно.
    true - можно добавить, false - нельзя.
    """
    # Для премиум-пользователей лимита нет
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    if user.is_premium:
        return True

    # Считаем активные привычки (is_active=True и end_date >= сегодня)
    today = date.today()
    count = await session.scalar(
        select(func.count(Habit.id)).where(
            Habit.user_id == user_id,
            Habit.is_active == True,
            Habit.end_date >= today
        )
    )
    return count is not None and count < 2
