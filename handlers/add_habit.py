import logging

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import timedelta, date, time
from sqlalchemy import select

from db import get_async_session_maker
from messages import (
    ASK_DURATION, ASK_END_DATE, ASK_NAME, ASK_PERIOD_TYPE, ASK_START_DATE, ASK_TIME,
    ERR_NAME_TOO_SHORT, ERR_NAME_TOO_LONG, PT_BTN1, PT_BTN2, ERR_PERIOD_TYPE,
    HABIT_ADD_ERROR, HABIT_ADDED_SUCCESS, HABIT_LIMIT_REACHED,
    ERR_START_DATE, ERR_END_DATE, ERR_PERIOD, ERR_PERIOD_TOO_LONG, ERR_TIME,
    TIMEZONE_PROMPT, USER_NOT_REGISTERED, ERR_HABIT_TRY_AGAIN
)
from models import Habit, HabitLog
from services.manage_user import get_or_create_user, set_user_timezone, COMMON_TIMEZONES
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
    waiting_for_timezone = State()


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
        user = await get_or_create_user(session, user_id)
        if not user:
            await message.answer(USER_NOT_REGISTERED)
            return
        if not await check_habits_limit(user.id, session):
            await message.answer(HABIT_LIMIT_REACHED)
            return

    await state.set_state(AddHabitStates.waiting_for_name)
    await message.answer(ASK_NAME)


@router.message(StateFilter(AddHabitStates.waiting_for_name))
async def process_name(message: Message, state: FSMContext):
    """Сохраняем название и спрашиваем тип периода"""
    if message.text is None:
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(ERR_NAME_TOO_SHORT)
        return
    if len(name) > 200:
        await message.answer(ERR_NAME_TOO_LONG)
        return

    await state.update_data(name=name)
    # Предлагаем выбрать тип периода: длительность или конкретные даты
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PT_BTN1)],
            [KeyboardButton(text=PT_BTN2)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(AddHabitStates.waiting_for_period_type)
    await message.answer(ASK_PERIOD_TYPE, reply_markup=kb)


@router.message(StateFilter(AddHabitStates.waiting_for_period_type))
async def process_period_type(message: Message, state: FSMContext):
    """Обрабатываем выбор типа периода"""
    choice = message.text
    if choice == PT_BTN1:
        await state.set_state(AddHabitStates.waiting_for_duration)
        await message.answer(ASK_DURATION, reply_markup=ReplyKeyboardRemove())
    elif choice == PT_BTN2:
        await state.set_state(AddHabitStates.waiting_for_start_date)
        await message.answer(ASK_START_DATE, reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(ERR_PERIOD_TYPE)


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
        await message.answer(ASK_DURATION)
        return

    start_date = date.today()
    end_date = start_date + timedelta(days=duration - 1)
    await state.update_data(start_date=start_date, end_date=end_date)
    await state.set_state(AddHabitStates.waiting_for_time)
    await message.answer(ASK_TIME)


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
        await message.answer(ERR_START_DATE)
        return
    await state.update_data(start_date=start_date)
    await state.set_state(AddHabitStates.waiting_for_end_date)
    await message.answer(ASK_END_DATE)


@router.message(StateFilter(AddHabitStates.waiting_for_end_date))
async def process_end_date(message: Message, state: FSMContext):
    """Парсим дату окончания"""
    try:
        if not message.text:
            raise ValueError
        end_date = date.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer(ERR_END_DATE)
        return

    data = await state.get_data()
    start_date = data['start_date']
    if end_date <= start_date:
        await message.answer(ERR_PERIOD)
        return

    if (end_date - start_date).days > 365:
        await message.answer(ERR_PERIOD_TOO_LONG)
        return

    await state.update_data(end_date=end_date)
    await state.set_state(AddHabitStates.waiting_for_time)
    await message.answer(ASK_TIME)


@router.message(StateFilter(AddHabitStates.waiting_for_time))
async def process_time(message: Message, state: FSMContext):
    """Парсим время"""
    try:
        if not message.text:
            raise ValueError
        reminder_time = time.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer(ERR_TIME)
        return
    await state.update_data(reminder_time=reminder_time.isoformat())

    maker = get_async_session_maker()
    async with maker() as session:
        if message.from_user is None:
            logger.warning(f'Message {message} has no from_user')
            return
        user = await get_or_create_user(session, message.from_user.id)
        if user and user.timezone:
            await _save_habit_from_state(message, state, session, user)
        else:
            await state.set_state(AddHabitStates.waiting_for_timezone)
            # Создаём reply-клавиатуру из списка COMMON_TIMEZONES
            kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=tz)] for tz in COMMON_TIMEZONES],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await message.answer(TIMEZONE_PROMPT, reply_markup=kb)


async def _save_habit_from_state(message: Message, state: FSMContext, session, user):
    """Вспомогательная функция сохранения привычки (вызывается после получения timezone или сразу)"""
    data = await state.get_data()
    name = data.get('name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    reminder_time_str = data.get('reminder_time')
    if not all([name, start_date, end_date, reminder_time_str]): # or not reminder_time_str or not start_date or not end_date:
        await message.answer(ERR_HABIT_TRY_AGAIN)
        await state.clear()
        return
    reminder_time = time.fromisoformat(reminder_time_str) # type: ignore

    habit = Habit(
        user_id=user.id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        reminder_time=reminder_time,
        is_active=True
    )
    session.add(habit)
    await session.commit()
    current = start_date
    while current <= end_date: # type: ignore
        log = HabitLog(habit_id=habit.id, date=current, status='pending')
        session.add(log)
        current += timedelta(days=1) # type: ignore
    await session.commit()

    await state.clear()
    await message.answer(
        HABIT_ADDED_SUCCESS.format(
            name=name,
            reminder_time=reminder_time.isoformat(),
            start_date=start_date.isoformat(), # type: ignore
            end_date=end_date.isoformat() # type: ignore
        ),
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(StateFilter(AddHabitStates.waiting_for_timezone))
async def process_timezone_text(message: Message, state: FSMContext):
    """Получаем часовой пояс"""
    if not message.text:
        await message.answer(TIMEZONE_PROMPT)
        return
    tz = message.text.strip()
    if tz not in COMMON_TIMEZONES:
        # Если ввели что-то не из списка – переспрашиваем
        await message.answer(TIMEZONE_PROMPT)
        return

    maker = get_async_session_maker()
    async with maker() as session:
        if message.from_user is None:
            logger.warning(f'Message {message} has no from_user')
            return
        success = await set_user_timezone(session, message.from_user.id, tz)
        if not success:
            await message.answer(HABIT_ADD_ERROR)
            await state.clear()
            return
        user = await get_or_create_user(session, message.from_user.id)
        await _save_habit_from_state(message, state, session, user)
