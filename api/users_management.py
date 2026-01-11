from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_, or_
from database import get_db, User, AccountRequest
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
import math

router = APIRouter()

# Authentication dependency
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

# Pydantic models
class UserBase(BaseModel):
    first_name: str
    last_name: str
    department: str
    phone_number: Optional[str] = None
    acc_role: str
    approved_acc_role: Optional[str] = None

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    phone_number: Optional[str] = None
    acc_role: Optional[str] = None
    approved_acc_role: Optional[str] = None
    email: Optional[str] = None

class UserResponse(UserBase):
    id: int
    email: str

class UsersListResponse(BaseModel):
    users: List[dict]
    total_count: int
    page: int
    limit: int
    total_pages: int

class BatchDeleteRequest(BaseModel):
    user_ids: List[int]

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    department: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    exclude_user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Retrieve paginated list of users with optional filtering.
    
    Excludes the current authenticated user from results.
    Shows ALL users from users table, with optional account_requests data.
    Filters can be applied for department, role, and generic search.
    """
    try:
        # Get current user's ID from JWT token
        current_user_id = current_user["user_id"]
        
        # Build base query - get ALL Users with optional AccountRequest data
        # Use LEFT JOIN so users without account_requests are still included
        # ALWAYS exclude current user
        query = (
            select(
                User.id,
                User.email,
                User.first_name,
                User.last_name,
                User.department,
                User.phone_number,
                User.acc_role,
                AccountRequest.approved_acc_role,
                AccountRequest.is_intern,
                AccountRequest.is_supervisor
            )
            .outerjoin(AccountRequest, User.id == AccountRequest.user_id)
            .where(User.id != current_user_id)  # Exclude current user
        )
        
        # Filter out interns and supervisors (if they have account_request)
        # Keep users who don't have account_request at all
        query = query.where(
            or_(
                AccountRequest.id.is_(None),  # No account_request (include)
                and_(  # Has account_request but not intern/supervisor
                    or_(AccountRequest.is_intern.is_(None), AccountRequest.is_intern == False),
                    or_(AccountRequest.is_supervisor.is_(None), AccountRequest.is_supervisor == False)
                )
            )
        )
        
        # Apply additional exclusion if provided
        if exclude_user_id and exclude_user_id != current_user_id:
            query = query.where(User.id != exclude_user_id)
        
        # Apply department filter (case-insensitive partial match)
        if department:
            query = query.where(User.department.ilike(f"%{department}%"))
        
        # Apply role filter (check both User.acc_role and AccountRequest.approved_acc_role)
        if role:
            query = query.where(
                or_(
                    User.acc_role.ilike(f"%{role}%"),
                    AccountRequest.approved_acc_role.ilike(f"%{role}%")
                )
            )

        # Apply search filter (first_name, last_name, email, department)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.department.ilike(search_pattern)
                )
            )
        
        # Get total count - use same filters as main query
        count_query = (
            select(func.count(User.id))
            .outerjoin(AccountRequest, User.id == AccountRequest.user_id)
            .where(User.id != current_user_id)  # Exclude current user
        )
        
        # Apply same filters to count
        count_query = count_query.where(
            or_(
                AccountRequest.id.is_(None),  # No account_request
                and_(  # Has account_request but not intern/supervisor
                    or_(AccountRequest.is_intern.is_(None), AccountRequest.is_intern == False),
                    or_(AccountRequest.is_supervisor.is_(None), AccountRequest.is_supervisor == False)
                )
            )
        )
        
        # Apply additional exclusion if provided
        if exclude_user_id and exclude_user_id != current_user_id:
            count_query = count_query.where(User.id != exclude_user_id)
        
        if department:
            count_query = count_query.where(User.department.ilike(f"%{department}%"))
        
        if role:
            count_query = count_query.where(
                or_(
                    User.acc_role.ilike(f"%{role}%"),
                    AccountRequest.approved_acc_role.ilike(f"%{role}%")
                )
            )

        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.where(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.department.ilike(search_pattern)
                )
            )
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Calculate pagination
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
        offset = (page - 1) * limit
        
        # Get paginated results with proper sorting
        query = (
            query.order_by(
                User.first_name.asc(),
                User.last_name.asc(),
                User.email.asc()
            )
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Format response
        users = []
        for row in rows:
            users.append({
                "id": row.id,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "department": row.department,
                "phone_number": row.phone_number,
                "acc_role": row.acc_role,
                "approved_acc_role": row.approved_acc_role,
                "email": row.email
            })
        
        return {
            "users": users,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Update user information by ID.
    Updates the User table (not AccountRequest).
    """
    try:
        # Find user in User table
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update only provided fields in User table
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.department is not None:
            user.department = user_data.department
        if user_data.phone_number is not None:
            user.phone_number = user_data.phone_number
        if user_data.acc_role is not None:
            user.acc_role = user_data.acc_role
        
        # Handle email update with duplicate check
        if user_data.email is not None and user_data.email != user.email:
            # Check if email already exists
            email_check = await db.execute(
                select(User).where(and_(User.email == user_data.email, User.id != user_id))
            )
            if email_check.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already registered")
            user.email = user_data.email
        
        # Also update AccountRequest if it exists
        account_request_result = await db.execute(
            select(AccountRequest).where(AccountRequest.user_id == user_id)
        )
        account_request = account_request_result.scalar_one_or_none()
        
        if account_request:
            if user_data.approved_acc_role is not None:
                account_request.approved_acc_role = user_data.approved_acc_role
            
            # Sync other fields to keep AccountRequest consistent with User
            if user_data.first_name is not None:
                account_request.first_name = user_data.first_name
            if user_data.last_name is not None:
                account_request.last_name = user_data.last_name
            if user_data.department is not None:
                account_request.department = user_data.department
            if user_data.phone_number is not None:
                account_request.phone_number = user_data.phone_number
            if user_data.acc_role is not None:
                account_request.acc_role = user_data.acc_role
            if user_data.email is not None:
                account_request.email = user_data.email
        
        await db.commit()
        await db.refresh(user)
        
        # Get approved_acc_role from AccountRequest if exists
        account_request_result = await db.execute(
            select(AccountRequest).where(AccountRequest.user_id == user_id)
        )
        account_request = account_request_result.scalar_one_or_none()
        
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "department": user.department,
            "phone_number": user.phone_number,
            "acc_role": user.acc_role,
            "approved_acc_role": account_request.approved_acc_role if account_request else None,
            "email": user.email
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.delete("/users/batch")
async def batch_delete_users(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Delete multiple users by IDs - permanently removes users from the users table.
    """
    try:
        if not request.user_ids:
            raise HTTPException(
                status_code=400,
                detail="user_ids must be a non-empty array"
            )
        
        # Delete users from the users table
        result = await db.execute(
            delete(User).where(User.id.in_(request.user_ids))
        )
        
        deleted_count = result.rowcount
        await db.commit()
        
        return {
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} user(s) from the system"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting users: {str(e)}")
