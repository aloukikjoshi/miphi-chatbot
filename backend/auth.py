import os, uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import User
from backend.schemas import UserRegister, UserLogin, TokenResponse, UserOut
from backend.logger import get_logger

load_dotenv()
logger = get_logger('miphi.auth')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'changeme-use-real-secret')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', '60'))
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
bearer_scheme = HTTPBearer()
router = APIRouter(prefix='/api/auth', tags=['auth'])

def hash_password(plain): return pwd_context.hash(plain)
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

def create_access_token(user_id, username):
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({'sub': str(user_id), 'username': username, 'exp': expire, 'iat': datetime.now(timezone.utc)}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: AsyncSession = Depends(get_db)) -> User:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('sub')
        if not user_id: raise exc
    except JWTError: raise exc
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active: raise exc
    return user

@router.post('/register', response_model=TokenResponse, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(User).where(User.username == payload.username))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail='Username already taken')
    if (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail='Email already registered')
    user = User(username=payload.username, email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user); await db.flush()
    logger.info('User registered', extra={'user_id': str(user.id), 'session_id': None, 'latency_ms': None, 'status_code': 201})
    return TokenResponse(access_token=create_access_token(user.id, user.username))

@router.post('/login', response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning('Failed login', extra={'user_id': None, 'session_id': None, 'latency_ms': None, 'status_code': 401})
        raise HTTPException(status_code=401, detail='Incorrect username or password')
    logger.info('User logged in', extra={'user_id': str(user.id), 'session_id': None, 'latency_ms': None, 'status_code': 200})
    return TokenResponse(access_token=create_access_token(user.id, user.username))

@router.get('/me', response_model=UserOut)
async def get_me(current_user: User = Depends(verify_token)):
    return current_user
