from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, User, AccountRequest
from pydantic import BaseModel
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM, verify_password, get_password_hash
from typing import Optional
from datetime import datetime

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
        raise HTTPException(status_code=401, detail=f"Invalid or expired token")

class ProfileResponse(BaseModel):
    first_name: str
    last_name: str
    email: str
    department: str
    phone_number: str
    acc_role: str

class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    department: str
    phone_number: str
    acc_role: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/users/{user_id}/profile", response_model=ProfileResponse)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get user profile information
    """
    try:
        # Get user from database
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Verify token matches user
        if user.email != current_user["email"]:
            raise HTTPException(status_code=403, detail="Unauthorized to access this profile")
        
        return ProfileResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            department=user.department,
            phone_number=user.phone_number,
            acc_role=user.acc_role
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")

@router.put("/users/{user_id}/profile", response_model=ProfileResponse)
async def update_user_profile(
    user_id: int,
    profile_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Update user profile information
    """
    try:
        # Get user from database
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Verify token matches user
        if user.email != current_user["email"]:
            raise HTTPException(status_code=403, detail="Unauthorized to update this profile")
        
        # Validate input data
        if not profile_data.first_name or not profile_data.first_name.strip():
            raise HTTPException(status_code=400, detail="First name is required")
        
        if not profile_data.last_name or not profile_data.last_name.strip():
            raise HTTPException(status_code=400, detail="Last name is required")
        
        if not profile_data.phone_number or not profile_data.phone_number.strip():
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        # Update user information
        user.first_name = profile_data.first_name.strip()
        user.last_name = profile_data.last_name.strip()
        user.department = profile_data.department.strip()
        user.phone_number = profile_data.phone_number.strip()
        user.acc_role = profile_data.acc_role.strip()
        
        await db.commit()
        await db.refresh(user)
        
        # Also update account_requests table if exists
        account_request_result = await db.execute(
            select(AccountRequest).where(AccountRequest.user_id == user_id)
        )
        account_request = account_request_result.scalar_one_or_none()
        
        if account_request:
            account_request.first_name = profile_data.first_name.strip()
            account_request.last_name = profile_data.last_name.strip()
            account_request.department = profile_data.department.strip()
            account_request.phone_number = profile_data.phone_number.strip()
            account_request.acc_role = profile_data.acc_role.strip()
            await db.commit()
        
        return ProfileResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            department=user.department,
            phone_number=user.phone_number,
            acc_role=user.acc_role
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

@router.post("/auth/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Change user password
    """
    try:
        # Validate new password length
        if len(password_data.new_password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters long"
            )
        
        # Get user from database
        user_result = await db.execute(
            select(User).where(User.email == current_user["email"])
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Hash and update new password
        user.hashed_password = get_password_hash(password_data.new_password)
        
        await db.commit()
        
        return {"message": "Password updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error changing password: {str(e)}")
