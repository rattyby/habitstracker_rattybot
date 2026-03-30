import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from environs import Env

# Загрузка переменных окружения
env = Env()
env.read_env()  # читает .env файл, если есть

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


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    """Ответ на команду /start"""
    logger.info(f'User {message.from_user.id} started bot')
    await message.answer(
        'Привет! Я трекер привычек. Пока я только учусь, но скоро буду полезным.'
    )


async def main():
    """Запуск поллинга"""
    logger.info('Starting bot polling...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())