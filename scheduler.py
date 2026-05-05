import logging
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, date, timezone
from sqlalchemy import select

from db import async_session_maker
from models import Habit, HabitLog, User


logger = logging.getLogger(__name__)

_bot = None
scheduler = AsyncIOScheduler()


def set_bot(bot_instance):
    """Устанавливает экземпляр бота для отправки сообщений"""
    global _bot
    _bot = bot_instance


async def send_reminder(habit_id: int, log_id: int, user_tz: str):
    """Отправляет напоминание пользователю"""
    if _bot is None:
        logger.error('Bot instance not set in scheduler')
        return

    async with async_session_maker() as session:
        habit = await session.get(Habit, habit_id)
        if not habit or not habit.is_active:
            return
        user = await session.get(User, habit.user_id)
        if not user:
            return
        log = await session.get(HabitLog, log_id)
        if not log or log.status != 'pending':
            return

        await _bot.send_message(
            user.telegram_id,
            f'🔔 Напоминание: привычка "{habit.name}"\n'
            f'Вы сегодня уже выполнили?'
        )
        log.reminder_sent = True
        log.reminded_at = datetime.now(timezone.utc)
        await session.commit()


async def schedule_daily_reminders():
    """Загружает активные привычки и планирует задачи на сегодня и будущие дни"""
    async with async_session_maker() as session:
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
                            args=[habit.id, log.id, user.timezone],
                            id=f'habit_{habit.id}_date_{current.isoformat()}'
                        )
                        logger.info(f'Scheduled reminder for habit {habit.id} on {current} at {habit.reminder_time} ({user.timezone})')
                current += timedelta(days=1)


def init_scheduler():
    """Запускает планировщик и регистрирует ежедневную синхронизацию"""
    scheduler.start()
    scheduler.add_job(
        schedule_daily_reminders,
        trigger=CronTrigger(hour=0, minute=0, timezone=pytz.UTC),
        id='daily_reminder_sync'
    )
    # Планируем задачи на сегодня (асинхронно, не блокируя запуск бота)
    import asyncio
    asyncio.create_task(schedule_daily_reminders())
