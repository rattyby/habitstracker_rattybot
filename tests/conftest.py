import os
import pytest

@pytest.fixture(autouse=True)
def set_env():
    """Автоматически устанавливает BOT_TOKEN для всех тестов"""
    os.environ.setdefault('BOT_TOKEN', 'test_token')
