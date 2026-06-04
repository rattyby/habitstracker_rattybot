import logging

from sqlalchemy import select

from models import User


logger = logging.getLogger(__name__)

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


async def get_or_create_user(session, telegram_id: int) -> User | None:
    """
    Проверяет существование пользователя в БД.
    Если не существует – создаёт нового.
    Возвращает объект User (или None, если не удалось).
    """
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        logger.info(f'New user registered: {telegram_id}')
    return user


async def set_user_timezone(session, telegram_id: int, timezone: str) -> bool:
    """Устанавливает часовой пояс пользователя. Возвращает True, если успешно."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f'User {telegram_id} not found while setting timezone')
        return False
    user.timezone = timezone
    await session.commit()
    logger.info(f'Timezone set for user {telegram_id}: {timezone}')
    return True
