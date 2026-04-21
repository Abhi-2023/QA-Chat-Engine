import uuid
from datetime import timezone, datetime
from sqlalchemy import String, Boolean, DateTime, func, ForeignKey, Text, JSON, Column, Integer
from sqlalchemy.orm import Mapped,mapped_column, relationship
from backend.app.core.database import Base


class Document(Base):
    __tablename__='documents'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:Mapped[str] = mapped_column(String(36),ForeignKey("users.id", ondelete='CASCADE'), index=True)
    filename:Mapped[str] = mapped_column(String(500))
    file_type:Mapped[str] = mapped_column(String(20))
    file_path:Mapped[str] = mapped_column(String(1000))
    file_hash:Mapped[str] = mapped_column(String(64), index=True)
    file_size:Mapped[int] = mapped_column(Integer)
    status:Mapped[str] = mapped_column(String(20))
    page_count:Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary:Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="documents")