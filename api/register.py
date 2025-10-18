from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.auth_utils import get_password_hash
from database import SessionLocal, User

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

class RegisterRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    department: str
    phone_number: str
    password: str
    role: str

@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        department=request.department,
        phone_number=request.phone_number,
        role=request.role,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "message": "User registered successfully",
        "email": new_user.email,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name
    }
