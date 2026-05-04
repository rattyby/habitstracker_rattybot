from .common import router as common_router
from .add_habit import router as add_habit_router

__all__ = ['routers']

routers = [add_habit_router, common_router]
