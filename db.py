from environs import Env
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator

env = Env()
env.read_env()

# Формируем URL для asyncpg
DB_HOST = env.str('DB_HOST')
DB_PORT = env.str('DB_PORT')
DB_USER = env.str('DB_USER')
DB_PASSWORD = env.str('DB_PASSWORD')
DB_NAME = env.str('DB_NAME')

DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

DATABASE_URL_SYNC = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

_engine = create_async_engine(DATABASE_URL, echo=True)
_async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)


def get_async_session_maker():
    return _async_session_maker


async def get_session() -> AsyncGenerator:
    maker = get_async_session_maker()
    async with maker() as session:
        yield session
