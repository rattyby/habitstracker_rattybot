import pytest

def test_bot_import():
    import bot
    assert bot.BOT_TOKEN is not None
    assert len(bot.BOT_TOKEN) > 10
    assert bot.dp is not None

def test_start_handler_exists():
    import bot
    assert hasattr(bot, 'cmd_start')
    assert callable(bot.cmd_start)
