import asyncio
import pytest
import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from models import Base


# Используем in-memory SQLite для тестов
TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


# @pytest.fixture(autouse=True)
# def set_env():
#     """Устанавливает все переменные окружения, нужные для импорта бота и БД"""
#     os.environ['BOT_TOKEN'] = '1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw'
#     os.environ['DB_HOST'] = 'localhost'
#     os.environ['DB_PORT'] = '5432'
#     os.environ['DB_USER'] = 'test_user'
#     os.environ['DB_PASSWORD'] = 'test_pass'
#     os.environ['DB_NAME'] = 'test_db'


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='function')
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session

    await engine.dispose()
