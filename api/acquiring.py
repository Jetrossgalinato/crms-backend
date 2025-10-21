from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, Acquiring, Supply, User
from datetime import datetime
from pydantic import BaseModel
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
from typing import Optional

router = APIRouter()

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"email": email}
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

class AcquiringRequest(BaseModel):
    acquirers_id: int
    supply_id: int
    quantity: int
    purpose: str = None

@router.post("/acquiring", status_code=201)
async def create_acquiring_request(
    request: AcquiringRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Create a new supply acquire request
    """
    try:
        # Validate quantity
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        # Verify supply exists and check available stock
        supply_result = await db.execute(
            select(Supply).where(Supply.supply_id == request.supply_id)
        )
        supply = supply_result.scalar_one_or_none()
        
        if not supply:
            raise HTTPException(status_code=404, detail="Supply not found")
        
        # Validate requested quantity against available stock
        if request.quantity > supply.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Requested quantity ({request.quantity}) exceeds available stock ({supply.quantity})"
            )
        
        # Verify user exists
        user_result = await db.execute(
            select(User).where(User.id == request.acquirers_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create new acquiring request
        new_request = Acquiring(
            acquirers_id=request.acquirers_id,
            supply_id=request.supply_id,
            quantity=request.quantity,
            purpose=request.purpose,
            status="Pending",
            created_at=datetime.utcnow()
        )
        
        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)
        
        return {
            "message": "Acquire request submitted successfully",
            "request_id": new_request.id,
            "status": new_request.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating acquire request: {str(e)}")
