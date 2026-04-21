from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc, delete, update, func
from backend.app.core.config import get_settings
from backend.app.core.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.conversation import Conversation, Message
from backend.app.services.chat import stream_chat_response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/chat', tags=['chat'])
class ChatRequest(BaseModel):
    message : str
    conversation_id :str | None = None
    file_ids : list[str] | None = None
    
class RenameRequest(BaseModel):
    title:str
    

@router.post('/conversation')
async def new_conversation(user = Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    new_conversation = Conversation(
        user_id= user.id
    )
    db.add(new_conversation)
    await db.flush()
    
    await db.commit()
    return new_conversation.id

@router.post('/send')
async def send_stream_response(body: ChatRequest, user=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    conversation_id=''
    if body.conversation_id is None:
        new_convo = Conversation(user_id = user.id)
        db.add(new_convo)
        await db.flush()
        await db.commi()
        conversation_id=new_convo.id
    else :
        result = await db.execute(select(Conversation).where(Conversation.id == body.conversation_id, Conversation.user_id == user.id))
        
        convo = result.scalar_one_or_none()
        if convo is None:
            raise HTTPException(status_code=404, detail="Conversation Not Found")
        conversation_id  = convo.id
        
    user_msg = Message(
        conversation_id= conversation_id,
        role='user',
        content =body.message
    )
    db.add(user_msg)
    await db.flush()
    await db.commit()
    
    result = await db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at).limit(20))
    history = result.scalars().all()
    await db.commit()
    return StreamingResponse(stream_chat_response(history,conversation_id, user.id, body.file_ids, db), media_type="text/event-stream")

@router.get("/conversations")
async def get_all_conversations(user=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    result = await db.execute(select(Conversation).where(Conversation.user_id == user.id).order_by(desc(Conversation.updated_at)))
    return result.scalars().all()

@router.get("/conversations/{id}/messages")
async def get_messages_by_conversation_id(id, user=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    result_convo = await db.execute(select(Conversation).where(Conversation.id == id, Conversation.user_id == user.id))
    verified_convo = result_convo.scalar_one_or_none()
    if verified_convo is None:
        raise HTTPException(status_code=404, detail="Conversation doesn't belong to user")
    result = await db.execute(select(Message).where(Message.conversation_id == id).order_by(Message.created_at))
    if (messages_history := result.scalars().all()):
        return messages_history
    else:
        raise HTTPException(status_code=404, detail="Message Not Found")
    
    
    
@router.delete('/conversations/{conversation_id}')
async def delete_conversation_by_id(conversation_id, user=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    result_convo = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    verified_convo = result_convo.scalar_one_or_none()
    if verified_convo is None:
        raise HTTPException(status_code=404, detail="Conversation not belong to user")
    await db.delete(verified_convo)
    await db.commit()
    return {'status': 'Conversation deleted Successfully'}

@router.patch("/conversations/{conversation_id}")
async def rename_conversation_by_id(conversation_id, body:RenameRequest, user=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    result_convo = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    verified_convo = result_convo.scalar_one_or_none()
    if verified_convo is None:
        raise HTTPException(status_code=404, detail="Conversation not belong to user")
    
    updated_result = await db.execute(update(Conversation).where(Conversation.id == conversation_id, Conversation.user_id ==user.id).values(title=body.title, updated_at=func.now()))
    await db.commit()
    return {'status': 'updated'}