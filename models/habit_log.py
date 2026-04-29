from datetime import datetime, date
from sqlalchemy import ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class HabitLog(Base):
    __tablename__ = 'habit_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey('habits.id', ondelete='CASCADE'))
    date: Mapped[date]
    status: Mapped[str] = mapped_column(String(20), default='pending')  # pending, completed, missed
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    second_reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reminded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    habit: Mapped['Habit'] = relationship(back_populates='logs')
