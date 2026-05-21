import logging

from sqlalchemy import select

from models import User


logger = logging.getLogger(__name__)


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
