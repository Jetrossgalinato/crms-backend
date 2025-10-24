from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from database import get_db, Equipment, Facility, Supply, Borrowing, Booking, Acquiring, AccountRequest, User, EquipmentLog, FacilityLog, SupplyLog
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
from typing import Optional

router = APIRouter()

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token from Authorization header and extract user info"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"email": email, "user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Not authenticated")

@router.get("/sidebar/counts")
async def get_sidebar_counts(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get all sidebar counts in a single optimized request
    """
    try:
        # Get current user's ID from JWT token
        current_user_id = current_user["user_id"]
        
        # Equipment count
        equipments_result = await db.execute(select(func.count(Equipment.id)))
        equipments = equipments_result.scalar() or 0
        
        # Facilities count
        facilities_result = await db.execute(select(func.count(Facility.facility_id)))
        facilities = facilities_result.scalar() or 0
        
        # Supplies count
        supplies_result = await db.execute(select(func.count(Supply.supply_id)))
        supplies = supplies_result.scalar() or 0
        
        # Users count - Count ALL User entries (excluding current user, interns, and supervisors)
        # This matches the logic in GET /api/users endpoint
        # Uses LEFT JOIN to include users without account_requests
        # Note: is_intern and is_supervisor can be NULL or False (both mean NOT intern/supervisor)
        users_result = await db.execute(
            select(func.count(User.id))
            .outerjoin(AccountRequest, User.id == AccountRequest.user_id)
            .where(
                and_(
                    User.id != current_user_id,  # ✅ Exclude current user
                    or_(
                        AccountRequest.id.is_(None),  # No account_request (include)
                        and_(  # Has account_request but not intern/supervisor
                            or_(AccountRequest.is_intern.is_(None), AccountRequest.is_intern == False),
                            or_(AccountRequest.is_supervisor.is_(None), AccountRequest.is_supervisor == False)
                        )
                    )
                )
            )
        )
        users = users_result.scalar() or 0
        
        # Borrowing requests count
        borrowing_result = await db.execute(select(func.count(Borrowing.id)))
        borrowing_count = borrowing_result.scalar() or 0
        
        # Booking requests count
        booking_result = await db.execute(select(func.count(Booking.id)))
        booking_count = booking_result.scalar() or 0
        
        # Acquiring requests count
        acquiring_result = await db.execute(select(func.count(Acquiring.id)))
        acquiring_count = acquiring_result.scalar() or 0
        
        # Total requests (sum of all request types)
        requests = borrowing_count + booking_count + acquiring_count
        
        # Account requests count (where is_intern and is_supervisor are both null or false)
        account_requests_result = await db.execute(
            select(func.count(AccountRequest.id)).where(
                and_(
                    or_(AccountRequest.is_intern.is_(None), AccountRequest.is_intern == False),
                    or_(AccountRequest.is_supervisor.is_(None), AccountRequest.is_supervisor == False)
                )
            )
        )
        account_requests = account_requests_result.scalar() or 0
        
        # Log counts - Get total counts from log tables
        equipment_logs_result = await db.execute(select(func.count(EquipmentLog.id)))
        equipment_logs = equipment_logs_result.scalar() or 0
        
        facility_logs_result = await db.execute(select(func.count(FacilityLog.id)))
        facility_logs = facility_logs_result.scalar() or 0
        
        supply_logs_result = await db.execute(select(func.count(SupplyLog.id)))
        supply_logs = supply_logs_result.scalar() or 0
        
        return {
            "equipments": equipments,
            "facilities": facilities,
            "supplies": supplies,
            "users": users,
            "requests": requests,
            "equipment_logs": equipment_logs,
            "facility_logs": facility_logs,
            "supply_logs": supply_logs,
            "account_requests": account_requests
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sidebar counts: {str(e)}")

@router.get("/users/me/role")
async def get_user_role(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get the current user's approved account role for menu visibility
    """
    try:
        # Get user email from token
        user_email = current_user["email"]
        
        # Get user from database
        user_result = await db.execute(
            select(User).where(User.email == user_email)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get account request for this user
        account_request_result = await db.execute(
            select(AccountRequest).where(AccountRequest.user_id == user.id)
        )
        account_request = account_request_result.scalar_one_or_none()
        
        # Return approved_acc_role (may be null if not yet assigned)
        approved_acc_role = None
        if account_request:
            approved_acc_role = account_request.approved_acc_role
        
        return {
            "approved_acc_role": approved_acc_role
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user role: {str(e)}")
