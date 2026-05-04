import os
import pytest

@pytest.fixture(autouse=True)
def set_env():
    """Устанавливает все переменные окружения, нужные для импорта бота и БД"""
    os.environ['BOT_TOKEN'] = '1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_PORT'] = '5432'
    os.environ['DB_USER'] = 'test_user'
    os.environ['DB_PASSWORD'] = 'test_pass'
    os.environ['DB_NAME'] = 'test_db'
