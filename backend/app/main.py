from fastapi import FastAPI
from backend.app.core.config import get_settings
from backend.app.core.database import init_db
from backend.app.models.user import User
from backend.app.models.conversation import Conversation, Message
from backend.app.models.documents import Document
from backend.app.api.auth import router as auth_router
from backend.app.api.chat import router as chat_router
from backend.app.api.files import router as file_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.api_pages import router as pages_router

settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version='0.1.0',
    description='Multimodel AI assistant'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(pages_router)
app.include_router(file_router)

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