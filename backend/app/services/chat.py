from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from backend.app.core.config import get_settings
import json, os, base64
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.conversation import Message, Conversation
from backend.app.models.documents import Document
from sqlalchemy import select, update
from backend.app.services.rag_services import retrieve_docs

settings = get_settings()
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514", streaming=True, api_key=settings.ANTHROPIC_API_KEY
)
SYSTEM_PROMPT = "You are Nexus AI a helpful multimodel assistant, Be concise, accurate & generate response step by step wherever need"
RAG_SYSTEM_PROMPT = """You are Nexus AI, a helpful assistant with access to uploaded documents.

When document context is provided below, follow these rules:
- Answer using the provided context
- Cite your sources as [filename, Page X] after each claim
- If the context doesn't contain the answer, say so clearly and answer from your general knowledge instead
- Do not make up information that isn't in the context

{context}"""


def load_image_as_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def format_history(messages: list[Message], system_prompt: str) -> list:
    formatted_message = [SystemMessage(content=system_prompt)]

    for msg in messages:
        if msg.role == "user":
            formatted_message.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            formatted_message.append(AIMessage(content=msg.content))

    return formatted_message


async def stream_chat_response(
    messages, conversation_id, user_id, file_ids, db: AsyncSession
):
    try:
        last_question = next(
            (msg.content for msg in reversed(messages) if msg.role == "user"), ""
        )
        if chunks := retrieve_docs(user_id, last_question):
            context = build_context(chunks)
            prompt = RAG_SYSTEM_PROMPT.format(context=context)
        else:
            prompt = SYSTEM_PROMPT

        formatted = format_history(messages, prompt)

        # Step 1 — Check if any file_ids were sent with this message
        if file_ids:
            image_blocks = []  # will collect image content blocks

            # Step 2 — Loop through each file_id, load from database
            for fid in file_ids:
                result = await db.execute(select(Document).where(Document.id == fid))
                doc = result.scalar_one_or_none()

                # Step 3 — Is this file an image? (not a PDF)
                if doc and doc.file_type in ("image/png", "image/jpeg"):

                    # Step 4 — Read the image file from disk and convert to base64
                    b64 = load_image_as_base64(doc.file_path)

                    # Step 5 — Build the image content block
                    image_blocks.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": doc.file_type,
                                "data": b64,
                            },
                        }
                    )

            # Step 6 — If we found any images, modify the last message
            if image_blocks:
                last_msg = (
                    formatted.pop()
                )  # removes: HumanMessage("What's in this image?")

                formatted.append(
                    HumanMessage(
                        content=[
                            *image_blocks,  # image block(s) first
                            {
                                "type": "text",
                                "text": last_msg.content,
                            },  # then the text question
                        ]
                    )
                )
                # Now the last message has both the image AND the text

        full_response = ""

        async for chunk in llm.astream(formatted):
            full_response += chunk.content
            yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

        new_message = Message(
            conversation_id=conversation_id, content=full_response, role="assistant"
        )

        db.add(new_message)
        # After db.add(new_message), update the conversation title
        if len(messages) <= 1:  # first message in conversation
            # Use first 50 chars of user's message as title
            first_msg = messages[0].content if messages else "New chat"
            title = first_msg[:50] + ("..." if len(first_msg) > 50 else "")

            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(title=title)
            )
        await db.commit()

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


def build_context(chunks: list[dict]) -> str:
    sections = []
    for chunk in chunks:
        section = f"[{chunk['filename']}, Page {chunk['page']}]\n{chunk['content']}"
        sections.append(section)

    return "\n---\n".join(sections)
