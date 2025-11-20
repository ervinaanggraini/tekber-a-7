from fastapi import APIRouter

from .health import router as health_router
from .login import router as login_router
from .logout import router as logout_router
from .users import router as users_router
from .financial_transactions import router as financial_transactions_router
from .chatbot import router as chatbot_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(users_router)
router.include_router(financial_transactions_router, prefix="/financial", tags=["financial-transactions"])
router.include_router(chatbot_router, prefix="/chat", tags=["chatbot"])
