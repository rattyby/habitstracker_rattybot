from .add_habit import router as add_habit_router
from .admin import router as admin_router
from .callbacks import router as callbacks_router
from .habits import router as habits_router
from .user_commands import router as user_commands_router

__all__ = ['routers']

routers = [admin_router, user_commands_router, add_habit_router, habits_router, callbacks_router]
