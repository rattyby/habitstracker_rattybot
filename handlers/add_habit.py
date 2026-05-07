import logging

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import timedelta, date, time
from sqlalchemy import select

from db import get_async_session_maker
from models import User, Habit, HabitLog
from services.premium import check_habits_limit


logger = logging.getLogger(__name__)

router = Router()


class AddHabitStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_period_type = State()   # 'duration' or 'dates'
    waiting_for_duration = State()      # количество дней
    waiting_for_start_date = State()    # если выбран вариант с датами
    waiting_for_end_date = State()
    waiting_for_time = State()


@router.message(Command('add_habit'))
async def cmd_add_habit(message: Message, state: FSMContext):
    """Начинаем процесс добавления привычки"""
    # Проверяем лимит активных привычек
    maker = get_async_session_maker()
    async with maker() as session:
        if not message.from_user is None:
            user_id = message.from_user.id
        else:
            user_id = message.chat.id
        # Находим или создаём пользователя в БД по telegram_id
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=user_id)
            session.add(user)
            await session.commit()

        if not await check_habits_limit(user.id, session):
            await message.answer('У вас достигнут лимит активных привычек (2 для бесплатного тарифа). Чтобы добавить новую, приобретите премиум.')
            return

    await state.set_state(AddHabitStates.waiting_for_name)
    await message.answer('Введите название привычки (например, "Утренняя зарядка"):')


@router.message(StateFilter(AddHabitStates.waiting_for_name))
async def process_name(message: Message, state: FSMContext):
    """Сохраняем название и спрашиваем тип периода"""
    if message.text is None:
        return
    name = message.text.strip()
    if len(name) < 3:
        await message.answer('Название слишком короткое. Придумайте что-то осмысленнее (минимум 3 символа).')
        return
    if len(name) > 200:
        await message.answer('Название слишком длинное. Уложитесь в 200 символов.')
        return

    await state.update_data(name=name)
    # Предлагаем выбрать тип периода: длительность или конкретные даты
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='На определённое количество дней')],
            [KeyboardButton(text='Выбрать даты начала и окончания')]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(AddHabitStates.waiting_for_period_type)
    await message.answer(
        'Как вы хотите задать период привычки?',
        reply_markup=kb
    )


@router.message(StateFilter(AddHabitStates.waiting_for_period_type))
async def process_period_type(message: Message, state: FSMContext):
    """Обрабатываем выбор типа периода"""
    choice = message.text
    if choice == 'На определённое количество дней':
        await state.set_state(AddHabitStates.waiting_for_duration)
        await message.answer(
            'Введите количество дней (от 1 до 365):',
            reply_markup=ReplyKeyboardRemove()
        )
    elif choice == 'Выбрать даты начала и окончания':
        await state.set_state(AddHabitStates.waiting_for_start_date)
        await message.answer(
            'Введите дату начала в формате ГГГГ-ММ-ДД (например, 2025-12-31):',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer('Пожалуйста, выберите вариант из предложенных.')


@router.message(StateFilter(AddHabitStates.waiting_for_duration))
async def process_duration(message: Message, state: FSMContext):
    """Получаем длительность и вычисляем дату окончания"""
    try:
        if not message.text:
            raise ValueError
        duration = int(message.text.strip())
        if duration < 1 or duration > 365:
            raise ValueError
    except ValueError:
        await message.answer('Пожалуйста, введите целое число от 1 до 365.')
        return

    start_date = date.today()
    end_date = start_date + timedelta(days=duration - 1)
    await state.update_data(start_date=start_date, end_date=end_date)
    await state.set_state(AddHabitStates.waiting_for_time)
    await message.answer(
        f'Период: с {start_date.isoformat()} по {end_date.isoformat()} ({duration} дн.)\n'
        'Теперь введите время напоминания в формате ЧЧ:ММ (например, 09:00):'
    )


@router.message(StateFilter(AddHabitStates.waiting_for_start_date))
async def process_start_date(message: Message, state: FSMContext):
    """Парсим дату начала"""
    try:
        if not message.text:
            raise ValueError
        start_date = date.fromisoformat(message.text.strip())
        if start_date < date.today():
            raise ValueError
    except ValueError:
        await message.answer('Неверный формат или дата в прошлом. Введите дату в формате ГГГГ-ММ-ДД, начиная с сегодняшней:')
        return
    await state.update_data(start_date=start_date)
    await state.set_state(AddHabitStates.waiting_for_end_date)
    await message.answer('Введите дату окончания в формате ГГГГ-ММ-ДД:')


@router.message(StateFilter(AddHabitStates.waiting_for_end_date))
async def process_end_date(message: Message, state: FSMContext):
    """Парсим дату окончания"""
    try:
        if not message.text:
            raise ValueError
        end_date = date.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer('Неверный формат. Введите дату в формате ГГГГ-ММ-ДД:')
        return

    data = await state.get_data()
    start_date = data['start_date']
    if end_date <= start_date:
        await message.answer('Дата окончания должна быть позже даты начала.')
        return

    if (end_date - start_date).days > 365:
        await message.answer('Слишком длинный период (максимум 365 дней).')
        return

    await state.update_data(end_date=end_date)
    await state.set_state(AddHabitStates.waiting_for_time)
    await message.answer(
        f'Период: с {start_date.isoformat()} по {end_date.isoformat()}.\n'
        'Введите время напоминания в формате ЧЧ:ММ (например, 09:00):'
    )


@router.message(StateFilter(AddHabitStates.waiting_for_time))
async def process_time(message: Message, state: FSMContext):
    """Парсим время и сохраняем привычку в БД"""
    try:
        if not message.text:
            raise ValueError
        reminder_time = time.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer('Неверный формат времени. Используйте ЧЧ:ММ, например 09:00 или 18:30.')
        return

    data = await state.get_data()
    name = data['name']
    start_date = data['start_date']
    end_date = data['end_date']

    # Сохраняем в БД
    maker = get_async_session_maker()
    async with maker() as session:
        # Получаем пользователя по telegram_id (он уже должен быть создан при старте)
        if message.from_user is None:
            logger.warning('Message has no from_user')
            return
        user = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user.scalar_one()

        habit = Habit(
            user_id=user.id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            reminder_time=reminder_time,
            is_active=True
        )
        session.add(habit)
        await session.commit()  # чтобы получить habit.id
        # Создаём логи на каждый день периода
        current = start_date
        while current <= end_date:
            log = HabitLog(
                habit_id=habit.id,
                date=current,
                status='pending'
            )
            session.add(log)
            current += timedelta(days=1)
        await session.commit()

    await state.clear()
    await message.answer(
        f'Привычка "{name}" успешно добавлена!\n'
        f'Напоминания будут приходить каждый день в {reminder_time.isoformat()} (по вашему часовому поясу).\n'
        f'Период: с {start_date.isoformat()} по {end_date.isoformat()}.'
    )
