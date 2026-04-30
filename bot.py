import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from environs import Env
from sqlalchemy import text

from db import engine
from handlers.common import router as common_router

# Загрузка переменных окружения
env = Env()
env.read_env()  # читает .env файл

BOT_TOKEN = env.str('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='{asctime} {levelname:<8} {message:<30} - {name}:{funcName} {filename}:{lineno}',
    style='{',
    stream=sys.stdout,  # явно указываем stdout
)
logger = logging.getLogger(__name__)

# Уменьшаем количество логов от готовых библиотек.
logging.getLogger('aiogram').setLevel(logging.WARNING)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
# Регистрация роутов
dp.include_router(common_router)


async def on_startup():
    """Проверка подключения к БД при старте бота"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        logger.info('Database connection successful')
    except Exception as e:
        logger.error(f'Database connection failed: {e}')
        raise


async def main():
    await on_startup()
    """Запуск поллинга"""
    logger.info('Starting bot polling...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())