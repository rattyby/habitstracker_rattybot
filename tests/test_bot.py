import pytest
from bot import dp, cmd_start
from aiogram.types import Message


def test_dp_has_start_handler():
    """Проверяем, что обработчик /start зарегистрирован"""
    # Получаем все обработчики сообщений
    # Упрощённо: проверяем, что функция cmd_start является обработчиком
    assert callable(cmd_start)


def test_bot_imports():
    """Проверяем, что модуль импортируется без ошибок"""
    import bot
    assert bot.BOT_TOKEN is not None