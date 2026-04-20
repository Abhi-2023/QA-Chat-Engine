import uuid
from datetime import timezone, datetime
from sqlalchemy import String, Boolean, DateTime, func, ForeignKey, Text, JSON, Column
from sqlalchemy.orm import Mapped,mapped_column, relationship
from backend.app.core.database import Base

class Conversation(Base):
    
    __tablename__="conversations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:Mapped[str] = mapped_column(String(36),ForeignKey("users.id", ondelete='CASCADE'))
    title:Mapped[str] = mapped_column(String(255), default='New Chat')
    mode: Mapped[str] = mapped_column(String(20), default='chat')
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda : datetime.now(timezone.utc))
    
    messages = relationship("Message", back_populates='conversation', cascade='all, delete-orphan')
    user= relationship('User', back_populates='conversations')
    

class Message(Base):
    
    __tablename__='messages'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id:Mapped[str] = mapped_column(String(36), ForeignKey('conversations.id', ondelete='CASCADE'), index=True)
    role:Mapped[str] = mapped_column(String(20))
    content:Mapped[str] = mapped_column(Text)
    attachments:Mapped[list | None] = mapped_column(JSON, nullable=True)
    metadata_ :Mapped[dict | None] = mapped_column('metadata', JSON, nullable=True )
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversation = relationship("Conversation", back_populates='messages')

    