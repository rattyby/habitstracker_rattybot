from environs import Env
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_engine = None
_async_session_maker = None


def _get_env():
    env = Env()
    env.read_env()
    return env


def _get_engine():
    global _engine
    if _engine is None:
        env = _get_env()
        DB_HOST = env.str('DB_HOST')
        DB_PORT = env.str('DB_PORT')
        DB_USER = env.str('DB_USER')
        DB_PASSWORD = env.str('DB_PASSWORD')
        DB_NAME = env.str('DB_NAME')
        DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        _engine = create_async_engine(DATABASE_URL, future=True)
    return _engine


def get_async_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        engine = _get_engine()
        _async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    return _async_session_maker


def get_sync_database_url():
    """Возвращает синхронный URL для PostgreSQL (используется Alembic)"""
    env = _get_env()
    DB_HOST = env.str('DB_HOST')
    DB_PORT = env.str('DB_PORT')
    DB_USER = env.str('DB_USER')
    DB_PASSWORD = env.str('DB_PASSWORD')
    DB_NAME = env.str('DB_NAME')
    return f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


def get_engine():
    return _get_engine()
