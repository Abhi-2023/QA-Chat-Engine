# ⚡ Nexus AI

**A multimodal AI assistant with RAG-powered document analysis, image understanding, and real-time streaming chat.**

Built from scratch as a learning project — every line of backend code written by hand, every architectural decision understood and documented.

---

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4-D97706?logo=anthropic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F61)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)

---

## ✨ Features

**Chat with streaming** — Real-time token-by-token responses via Server-Sent Events (SSE). Claude generates, you see it live — just like ChatGPT.

**PDF analysis with RAG** — Upload any PDF. The system extracts text, chunks it semantically, embeds with local MiniLM, stores vectors in ChromaDB, and retrieves relevant context when you ask questions. Answers include `[filename, Page X]` citations.

**Image analysis** — Upload images for captioning, OCR, and visual QA. Powered by Claude Vision — the image bytes go directly to Claude, no preprocessing needed.

**Smart retrieval** — When you upload a file and ask a question, only chunks from THAT file are searched. General questions (no file attached) search across all your documents.

**Conversation management** — Create, rename, delete conversations. Full chat history persisted in PostgreSQL. JWT authentication with bcrypt password hashing.

---

## 🏗️ Architecture

```
┌─────────────┐     HTTP/SSE      ┌──────────────────────────────────┐
│   Browser    │◄────────────────► │         FastAPI Backend          │
│  (Jinja2 +   │                   │                                  │
│   Vanilla JS)│                   │  ┌──────────┐  ┌──────────────┐ │
└─────────────┘                   │  │ Auth API  │  │   Chat API   │ │
                                  │  └──────────┘  └──────┬───────┘ │
                                  │                       │         │
                                  │  ┌────────────────────▼──────┐  │
                                  │  │      Chat Service         │  │
                                  │  │  ┌─────────┐ ┌─────────┐ │  │
                                  │  │  │   RAG   │ │ Vision  │ │  │
                                  │  │  │ Service │ │ Service │ │  │
                                  │  │  └────┬────┘ └────┬────┘ │  │
                                  │  └───────┼───────────┼──────┘  │
                                  └──────────┼───────────┼─────────┘
                                             │           │
                          ┌──────────────────┼───────────┼──────────┐
                          │                  ▼           ▼          │
                          │  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
                          │  │ ChromaDB │ │  Claude   │ │PostgreSQL│ │
                          │  │ (vectors)│ │   API    │ │ (data)  │ │
                          │  └──────────┘ └──────────┘ └─────────┘ │
                          │                                        │
                          │  ┌──────────┐ ┌──────────┐             │
                          │  │  MiniLM  │ │ PyMuPDF  │             │
                          │  │(embeddings)│(PDF parse)│             │
                          │  └──────────┘ └──────────┘             │
                          └────────────────────────────────────────┘
```

---

## 🔧 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI + async SQLAlchemy | Async-first, auto-generated Swagger docs |
| **Database** | PostgreSQL 16 | Relational data — users, conversations, messages |
| **Vector Store** | ChromaDB | Document chunk storage + cosine similarity search |
| **LLM** | Claude Sonnet (via LangChain) | Chat, vision, and document QA |
| **Embeddings** | all-MiniLM-L6-v2 | Local, free, 384-dim vectors, runs on CPU |
| **PDF Parsing** | PyMuPDF | Fast text extraction with page-level granularity |
| **Auth** | JWT + bcrypt | Stateless authentication, secure password hashing |
| **Frontend** | Jinja2 + vanilla JS | Server-rendered templates, SSE streaming |
| **Containerization** | Docker + docker-compose | One-command local setup |

---

## 📁 Project Structure

