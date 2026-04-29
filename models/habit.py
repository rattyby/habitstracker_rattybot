from datetime import datetime, date, time
from sqlalchemy import ForeignKey, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Habit(Base):
    __tablename__ = 'habits'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date]
    end_date: Mapped[date]
    reminder_time: Mapped[time]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped['User'] = relationship('User', back_populates='habits')
    logs: Mapped[list['HabitLog']] = relationship('HabitLog', back_populates='habit', cascade='all, delete-orphan')
