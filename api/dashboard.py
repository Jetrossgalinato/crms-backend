from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from database import get_db, User, AccountRequest, Equipment, Facility, Supply, Borrowing, Booking
from jose import JWTError, jwt, ExpiredSignatureError
from api.auth_utils import SECRET_KEY, ALGORITHM
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Authorization header missing"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401, 
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header format"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401, 
                detail="Invalid authentication credentials"
            )
        return {"email": email}
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401, 
            detail="Token has expired"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Token validation failed: {str(e)}"
        )

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get comprehensive dashboard statistics
    """
    try:
        # Total users (approved users)
        total_users_result = await db.execute(
            select(func.count(User.id)).where(User.is_approved == True)
        )
        total_users = total_users_result.scalar() or 0
        
        # Pending account requests
        pending_account_result = await db.execute(
            select(func.count(AccountRequest.id)).where(AccountRequest.status == "Pending")
        )
        pending_account = pending_account_result.scalar() or 0
        
        # Pending borrowing requests
        pending_borrowing_result = await db.execute(
            select(func.count(Borrowing.id)).where(Borrowing.request_status == "Pending")
        )
        pending_borrowing = pending_borrowing_result.scalar() or 0
        
        # Pending booking requests
        pending_booking_result = await db.execute(
            select(func.count(Booking.id)).where(Booking.status == "Pending")
        )
        pending_booking = pending_booking_result.scalar() or 0
        
        # Total pending requests
        pending_requests = pending_account + pending_borrowing + pending_booking
        
        # Total equipment
        total_equipment_result = await db.execute(
            select(func.count(Equipment.id))
        )
        total_equipment = total_equipment_result.scalar() or 0
        
        # Active facilities (Available or not Under Maintenance)
        active_facilities_result = await db.execute(
            select(func.count(Facility.facility_id)).where(
                Facility.status != "Under Maintenance"
            )
        )
        active_facilities = active_facilities_result.scalar() or 0
        
        # Total supplies
        total_supplies_result = await db.execute(
            select(func.count(Supply.supply_id))
        )
        total_supplies = total_supplies_result.scalar() or 0
        
        # Borrowed today (using start_date)
        today = datetime.now().date().isoformat()
        borrowed_today_result = await db.execute(
            select(func.count(Borrowing.id)).where(
                Borrowing.start_date == today,
                Borrowing.request_status == "Approved"
            )
        )
        borrowed_today = borrowed_today_result.scalar() or 0
        
        # Borrowed last 7 days
        seven_days_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
        borrowed_last_7_result = await db.execute(
            select(func.count(Borrowing.id)).where(
                Borrowing.start_date >= seven_days_ago,
                Borrowing.request_status == "Approved"
            )
        )
        borrowed_last_7_days = borrowed_last_7_result.scalar() or 0
        
        # Total equipment categories (distinct categories)
        categories_result = await db.execute(
            select(func.count(distinct(Equipment.category))).where(
                Equipment.category.isnot(None)
            )
        )
        total_equipment_categories = categories_result.scalar() or 0
        
        return {
            "total_users": total_users,
            "pending_requests": pending_requests,
            "total_equipment": total_equipment,
            "active_facilities": active_facilities,
            "total_supplies": total_supplies,
            "borrowed_last_7_days": borrowed_last_7_days,
            "borrowed_today": borrowed_today,
            "total_equipment_categories": total_equipment_categories
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard statistics: {str(e)}")

@router.get("/dashboard/equipment/by-person-liable")
async def get_equipment_by_person_liable(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get equipment count grouped by person liable
    """
    try:
        result = await db.execute(
            select(
                Equipment.person_liable,
                func.count(Equipment.id).label('equipment_count')
            )
            .where(Equipment.person_liable.isnot(None))
            .group_by(Equipment.person_liable)
            .order_by(func.count(Equipment.id).desc())
        )
        
        data = result.all()
        return [
            {
                "person_liable": row.person_liable,
                "equipment_count": row.equipment_count
            }
            for row in data
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching equipment by person liable: {str(e)}")

@router.get("/dashboard/equipment/by-category")
async def get_equipment_by_category(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get equipment count grouped by category
    """
    try:
        result = await db.execute(
            select(
                Equipment.category,
                func.count(Equipment.id).label('count')
            )
            .where(Equipment.category.isnot(None))
            .group_by(Equipment.category)
            .order_by(func.count(Equipment.id).desc())
        )
        
        data = result.all()
        return [
            {
                "category": row.category,
                "count": row.count
            }
            for row in data
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching equipment by category: {str(e)}")

@router.get("/dashboard/equipment/by-status")
async def get_equipment_by_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get equipment count grouped by status
    """
    try:
        result = await db.execute(
            select(
                Equipment.status,
                func.count(Equipment.id).label('count')
            )
            .where(Equipment.status.isnot(None))
            .group_by(Equipment.status)
            .order_by(func.count(Equipment.id).desc())
        )
        
        data = result.all()
        return [
            {
                "status": row.status,
                "count": row.count
            }
            for row in data
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching equipment by status: {str(e)}")

@router.get("/dashboard/equipment/by-facility")
async def get_equipment_by_facility(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get equipment count grouped by facility
    """
    try:
        # Join equipment with facilities table
        result = await db.execute(
            select(
                Facility.facility_name,
                func.count(Equipment.id).label('equipment_count')
            )
            .select_from(Facility)
            .outerjoin(Equipment, Equipment.facility_id == Facility.facility_id)
            .group_by(Facility.facility_id, Facility.facility_name)
            .order_by(func.count(Equipment.id).desc())
        )
        
        data = result.all()
        return [
            {
                "facility_name": row.facility_name,
                "equipment_count": row.equipment_count
            }
            for row in data
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching equipment by facility: {str(e)}")

@router.get("/dashboard/equipment/availability")
async def get_equipment_availability(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get equipment availability statistics with counts and percentages
    """
    try:
        # Get total equipment count
        total_result = await db.execute(
            select(func.count(Equipment.id))
        )
        total_equipment = total_result.scalar() or 0
        
        if total_equipment == 0:
            return []
        
        # Get all equipment with their borrowing status
        equipment_result = await db.execute(select(Equipment))
        all_equipment = equipment_result.scalars().all()
        
        # Get active borrowings
        borrowing_result = await db.execute(
            select(Borrowing).where(
                Borrowing.request_status == "Approved",
                Borrowing.return_status != "Returned"
            )
        )
        active_borrowings = borrowing_result.scalars().all()
        borrowed_equipment_ids = {b.borrowed_item for b in active_borrowings}
        
        # Calculate availability
        available_count = 0
        in_use_count = 0
        unavailable_count = 0
        
        for equipment in all_equipment:
            if equipment.id in borrowed_equipment_ids:
                in_use_count += 1
            elif equipment.status and equipment.status.lower() in ["working", "available", "good"]:
                available_count += 1
            else:
                unavailable_count += 1
        
        return [
            {
                "status": "Available",
                "count": available_count,
                "percentage": round((available_count / total_equipment) * 100, 1)
            },
            {
                "status": "In Use",
                "count": in_use_count,
                "percentage": round((in_use_count / total_equipment) * 100, 1)
            },
            {
                "status": "Unavailable",
                "count": unavailable_count,
                "percentage": round((unavailable_count / total_equipment) * 100, 1)
            }
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching equipment availability: {str(e)}")
