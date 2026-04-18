from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase
from backend.app.core.config import get_settings
settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass


async def get_db():
    db = async_session()
    try:
        yield db
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise
    finally:
        await db.close()
        
async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    
        await conn.run_sync(Base.metadata.create_all)