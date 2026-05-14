import pytest

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


# Загружаем тестовые переменные окружения
load_dotenv('.env.test')


@pytest.fixture(scope='function')
async def session():
    from db import get_engine, get_async_session_maker
    from models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = get_async_session_maker()
    async with maker() as sess:
        yield sess
        await sess.rollback()
        await sess.close()
