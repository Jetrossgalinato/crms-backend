from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import SessionLocal, User
from api.auth_utils import SECRET_KEY, ALGORITHM

router = APIRouter()
security = HTTPBearer()

async def get_db():
    async with SessionLocal() as session:
        yield session

class AuthVerifyResponse(BaseModel):
    user: dict
    role: str

@router.get("/auth/verify", response_model=AuthVerifyResponse)
async def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify JWT token and return user information
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Get user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if user is approved
    if user.is_approved == 0:
        raise HTTPException(status_code=403, detail="Account pending approval")
    
    return AuthVerifyResponse(
        user={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "department": user.department,
            "phone_number": user.phone_number,
            "status": user.status,
        },
        role=user.acc_role
    )
