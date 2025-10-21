from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import SessionLocal, User
from api.auth_utils import SECRET_KEY, ALGORITHM
from typing import Optional

router = APIRouter()
security = HTTPBearer(auto_error=False)

async def get_db():
    async with SessionLocal() as session:
        yield session

class AuthVerifyResponse(BaseModel):
    user_id: str
    email: str
    role: str
    user: dict

@router.get("/auth/verify", response_model=AuthVerifyResponse)
async def verify_auth(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify JWT token and return user information
    """
    # Check if Authorization header is present
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    # Get user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if user is approved
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval")
    
    return AuthVerifyResponse(
        user_id=str(user.id),  # At top level for easy access
        email=user.email,
        role=user.acc_role,
        user={
            "id": user.id,
            "user_id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "department": user.department,
            "phone_number": user.phone_number,
            "status": user.status,
        }
    )
