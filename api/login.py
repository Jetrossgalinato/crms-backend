
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.auth_utils import verify_password, create_access_token
from database import SessionLocal, User

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Query user from database
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
