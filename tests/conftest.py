import os
import pytest

@pytest.fixture(autouse=True)
def set_env():
    """Устанавливает тестовый токен, проходящий валидацию aiogram"""
    os.environ['BOT_TOKEN'] = '1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw'
