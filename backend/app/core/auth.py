from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from backend.app.core.config import get_settings
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.user import User
from backend.app.core.database import get_db

settings = get_settings()
security = HTTPBearer()
pwd_context = CryptContext(schemes=['bcrypt'])

def hash_password (password:str) -> str:
    return pwd_context.hash(password)

def verify_password(plain:str, hashed:str) ->bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id : str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {'sub':user_id, 'exp':expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token:str) -> str:
    try:
        if not (payload := jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])):
            raise HTTPException(
                status_code=400,
                detail='User does not exists, Please login'
            )
        return payload.get('sub')
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        ) from e
        
        
async def get_current_user(creds:HTTPAuthorizationCredentials = Depends(security), db:AsyncSession = Depends(get_db)):
    try:
        user_id = decode_token(creds.credentials)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        return user
    except Exception as e:
        raise