import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy import select

from db import get_async_session_maker
from models import User


logger = logging.getLogger(__name__)
router = Router()

# Список популярных часовых поясов (можно расширить)
COMMON_TIMEZONES = [
    'Europe/London',
    'Europe/Minsk',
    'Europe/Moscow',
    'Europe/Kiev',
    'Asia/Yekaterinburg',
    'Asia/Novosibirsk',
    'Asia/Vladivostok',
    'UTC'
]


@router.message(Command('set_timezone'))
async def cmd_set_timezone(message: Message):
    """Начинаем процесс выбора часового пояса"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tz, callback_data=f'tz_{tz}')]
            for tz in COMMON_TIMEZONES
        ]
    )
    await message.answer(
        'Выберите ваш часовой пояс (по городу):',
        reply_markup=kb
    )


@router.callback_query(F.data.startswith('tz_'))
async def process_timezone_callback(callback: CallbackQuery):
    if callback.data is None or callback.from_user is None or callback.message is None:
        logger.warning('Callback has no data of from_user')
        return
    tz = callback.data[3:]  # убираем 'tz_'
    # Сохраняем в БД
    maker = get_async_session_maker()
    async with maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.timezone = tz
            await session.commit()
            if isinstance(callback.message, Message):
                await callback.message.edit_text(f'Часовой пояс установлен: {tz}')
            else:
                logger.error('Callback message is not a Message for user {}'.format(callback.from_user.id))
        else:
            if isinstance(callback.message, Message):
                await callback.message.edit_text('Сначала используйте /start, чтобы зарегистрироваться.')
            else:
                logger.error('Callback message is not a Message for user {}'.format(callback.from_user.id))
    await callback.answer()
