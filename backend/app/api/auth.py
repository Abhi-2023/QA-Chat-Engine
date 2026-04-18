from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.auth import create_access_token, decode_token, hash_password,verify_password, get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from fastapi import HTTPException

router = APIRouter(prefix="/auth", tags=['auth'])

class RegisterRequest(BaseModel):
    email : EmailStr
    password:str
    full_name:str=""
    
class LoginRequest(BaseModel):
    email : EmailStr
    password : str
    
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user_id : str
    email : str
    

@router.post('/register')
async def register_user(payload: RegisterRequest, db = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )
    
    user = User(
        email = payload.email,
        hashed_password = hash_password(password=payload.password),
        full_name=payload.full_name
    )
    
    db.add(user)
    
    await db.flush()
    
    token = create_access_token(user_id=user.id)
    await db.commit()
    
    return AuthResponse(
        access_token=token,
        token_type='bearer',
        user_id=user.id,
        email=user.email
    )
    
@router.post('/login')
async def login_user(payload: LoginRequest, db = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        if verify_password(payload.password, user.hashed_password) is False:
            raise HTTPException(
                status_code=401,
                detail="Password or email Id does not match"
            )
        token = create_access_token(user_id=user.id)        
        return AuthResponse(
            access_token=token,
            token_type='bearer',
            user_id=user.id,
            email=user.email
        )
    else :
        raise HTTPException(
            status_code = 401,
            detail="User does not exist, Please sign up"
        )
        
@router.get('/profile')
async def get_profile(user : User = Depends(get_current_user)):
    return {'email': user.email, 'plan': user.plan}