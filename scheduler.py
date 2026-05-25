import logging
import pytz

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, date, timezone
from sqlalchemy import select

from db import get_async_session_maker
from messages import PREMIUM_EXPIRED
from models import Habit, HabitLog, User


logger = logging.getLogger(__name__)

_bot = None
scheduler = AsyncIOScheduler()


def set_bot(bot_instance):
    """Устанавливает экземпляр бота для отправки сообщений"""
    global _bot
    _bot = bot_instance


async def _send_reminder_message(habit, user, log, is_second=False):
    """Отправляет сообщение-напоминание (первое или повторное)"""
    if _bot is None:
        logger.error('Bot instance not set in scheduler')
        return False

    if not habit or not habit.is_active:
        return False
    if not user:
        return False
    if not log or log.status != 'pending':
        return False
    if is_second and log.second_reminder_sent:
        return False

    text = (
        '🔔 Напоминаю ещё раз' if is_second else '🔔 Напоминание' +
        f': привычка "{habit.name}"\nВы сегодня уже выполнили?'
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Выполнено', callback_data=f'complete_{habit.id}_{log.id}')]
    ])

    await _bot.send_message(
        user.telegram_id,
        text,
        reply_markup=kb
    )

    if is_second:
        log.second_reminder_sent = True
    else:
        log.reminder_sent = True
        log.reminded_at = datetime.now(timezone.utc)

    return True


async def send_reminder(habit_id: int, log_id: int):
    """Отправляет напоминание пользователю"""
    maker = get_async_session_maker()
    async with maker() as session:
        habit = await session.get(Habit, habit_id)
        if habit:
            user = await session.get(User, habit.user_id)
        log = await session.get(HabitLog, log_id)

        if not await _send_reminder_message(habit, user, log):
            logger.warning(f'Failed to send reminder for habit {habit_id}')
            return

        logger.debug(f'Sent reminder for habit {habit_id}')

        # Планируем повторное напоминание
        if not (habit and log):
            logger.warning(f'Failed to schedule second reminder for habit {habit_id}')
            return
        scheduler.add_job(
            send_second_reminder,
            trigger='date',
            run_date=datetime.now(timezone.utc) + timedelta(minutes=30),
            args=[habit.id, log.id],
            id=f'second_habit_{habit.id}_date_{log.date.isoformat()}'
        )
        logger.debug(f'Scheduled second reminder for habit {habit.id} in 30 minutes')

        await session.commit()


# Добавить новую функцию
async def send_second_reminder(habit_id: int, log_id: int):
    """Отправляет повторное напоминание через 30 минут"""
    maker = get_async_session_maker()
    async with maker() as session:
        habit = await session.get(Habit, habit_id)
        if habit:
            user = await session.get(User, habit.user_id)
        log = await session.get(HabitLog, log_id)
        if not log:
            logger.warning(f'Failed to send second reminder for habit {habit_id}')
            return
        if log.status != 'pending' or log.second_reminder_sent:
            return

        await _send_reminder_message(habit, user, log, is_second=True)
        await session.commit()


async def schedule_daily_reminders():
    """Загружает активные привычки и планирует задачи на сегодня и будущие дни"""
    maker = get_async_session_maker()
    async with maker() as session:
        today = date.today()
        habits = await session.execute(
            select(Habit).where(
                Habit.is_active == True,
                Habit.end_date >= today
            )
        )
        habits = habits.scalars().all()

        for habit in habits:
            user = await session.get(User, habit.user_id)
            if not user or not user.timezone:
                continue
            tz = pytz.timezone(user.timezone)
            current = max(habit.start_date, today)
            while current <= habit.end_date:
                log = await session.execute(
                    select(HabitLog).where(
                        HabitLog.habit_id == habit.id,
                        HabitLog.date == current
                    )
                )
                log = log.scalar_one_or_none()
                if log and log.status == 'pending' and not log.reminder_sent:
                    # Комбинируем дату и время
                    reminder_dt = datetime.combine(current, habit.reminder_time)
                    # Локализуем в часовом поясе пользователя и переводим в UTC
                    local_dt = tz.localize(reminder_dt)
                    utc_dt = local_dt.astimezone(pytz.UTC)
                    now_utc = datetime.now(timezone.utc)
                    if utc_dt > now_utc:
                        scheduler.add_job(
                            send_reminder,
                            trigger='date',
                            run_date=utc_dt,
                            args=[habit.id, log.id],
                            id=f'habit_{habit.id}_date_{current.isoformat()}'
                        )
                        logger.info(f'Scheduled reminder for habit {habit.id} on {current} at {habit.reminder_time}')
                current += timedelta(days=1)


async def expire_premium():
    """Проверяет пользователей, у которых истёк премиум, и уведомляет их."""
    if _bot is None:
        return

    maker = get_async_session_maker()
    async with maker() as session:
        now = datetime.now(timezone.utc)
        users_to_expire = await session.execute(
            select(User).where(User.premium_until < now, User.premium_until != None)
        )
        users = users_to_expire.scalars().all()

        for user in users:
            # Убираем премиум-статус
            user.is_premium = False
            await session.commit()
            try:
                await _bot.send_message(
                    user.telegram_id,
                    PREMIUM_EXPIRED
                )
                logger.info(f'Premium expired for user {user.telegram_id}')
            except Exception as e:
                logger.error(f'Failed to notify premium expiry for user {user.telegram_id}: {e}')


def init_scheduler():
    """Запускает планировщик и регистрирует ежедневную синхронизацию"""
    scheduler.start()
    scheduler.add_job(
        schedule_daily_reminders,
        trigger=CronTrigger(hour=0, minute=0, timezone=pytz.UTC),
        id='daily_reminder_sync'
    )
    scheduler.add_job(
        expire_premium,
        trigger=CronTrigger(hour=0, minute=1, timezone=pytz.UTC),
        id='expire_premium'
    )
    # Планируем задачи на сегодня (асинхронно, не блокируя запуск бота)
    import asyncio
    asyncio.create_task(schedule_daily_reminders())
