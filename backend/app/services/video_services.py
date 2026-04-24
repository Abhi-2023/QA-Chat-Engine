# from backend.app.core.config import get_settings
# import yt_dlp, uuid, os, whisper
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from  backend.app.models.documents import Document
# from backend.app.services.embedding_service import embed_batch
# from backend.app.core.chroma import get_chroma_collection
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# settings = get_settings()
# collection = get_chroma_collection()

# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=400,
#     chunk_overlap = 50
# )


# def download_audio(url: str, output_dir: str = settings.UPLOAD_DIR):
#     os.makedirs(output_dir, exist_ok=True)

#     file_id = str(uuid.uuid4())
#     output_template = f"{output_dir}/{file_id}.%(ext)s"

#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'outtmpl': output_template,
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#         }],
#     }

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)

#     # 🔹 Final file path (after conversion)
#     file_path = os.path.join(output_dir, f"{file_id}.mp3")
    
#     return {"file_path" : file_path}
 
 
# def transcribe_audio(file_path: str):
#     model = whisper.load_model(settings.WHISPER_MODEL)
#     result = model.transcribe(file_path)
#     return [
#         {
#             'start': seg['start'],
#             'end': seg['end'],
#             'text': seg['text'].strip()
#         }
#         for seg in result['segments']
#     ]
    
# async def process_video(file_id: str, user_id:str, db: AsyncSession):
#     doc_result = await db.execute(select(Document).where(Document.id == file_id, Document.user_id == user_id))
#     doc= doc_result.scalar_one_or_none()
#     if doc is None:
#         return
#     try :
#         file_path = doc.file_path
#         file_name = doc.filename
        
#         doc.status = "Processing"
#         await db.commit()
#         segments = transcribe_audio(file_path)
        
#         chunked_text = chunk_transcription(segments)
#         if not chunked_text :
#             doc.status= "failed"
#             await db.commit()
#             return
        
#         text = [c['text'] for c in chunked_text]
        
#         ## Converting the chunks into vector
#         vector_embedded = embed_batch(text)
        
#         ## Creating lists for all pages to store in vector db
#         ids = [f"{file_id}_chunk_{chunk['chunk_index']}" for chunk in  chunked_text]
#         documents = [chunk['text'] for chunk in chunked_text]
#         metadatas = []
#         for chunk in chunked_text:
#             start = chunk['start']
#             end = chunk['end']
#             chunk_index = chunk['chunk_index']
#             metadatas.append({
#                 "file_id": file_id,
#                 "user_id":user_id,
#                 "start" : start,
#                 "end" : end,
#                 "chunk_index" : chunk_index,
#                 "filename" : file_name
#             })
            
#         ## Add the details to vector db
#         collection.add(ids=ids, documents=documents, embeddings=vector_embedded, metadatas=metadatas)
#         doc.status='ready'
#         await db.commit()
#     except Exception as e :
#         doc.status='failed'
#         await db.commit()
#         print(f'Document Processing failed : {e}')

            
            
# def chunk_transcription(pages : list[dict])-> list[dict]:
#     chunk_list=[]
#     chunk_counter=0
#     for content in pages:
#         text = content.get('text')
#         start = content.get('start')
#         end = content.get('end')
#         chunks = splitter.split_text(text)
#         for chunk in chunks:
#             chunk_list.append({
#                 'text':chunk,
#                 'start':start,
#                 'end':end,
#                 'chunk_index':chunk_counter
#             })
#             chunk_counter+=1
        
#     return chunk_list