from .start import router as start_router
from .appointment import router as appointment_router
from .admin import router as admin_router
from .callbacks import router as callbacks_router
from .main_menu import router as main_menu_router  # ← ДОБАВЬ ЭТУ СТРОКУ

__all__ = [
    'start_router',
    'appointment_router',
    'admin_router',
    'callbacks_router',
    'main_menu_router'  # ← ДОБАВЬ ЭТУ СТРОКУ
]