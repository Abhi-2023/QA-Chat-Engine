from backend.app.services.embedding_service import embed_text
from backend.app.core.chroma import get_chroma_collection

collections = get_chroma_collection()

def retrieve_docs(user_id: str, query : str, top_k : int=5) -> list[dict]:
    vector_query = embed_text(query)
    results = collections.query(query_embeddings=[vector_query], n_results=top_k, where={'user_id': user_id})
    if not results or not results['documents'][0]:
        return []
    return [
        {
            "content": doc,
            "page": meta.get('page'),
            "filename": meta.get('filename'),
            "chunk_index": meta.get('chunk_index'),
            "score": round(score, 4)
        }
        for doc, meta, score in zip(results['documents'][0], results['metadatas'][0], results['distances'][0])
    ]
