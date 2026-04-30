import logging

from aiogram import Router, types
from aiogram.filters import Command

router = Router()

logger = logging.getLogger(__name__)


@router.message(Command('start'))
async def cmd_start(message: types.Message):
    """Ответ на команду /start"""
    if message.from_user is None:
        logger.warning('Message has no from_user')
        return
    logger.info(f'User {message.from_user.id} started bot')
    await message.answer(
        'Привет! Я трекер привычек.\n'
        'Доступные команды:\n'
        '/add_habit – добавить новую привычку\n'
        '/my_habits – посмотреть мои привычки\n'
        '/help – помощь'
    )


@router.message(Command('add_habit'))
async def cmd_add_habit(message: types.Message):
    # Позже здесь будет FSM
    await message.answer('Функция добавления привычки в разработке. Скоро появится!')


@router.message(Command('my_habits'))
async def cmd_my_habits(message: types.Message):
    await message.answer('Список ваших привычек пока пуст. Добавьте первую через /add_habit')


@router.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(
        'Я помогаю внедрять полезные привычки.\n'
        'Чтобы добавить привычку – /add_habit\n'
        'Покажу ваши привычки – /my_habits'
    )
