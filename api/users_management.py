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
    exclude_user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Retrieve paginated list of users with optional filtering.
    
    Excludes the current authenticated user from results.
    Only returns users where is_intern IS NULL AND is_supervisor IS NULL.
    Filters can be applied for department and role.
    """
    try:
        # Get current user's ID from JWT token
        current_user_id = current_user["user_id"]
        
        # Build base query - get AccountRequests with User email
        # Filter for regular users (not interns or supervisors)
        # ALWAYS exclude current user
        query = (
            select(AccountRequest, User.email)
            .join(User, AccountRequest.user_id == User.id)
            .where(
                and_(
                    AccountRequest.is_intern.is_(None),
                    AccountRequest.is_supervisor.is_(None),
                    AccountRequest.user_id != current_user_id  # Exclude current user
                )
            )
        )
        
        # Apply additional exclusion if provided
        if exclude_user_id and exclude_user_id != current_user_id:
            query = query.where(AccountRequest.user_id != exclude_user_id)
        
        # Apply department filter (case-insensitive partial match)
        if department:
            query = query.where(
                AccountRequest.department.ilike(f"%{department}%")
            )
        
        # Apply role filter (case-insensitive partial match on both acc_role and approved_acc_role)
        if role:
            query = query.where(
                or_(
                    AccountRequest.acc_role.ilike(f"%{role}%"),
                    AccountRequest.approved_acc_role.ilike(f"%{role}%")
                )
            )
        
        # Get total count - use same filters as main query
        count_query = (
            select(func.count(AccountRequest.id))
            .join(User, AccountRequest.user_id == User.id)
            .where(
                and_(
                    AccountRequest.is_intern.is_(None),
                    AccountRequest.is_supervisor.is_(None),
                    AccountRequest.user_id != current_user_id  # Exclude current user
                )
            )
        )
        
        # Apply additional exclusion if provided
        if exclude_user_id and exclude_user_id != current_user_id:
            count_query = count_query.where(AccountRequest.user_id != exclude_user_id)
        
        # Apply same filters to count
        if department:
            count_query = count_query.where(
                AccountRequest.department.ilike(f"%{department}%")
            )
        if role:
            count_query = count_query.where(
                or_(
                    AccountRequest.acc_role.ilike(f"%{role}%"),
                    AccountRequest.approved_acc_role.ilike(f"%{role}%")
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
                AccountRequest.first_name.asc(),
                AccountRequest.last_name.asc(),
                User.email.asc()
            )
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Format response
        users = []
        for account_request, email in rows:
            users.append({
                "id": account_request.id,
                "first_name": account_request.first_name,
                "last_name": account_request.last_name,
                "department": account_request.department,
                "phone_number": account_request.phone_number,
                "acc_role": account_request.acc_role,
                "approved_acc_role": account_request.approved_acc_role,
                "email": email
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
    user_data: UserBase,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Update user information by ID.
    """
    try:
        # Find account request
        result = await db.execute(
            select(AccountRequest).where(AccountRequest.id == user_id)
        )
        account_request = result.scalar_one_or_none()
        
        if not account_request:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields
        account_request.first_name = user_data.first_name
        account_request.last_name = user_data.last_name
        account_request.department = user_data.department
        account_request.phone_number = user_data.phone_number
        account_request.acc_role = user_data.acc_role
        account_request.approved_acc_role = user_data.approved_acc_role
        
        await db.commit()
        await db.refresh(account_request)
        
        # Get user email
        user_result = await db.execute(
            select(User).where(User.id == account_request.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        return {
            "id": account_request.id,
            "first_name": account_request.first_name,
            "last_name": account_request.last_name,
            "department": account_request.department,
            "phone_number": account_request.phone_number,
            "acc_role": account_request.acc_role,
            "approved_acc_role": account_request.approved_acc_role,
            "email": user.email if user else ""
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
    Delete multiple users by IDs.
    """
    try:
        if not request.user_ids:
            raise HTTPException(
                status_code=400,
                detail="user_ids must be a non-empty array"
            )
        
        # Delete account requests
        result = await db.execute(
            delete(AccountRequest).where(AccountRequest.id.in_(request.user_ids))
        )
        
        deleted_count = result.rowcount
        await db.commit()
        
        return {
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} users"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting users: {str(e)}")
