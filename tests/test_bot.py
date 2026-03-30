import bot
import pytest

def test_bot_import():
    """Проверяем, что модуль bot импортируется без ошибок"""
    assert bot.BOT_TOKEN == 'test_token'
    assert bot.dp is not None

def test_start_handler_exists():
    """Проверяем, что обработчик /start зарегистрирован"""
    # Получаем все обработчики сообщений (упрощённая проверка)
    handlers = bot.dp.message.handlers
    # Хотя бы один обработчик должен быть
    assert len(handlers) > 0