```
nexus-ai/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI entry point, startup events
│       ├── core/
│       │   ├── config.py              # Pydantic settings from .env
│       │   ├── database.py            # Async SQLAlchemy engine + session
│       │   ├── auth.py                # JWT creation/verification, password hashing
│       │   └── chroma.py              # ChromaDB persistent client singleton
│       ├── api/
│       │   ├── auth.py                # POST /auth/register, /auth/login
│       │   ├── chat.py                # POST /chat/send (streaming), conversations CRUD
│       │   ├── files.py               # POST /file/upload with deduplication
│       │   └── pages.py               # Jinja2 template rendering
│       ├── models/
│       │   ├── user.py                # User table with UUID PK
│       │   ├── conversation.py        # Conversation + Message with cascade delete
│       │   └── documents.py           # Document metadata + processing status
│       └── services/
│           ├── chat.py                # LangChain + Claude streaming, RAG context injection
│           ├── document_service.py    # PDF extraction, chunking, processing pipeline
│           ├── embedding_service.py   # MiniLM sentence-transformers wrapper
│           └── rag_services.py        # ChromaDB vector search with user/file filtering
├── frontend/
│   ├── templates/index.html           # Single-page chat UI
│   └── static/
│       ├── css/style.css              # Chat bubbles, sidebar, dialogs
│       └── js/app.js                  # Auth, SSE streaming, file attachments
├── docker-compose.yml                 # PostgreSQL + Redis
├── Dockerfile                         # Production container
└── requirements.txt
```

---

## 🚀 Local Setup

**Prerequisites:** Python 3.10+, Docker Desktop

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/nexus-ai.git
cd nexus-ai
python -m venv venv && venv\Scripts\activate  # Windows
# source venv/bin/activate                    # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start databases
docker-compose up -d

# 4. Configure environment
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY

# 5. Run the app
uvicorn backend.app.main:app --port 8001
```

Open **http://localhost:8001** → Register → Start chatting.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT token |
| `GET` | `/auth/profile` | Current user info |
| `POST` | `/chat/send` | Send message + stream response (SSE) |
| `POST` | `/chat/conversations` | Create new conversation |
| `GET` | `/chat/conversations` | List all conversations |
| `GET` | `/chat/conversations/{id}/messages` | Get conversation history |
| `PATCH` | `/chat/conversations/{id}` | Rename conversation |
| `DELETE` | `/chat/conversations/{id}` | Delete conversation |
| `POST` | `/file/upload` | Upload PDF/image with SHA-256 dedup |

Full interactive docs at **http://localhost:8001/docs**

---

## 🧠 How RAG Works in This Project

```
1. UPLOAD: PDF → PyMuPDF extracts text → LangChain chunks (400 char, 50 overlap)
           → MiniLM embeds each chunk → ChromaDB stores vectors + metadata

2. QUERY:  User question → MiniLM embeds question → ChromaDB cosine search
           → Top 5 chunks retrieved (filtered by user_id + file_id)
           → Chunks injected into Claude's system prompt as context
           → Claude answers with [filename, Page X] citations

3. IMAGES: Uploaded image → base64 encoded → sent directly to Claude Vision
           → No RAG needed — Claude sees the pixels natively
```

---

## 🔮 Future Improvements

| Feature | Impact | Complexity |
|---------|--------|-----------|
| Cross-encoder reranking | +15% answer relevancy | Medium |
| HyDE query expansion | +10% recall on vague queries | Low |
| Hybrid search (BM25 + vector) | Better keyword matching | Medium |
| Semantic chunking | Fewer broken contexts | Medium |
| Celery background workers | Non-blocking file processing | Medium |
| WebSocket notifications | Real-time processing status | High |
| Evaluation suite (RAGAS) | Quantified retrieval quality | Medium |

---

## 📝 What I Learned Building This

- **Async Python** — SQLAlchemy async sessions, FastAPI streaming, generator pipelines
- **RAG architecture** — The full pipeline from text extraction to cited answers
- **Vector databases** — How embeddings work, cosine similarity, metadata filtering
- **LLM integration** — LangChain message types, system prompts, context injection
- **Auth systems** — JWT tokens, bcrypt hashing, dependency injection for route protection
- **System design** — Separating routes from services, file type routing, cascade deletes

---

## 📄 License

MIT — use it however you want.
