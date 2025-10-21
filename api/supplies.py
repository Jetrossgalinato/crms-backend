from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, Supply, Facility, User
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
from typing import List, Optional

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

@router.get("/supplies")
async def get_supplies(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get all supplies with their current stock levels and facility information
    """
    try:
        # Fetch all supplies
        result = await db.execute(select(Supply))
        supplies = result.scalars().all()
        
        # Build response with facility names
        supplies_list = []
        for supply in supplies:
            # Get facility name if facility_id exists
            facility_name = None
            if supply.facility_id:
                facility_result = await db.execute(
                    select(Facility).where(Facility.facility_id == supply.facility_id)
                )
                facility = facility_result.scalar_one_or_none()
                if facility:
                    facility_name = facility.facility_name
            
            supplies_list.append({
                "supply_id": supply.supply_id,
                "supply_name": supply.supply_name,
                "description": supply.description,
                "category": supply.category,
                "quantity": supply.quantity,
                "stocking_point": supply.stocking_point,
                "stock_unit": supply.stock_unit,
                "facility_id": supply.facility_id,
                "facility_name": facility_name,
                "remarks": supply.remarks,
                "image_url": supply.image_url
            })
        
        return {"supplies": supplies_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching supplies: {str(e)}")
