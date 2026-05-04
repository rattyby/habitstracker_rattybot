from .common import router as common_router
from .add_habit import router as add_habit_router
from .timezone import router as timezone_router

__all__ = ['routers']

routers = [add_habit_router, timezone_router, common_router]
