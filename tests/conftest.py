import asyncio
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from models import Base


# Используем in-memory SQLite для тестов
TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='function')
async def session_maker():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    await engine.dispose()


@pytest.fixture(autouse=True)
def patch_db_session_maker(monkeypatch, session_maker):
    from db import get_async_session_maker
    monkeypatch.setattr("db.get_async_session_maker", lambda: session_maker)
