import pytest


def test_bot_import():
    import bot
    assert bot.BOT_TOKEN is not None
    assert len(bot.BOT_TOKEN) > 10
    assert bot.dp is not None


def test_router_import():
    from handlers.common import router
    assert router is not None

    from handlers.habits import router
    assert router is not None

    from handlers.add_habit import router
    assert router is not None

    from handlers.timezone import router
    assert router is not None
