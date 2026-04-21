from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, func
from backend.app.core.config import get_settings
from backend.app.core.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.documents import Document
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib, uuid, os

type_list = ["application/pdf", "image/png", "image/jpeg"]
router = APIRouter(prefix='/file', tags=['files'])
settings = get_settings()

@router.post('/upload')
async def file_upload(file: UploadFile = File(...), user=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    file_type = file.content_type
    if file_type not in type_list and not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Please upload pdf, image or video")
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=404, detail="Please upload file less than 50 MB")
    
    hasher = hashlib.sha256()
    
    while chunk := file.file.read(1024 * 1024):
        hasher.update(chunk)
        
    file_hash = hasher.hexdigest()
    
    result = await db.execute(select(Document).where(Document.file_hash == file_hash, Document.user_id == user.id))
    
    if file_existing := result.scalar_one_or_none():
        raise HTTPException(status_code=400,detail="File with this name already exists")
    
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)
    
    file.file.seek(0)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, 'wb') as f:
        while chunk := file.file.read(1024 * 1024):
            f.write(chunk)
            
    new_file = Document(
        user_id = user.id,
        status = 'Uploaded',
        filename = unique_name,
        file_type = file_type,
        file_path = file_path,
        file_hash = file_hash,
        file_size = file_size,
        created_at = func.now()
    )
    
    db.add(new_file)
    
    await db.flush()
    
    await db.commit()
    
    return {"file_id": new_file.id}
            
    
    