from .add_habit import router as add_habit_router
from .admin import router as admin_router
from .callbacks import router as callbacks_router
from .common import router as common_router
from .habits import router as habits_router
from .premium_info import router as premium_router
from .timezone import router as timezone_router

__all__ = ['routers']

routers = [admin_router, premium_router, add_habit_router, habits_router, timezone_router, callbacks_router, common_router]
