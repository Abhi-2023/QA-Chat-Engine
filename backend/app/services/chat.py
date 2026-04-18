from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from backend.app.core.config import get_settings
import json
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.conversation import Message

settings = get_settings()
llm = ChatAnthropic(model="claude-sonnet-4-20250514", streaming=True, api_key=settings.ANTHROPIC_API_KEY)
SYSTEM_PROMPT = "You are Nexus AI a helpful multimodel assistant, Be concise, accurate & generate response step by step wherever need"


def format_history(messages: list[Message]) -> list:
    formatted_message = [SystemMessage(content=SYSTEM_PROMPT)]
    
    for msg in messages:
        if msg.role == 'user':
            formatted_message.append(HumanMessage(content=msg.content))
        elif msg.role == 'assistant':
            formatted_message.append(AIMessage(content=msg.content))
    
    return formatted_message

async def stream_chat_response(messages, conversation_id, db: AsyncSession):
    try:
        formatted = format_history(messages)
        full_response=""
        async for chunk in llm.astream(formatted):
            full_response += chunk.content
            yield f"data : {json.dumps({'type':'token', 'content':chunk.content})}\n\n"
            
        new_message = Message(
            conversation_id = conversation_id,
            content=full_response,
            role='assistant'
        )
        
        db.add(new_message)
        await db.commit()
        
        yield f"data : {json.dumps({'type':'done'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
