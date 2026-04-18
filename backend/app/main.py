from fastapi import FastAPI
from backend.app.core.config import get_settings
from backend.app.core.database import init_db
from backend.app.models.user import User
from backend.app.models.conversation import Conversation, Message
from backend.app.api.auth import router as auth_router
from backend.app.api.chat import router as chat_router

settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version='0.1.0',
    description='Multimodel AI assistant'
)

app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/health")
async def health_check():
    return {
        "status":"healthy",
        "app": settings.APP_NAME,
        "debug":settings.DEBUG
    }
    
@app.on_event('startup')
async def on_startup():
    await init_db()