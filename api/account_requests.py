from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import SessionLocal, AccountRequest, User
from typing import List, Optional

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

class AccountRequestResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    email: str
    status: str
    created_at: str
    department: Optional[str] = None
    phone_number: Optional[str] = None
    acc_role: Optional[str] = None
    approved_acc_role: Optional[str] = None
    is_supervisor: bool = False
    is_intern: bool = False

class ApproveRequestBody(BaseModel):
    approved_acc_role: str

@router.get("/account-requests", response_model=List[AccountRequestResponse])
async def get_account_requests(db: AsyncSession = Depends(get_db)):
    """
    Fetch all account requests from users with is_approved = 0
    """
    result = await db.execute(select(AccountRequest))
    requests = result.scalars().all()
    
    return [
        AccountRequestResponse(
            id=req.id,
            user_id=req.user_id,
            first_name=req.first_name,
            last_name=req.last_name,
            email=req.email,
            status=req.status,
            created_at=req.created_at.isoformat() if req.created_at else "",
            department=req.department,
            phone_number=req.phone_number,
            acc_role=req.acc_role,
            approved_acc_role=req.approved_acc_role,
            is_supervisor=req.is_supervisor,
            is_intern=req.is_intern
        )
        for req in requests
    ]

@router.post("/account-requests/{request_id}/approve")
async def approve_account_request(
    request_id: int,
    body: ApproveRequestBody,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve an account request and update the user's status
    """
    # Get the account request
    result = await db.execute(
        select(AccountRequest).where(AccountRequest.id == request_id)
    )
    account_request = result.scalar_one_or_none()
    
    if not account_request:
        raise HTTPException(status_code=404, detail="Account request not found")
    
    # Update the account request
    account_request.status = "Approved"
    account_request.approved_acc_role = body.approved_acc_role
    
    # Update the associated user
    user_result = await db.execute(
        select(User).where(User.id == account_request.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if user:
        user.is_approved = True
        user.status = "Approved"
        user.acc_role = body.approved_acc_role
    
    await db.commit()
    
    return {"message": "Account request approved successfully"}

@router.post("/account-requests/{request_id}/reject")
async def reject_account_request(request_id: int, db: AsyncSession = Depends(get_db)):
    """
    Reject an account request
    """
    result = await db.execute(
        select(AccountRequest).where(AccountRequest.id == request_id)
    )
    account_request = result.scalar_one_or_none()
    
    if not account_request:
        raise HTTPException(status_code=404, detail="Account request not found")
    
    # Update the account request
    account_request.status = "Rejected"
    
    # Update the associated user
    user_result = await db.execute(
        select(User).where(User.id == account_request.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if user:
        user.status = "Rejected"
    
    await db.commit()
    
    return {"message": "Account request rejected successfully"}

@router.delete("/account-requests/{request_id}")
async def delete_account_request(request_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete an account request
    """
    result = await db.execute(
        select(AccountRequest).where(AccountRequest.id == request_id)
    )
    account_request = result.scalar_one_or_none()
    
    if not account_request:
        raise HTTPException(status_code=404, detail="Account request not found")
    
    await db.delete(account_request)
    await db.commit()
    
    return {"message": "Account request deleted successfully"}
