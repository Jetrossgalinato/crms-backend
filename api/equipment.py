from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from database import SessionLocal, User, Equipment, Facility, Borrowing
from api.auth_utils import SECRET_KEY, ALGORITHM
from typing import List, Optional
from datetime import datetime

router = APIRouter()
security = HTTPBearer()

async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

class EquipmentResponse(BaseModel):
    id: int
    created_at: str
    name: str
    po_number: Optional[str] = None
    unit_number: Optional[str] = None
    brand_name: Optional[str] = None
    description: Optional[str] = None
    facility: Optional[str] = None
    facility_id: Optional[int] = None
    facility_name: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    availability: str = "Available"
    date_acquire: Optional[str] = None
    supplier: Optional[str] = None
    amount: Optional[str] = None
    estimated_life: Optional[str] = None
    item_number: Optional[str] = None
    property_number: Optional[str] = None
    control_number: Optional[str] = None
    serial_number: Optional[str] = None
    person_liable: Optional[str] = None
    remarks: Optional[str] = None
    updated_at: Optional[str] = None
    image: Optional[str] = None

class UserAccountResponse(BaseModel):
    id: int
    is_employee: bool
    is_approved: bool
    user_id: str
    email: str
    first_name: str
    last_name: str
    department: str
    role: str
    account_request_id: int

class BorrowingRequest(BaseModel):
    borrowed_item: int
    purpose: str
    start_date: str
    end_date: str
    return_date: str
    request_status: str = "Pending"
    availability: str
    borrowers_id: int

class BorrowingResponse(BaseModel):
    id: int
    borrowed_item: int
    purpose: str
    start_date: str
    end_date: str
    return_date: str
    request_status: str
    availability: str
    borrowers_id: int
    created_at: str

@router.get("/equipment", response_model=List[EquipmentResponse])
async def get_equipment_list(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all equipment with facility names and availability status
    Public endpoint - no authentication required
    """
    # Get all equipment
    result = await db.execute(select(Equipment))
    equipment_list = result.scalars().all()
    
    response = []
    for equip in equipment_list:
        # Get facility name if facility_id exists
        facility_name = None
        if equip.facility_id:
            facility_result = await db.execute(
                select(Facility).where(Facility.facility_id == equip.facility_id)
            )
            facility = facility_result.scalar_one_or_none()
            if facility:
                facility_name = facility.facility_name
        
        # Check if equipment is currently borrowed
        borrowing_check = await db.execute(
            select(Borrowing).where(
                Borrowing.borrowed_item == equip.id,
                Borrowing.request_status == "Approved",
                (Borrowing.return_status == None) | (Borrowing.return_status != "Returned")
            )
        )
        active_borrowing = borrowing_check.scalar_one_or_none()
        availability = "Borrowed" if active_borrowing else "Available"
        
        response.append(EquipmentResponse(
            id=equip.id,
            created_at=equip.created_at.isoformat() if equip.created_at else "",
            name=equip.name,
            po_number=equip.po_number,
            unit_number=equip.unit_number,
            brand_name=equip.brand_name,
            description=equip.description,
            facility=equip.facility,
            facility_id=equip.facility_id,
            facility_name=facility_name,
            category=equip.category,
            status=equip.status,
            availability=availability,
            date_acquire=equip.date_acquire,
            supplier=equip.supplier,
            amount=equip.amount,
            estimated_life=equip.estimated_life,
            item_number=equip.item_number,
            property_number=equip.property_number,
            control_number=equip.control_number,
            serial_number=equip.serial_number,
            person_liable=equip.person_liable,
            remarks=equip.remarks,
            updated_at=equip.updated_at.isoformat() if equip.updated_at else None,
            image=equip.image
        ))
    
    return response

@router.get("/users/{user_id}/account", response_model=UserAccountResponse)
async def get_user_account(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user account information
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
    
    return UserAccountResponse(
        id=user.id,
        is_employee=user.is_employee,
        is_approved=user.is_approved,
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        department=user.department,
        role=user.acc_role,
        account_request_id=user.id  # Using user.id as bookers_id
    )

@router.post("/borrowing", response_model=BorrowingResponse, status_code=201)
async def create_borrowing_request(
    borrowing: BorrowingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new borrowing request
    """
    # Check if equipment exists
    equipment_result = await db.execute(
        select(Equipment).where(Equipment.id == borrowing.borrowed_item)
    )
    equipment = equipment_result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Check if user is an employee
    if not current_user.is_employee:
        raise HTTPException(status_code=403, detail="Only employees can create borrowing requests")
    
    # Create borrowing record
    new_borrowing = Borrowing(
        borrowed_item=borrowing.borrowed_item,
        borrowers_id=borrowing.borrowers_id,
        purpose=borrowing.purpose,
        start_date=borrowing.start_date,
        end_date=borrowing.end_date,
        return_date=borrowing.return_date,
        request_status=borrowing.request_status,
        availability=borrowing.availability,
        created_at=datetime.utcnow()
    )
    
    db.add(new_borrowing)
    await db.commit()
    await db.refresh(new_borrowing)
    
    return BorrowingResponse(
        id=new_borrowing.id,
        borrowed_item=new_borrowing.borrowed_item,
        purpose=new_borrowing.purpose,
        start_date=new_borrowing.start_date,
        end_date=new_borrowing.end_date,
        return_date=new_borrowing.return_date,
        request_status=new_borrowing.request_status,
        availability=new_borrowing.availability,
        borrowers_id=new_borrowing.borrowers_id,
        created_at=new_borrowing.created_at.isoformat() if new_borrowing.created_at else ""
    )
