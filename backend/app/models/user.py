import uuid
from datetime import timezone, datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped,mapped_column, relationship
from backend.app.core.database import Base

class User(Base):
    __tablename__='users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    email:Mapped[str] = mapped_column(String(255),unique=True, index=True)
    hashed_password:Mapped[str]= mapped_column(String(255))
    full_name:Mapped[str] = mapped_column(String(100),default="")
    plan:Mapped[str] = mapped_column(String(20), default='free')
    is_active:Mapped[bool] = mapped_column(Boolean, default=True)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversations= relationship("Conversation", back_populates='user', cascade='all, delete-orphan')