import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from environs import Env
from sqlalchemy import text

from db import engine
from handlers import routers
from scheduler import set_bot, init_scheduler

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

# Инициализация бота и диспетчера.
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
# Регистрация роутов
dp.include_routers(*routers)


async def on_startup():
    """Проверка подключения к БД при старте бота"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        logger.info('Database connection successful')
    except Exception as e:
        logger.error(f'Database connection failed: {e}')
        raise

    # Передача объекта Bot в планировщик и запуск задач.
    set_bot(bot)
    init_scheduler()
    logger.info('Scheduler initialized')


async def main():
    await on_startup()
    """Запуск поллинга"""
    logger.info('Starting bot polling...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
