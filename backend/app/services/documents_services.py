import fitz
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.app.core.chroma import get_chroma_collection
from backend.app.services.embedding_service import embed_batch
# from backend.app.services.video_services import process_video
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.documents import Document

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap = 50
)

collection = get_chroma_collection()

async def process_files(file_id: str,  user_id:str, file_type:str, db:AsyncSession ):
    if file_type == 'application/pdf':
        await process_documents(file_id=file_id, user_id= user_id, db= db)
    elif file_type in {'image/jpeg', 'image/png', 'image/jpg'}:
        await process_image(file_id, user_id, db)
    # else :
    #     process_video(file_id, user_id, db)
        

async def process_image(file_id: str, user_id: str, db: AsyncSession):
    result = await db.execute(select(Document).where(Document.id == file_id, Document.user_id == user_id))
    if (image := result.scalar_one_or_none()):
        image.status = 'ready'
        await db.commit()
        

async def process_documents(file_id:str, user_id:str, db:AsyncSession):
    doc_result = await db.execute(select(Document).where(Document.id == file_id, Document.user_id == user_id))
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        return
    try:
        file_path = doc.file_path
        file_name = doc.filename
        
        doc.status = "Processing"
        await db.commit()
        
        # # processing file details & chunking
        extracted_text = extract_text(file_path=file_path)
        page_count = get_page_count(file_path)
        
        doc.page_count = page_count
        
        chunked_text = chunk_text(extracted_text)
        if not chunked_text :
            doc.status= "failed"
            await db.commit()
            return
        
        text = [c['text'] for c in chunked_text]
        
        ## Converting the chunks into vector
        vector_embedded = embed_batch(text)
        
        ## Creating lists for all pages to store in vector db
        ids = [f"{file_id}_chunk_{chunk['chunk_index']}" for chunk in  chunked_text]
        documents = [chunk['text'] for chunk in chunked_text]
        metadatas = []
        for chunk in chunked_text:
            page = chunk['page']
            chunk_index = chunk['chunk_index']
            metadatas.append({
                "file_id": file_id,
                "user_id":user_id,
                "page" : page,
                "chunk_index" : chunk_index,
                "filename" : file_name
            })
            
        ## Add the details to vector db
        collection.add(ids=ids, documents=documents, embeddings=vector_embedded, metadatas=metadatas)
        doc.status='ready'
        await db.commit()
    except Exception as e:
        doc.status='failed'
        await db.commit()
        print(f'Document Processing failed : {e}')
    
def extract_text(file_path: str)-> list[dict]:
    doc = fitz.open(file_path)
    pages_dict_list = []
    try :
        for page in doc:
            text = page.get_text().strip()
            if text is None or len(text) < 50:
                continue
            text = re.sub(r"\x00", "", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            
            pages_dict_list.append(
                {"page": page.number+1,
                "text": text}
                )
        return pages_dict_list
    finally:
        doc.close() 
    

def get_page_count(file_path:str) -> int:
    doc = fitz.open(file_path)
    try:
        return doc.page_count
    finally:
        doc.close()
        
def chunk_text(pages : list[dict])-> list[dict]:
    chunk_list=[]
    chunk_counter=0
    for content in pages:
        text = content.get('text')
        page_number = content.get('page')
        chunks = splitter.split_text(text)
        for chunk in chunks:
            chunk_list.append({
                'text':chunk,
                'page':page_number,
                'chunk_index':chunk_counter
            })
            chunk_counter+=1
        
    return chunk_list