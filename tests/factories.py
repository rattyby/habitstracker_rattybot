from factory.alchemy import SQLAlchemyModelFactory
from factory.declarations import Sequence, SubFactory
from factory.faker import Faker
from datetime import date, time, timedelta

from models import User, Habit, HabitLog


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = 'flush'  # не commit, чтобы можно было откатить транзакцию

    telegram_id = Sequence(lambda n: 100000 + n)
    username = Faker('user_name')
    timezone = 'Europe/Minsk'
    is_premium = False


class HabitFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Habit

    user_id = SubFactory(UserFactory)
    name = Faker('word')
    start_date = date.today()
    end_date = date.today() + timedelta(days=7)
    reminder_time = time(9, 0)
    is_active = True
