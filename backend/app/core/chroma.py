import chromadb
from backend.app.core.config import get_settings
from functools import lru_cache

settings = get_settings()
client = chromadb.PersistentClient(path=settings.CHROMA_DIR)

documents = client.get_or_create_collection(name='documents', metadata={'hnsw:space': 'cosine'})

@lru_cache
def get_chroma_collection() :
    return documents