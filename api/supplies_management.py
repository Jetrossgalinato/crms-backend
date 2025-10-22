from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db, Supply, Facility
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
import os
import uuid

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = "uploads/supply-images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Authentication dependency
async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token from Authorization header"""
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
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Not authenticated")

# Pydantic models
class SupplyCreate(BaseModel):
    name: str
    category: str
    quantity: int = 0
    stocking_point: int = 0
    stock_unit: str
    facility_id: Optional[int] = None
    description: Optional[str] = None
    image: Optional[str] = None
    remarks: Optional[str] = None

class SupplyUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    stocking_point: Optional[int] = None
    stock_unit: Optional[str] = None
    facility_id: Optional[int] = None
    description: Optional[str] = None
    image: Optional[str] = None
    remarks: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    supply_ids: List[int]

class BulkImportRequest(BaseModel):
    supplies: List[SupplyCreate]

class LogActionRequest(BaseModel):
    action: str
    supply_id: Optional[int] = None
    details: Optional[str] = None
    
    class Config:
        # Allow extra fields from frontend
        extra = "allow"

# Helper function to save uploaded file
async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return the URL path"""
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg"]
    if upload_file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PNG and JPEG images are allowed")
    
    # Validate file size (max 5MB)
    contents = await upload_file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="File size must not exceed 5MB")
    
    # Generate unique filename
    file_extension = upload_file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Return URL path
    return f"/uploads/supply-images/{unique_filename}"

# Helper function to format supply response
async def format_supply_response(supply: Supply, db: AsyncSession):
    """Format supply with facility information"""
    facility_data = None
    if supply.facility_id:
        facility_result = await db.execute(
            select(Facility).where(Facility.facility_id == supply.facility_id)
        )
        facility = facility_result.scalar_one_or_none()
        if facility:
            facility_data = {
                "id": facility.facility_id,
                "name": facility.facility_name
            }
    
    return {
        "id": supply.supply_id,
        "name": supply.supply_name,
        "category": supply.category,
        "quantity": supply.quantity,
        "stocking_point": supply.stocking_point,
        "stock_unit": supply.stock_unit,
        "description": supply.description,
        "image": supply.image_url,
        "remarks": supply.remarks,
        "facilities": facility_data,
        "created_at": supply.created_at.isoformat() if supply.created_at else None,
        "updated_at": supply.updated_at.isoformat() if supply.updated_at else None
    }

@router.get("/supplies")
async def get_all_supplies(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get all supplies with full details"""
    try:
        result = await db.execute(select(Supply))
        supplies = result.scalars().all()
        
        supplies_list = []
        for supply in supplies:
            supply_data = await format_supply_response(supply, db)
            supplies_list.append(supply_data)
        
        return supplies_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching supplies: {str(e)}")

@router.get("/facilities")
async def get_all_facilities(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get all available facilities"""
    try:
        result = await db.execute(select(Facility))
        facilities = result.scalars().all()
        
        facilities_list = [
            {
                "id": facility.facility_id,
                "name": facility.facility_name
            }
            for facility in facilities
        ]
        
        return facilities_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching facilities: {str(e)}")

@router.post("/supplies/upload-image")
async def upload_supply_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Upload an image for a supply item"""
    try:
        # Save the uploaded file
        image_url = await save_upload_file(file)
        
        return {
            "image_url": f"http://localhost:8000{image_url}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@router.post("/supplies", status_code=201)
async def create_supply(
    supply_data: SupplyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Create a new supply item"""
    try:
        # Validate required fields
        if not supply_data.name or not supply_data.category or not supply_data.stock_unit:
            raise HTTPException(
                status_code=400,
                detail="Name, category, and stock_unit are required"
            )
        
        # Validate facility_id if provided
        if supply_data.facility_id:
            facility_result = await db.execute(
                select(Facility).where(Facility.facility_id == supply_data.facility_id)
            )
            if not facility_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Invalid facility_id")
        
        # Create new supply
        new_supply = Supply(
            supply_name=supply_data.name,
            category=supply_data.category,
            quantity=supply_data.quantity,
            stocking_point=supply_data.stocking_point,
            stock_unit=supply_data.stock_unit,
            facility_id=supply_data.facility_id,
            description=supply_data.description,
            image_url=supply_data.image,
            remarks=supply_data.remarks,
            created_at=datetime.utcnow()
        )
        
        db.add(new_supply)
        await db.commit()
        await db.refresh(new_supply)
        
        # Format response with facility data
        response = await format_supply_response(new_supply, db)
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating supply: {str(e)}")

@router.put("/supplies/{supply_id}")
async def update_supply(
    supply_id: int,
    supply_data: SupplyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Update an existing supply item"""
    try:
        # Get supply
        result = await db.execute(
            select(Supply).where(Supply.supply_id == supply_id)
        )
        supply = result.scalar_one_or_none()
        
        if not supply:
            raise HTTPException(status_code=404, detail="Supply not found")
        
        # Validate facility_id if provided
        if supply_data.facility_id is not None:
            facility_result = await db.execute(
                select(Facility).where(Facility.facility_id == supply_data.facility_id)
            )
            if not facility_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Invalid facility_id")
        
        # Update fields
        if supply_data.name is not None:
            supply.supply_name = supply_data.name
        if supply_data.category is not None:
            supply.category = supply_data.category
        if supply_data.quantity is not None:
            supply.quantity = supply_data.quantity
        if supply_data.stocking_point is not None:
            supply.stocking_point = supply_data.stocking_point
        if supply_data.stock_unit is not None:
            supply.stock_unit = supply_data.stock_unit
        if supply_data.facility_id is not None:
            supply.facility_id = supply_data.facility_id
        if supply_data.description is not None:
            supply.description = supply_data.description
        if supply_data.image is not None:
            supply.image_url = supply_data.image
        if supply_data.remarks is not None:
            supply.remarks = supply_data.remarks
        
        supply.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(supply)
        
        # Format response with facility data
        response = await format_supply_response(supply, db)
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating supply: {str(e)}")

@router.delete("/supplies")
async def delete_supplies(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple supply items"""
    try:
        if not request.supply_ids:
            raise HTTPException(
                status_code=400,
                detail="supply_ids must be a non-empty array"
            )
        
        # Get supplies to delete
        result = await db.execute(
            select(Supply).where(Supply.supply_id.in_(request.supply_ids))
        )
        supplies = result.scalars().all()
        found_count = len(supplies)
        
        # Delete supplies
        await db.execute(
            delete(Supply).where(Supply.supply_id.in_(request.supply_ids))
        )
        await db.commit()
        
        # Determine response message
        total_requested = len(request.supply_ids)
        if found_count == total_requested:
            message = f"Successfully deleted {found_count} supplies"
        else:
            not_found = total_requested - found_count
            message = f"Deleted {found_count} supplies, {not_found} not found"
        
        return {
            "deleted": found_count,
            "message": message
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting supplies: {str(e)}")

@router.post("/supplies/bulk-import")
async def bulk_import_supplies(
    request: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Import multiple supplies from CSV data"""
    try:
        if not request.supplies:
            raise HTTPException(
                status_code=400,
                detail="supplies must be a non-empty array"
            )
        
        imported_count = 0
        failed_count = 0
        
        for supply_data in request.supplies:
            try:
                # Validate required fields
                if not supply_data.name or not supply_data.category or not supply_data.stock_unit:
                    failed_count += 1
                    continue
                
                # Validate facility_id if provided
                if supply_data.facility_id:
                    facility_result = await db.execute(
                        select(Facility).where(Facility.facility_id == supply_data.facility_id)
                    )
                    if not facility_result.scalar_one_or_none():
                        failed_count += 1
                        continue
                
                # Create new supply
                new_supply = Supply(
                    supply_name=supply_data.name,
                    category=supply_data.category,
                    quantity=supply_data.quantity,
                    stocking_point=supply_data.stocking_point,
                    stock_unit=supply_data.stock_unit,
                    facility_id=supply_data.facility_id,
                    description=supply_data.description,
                    image_url=supply_data.image,
                    remarks=supply_data.remarks,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_supply)
                imported_count += 1
                
            except Exception:
                failed_count += 1
                continue
        
        await db.commit()
        
        # Determine response message
        if failed_count == 0:
            message = f"Successfully imported {imported_count} supplies"
        else:
            message = f"Imported {imported_count} supplies, {failed_count} failed"
        
        return {
            "imported": imported_count,
            "failed": failed_count,
            "message": message
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing supplies: {str(e)}")

@router.post("/supply-logs")
@router.post("/supplies/log-action")
async def log_supply_action(
    log_data: LogActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Log supply management actions (create, update, delete)
    Supports both /supply-logs and /supplies/log-action endpoints
    Note: This endpoint is ready but requires SupplyLog model to be added to database.py
    """
    try:
        # Validate action type
        valid_actions = ["create", "update", "delete"]
        if log_data.action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail="Invalid action type. Must be 'create', 'update', or 'delete'"
            )
        
        # TODO: Uncomment when SupplyLog model is added to database.py
        # from database import SupplyLog
        # 
        # new_log = SupplyLog(
        #     supply_id=log_data.supply_id,
        #     action=log_data.action,
        #     details=log_data.details,
        #     user_email=current_user["email"],
        #     created_at=datetime.utcnow()
        # )
        # 
        # db.add(new_log)
        # await db.commit()
        # 
        # return {
        #     "success": True,
        #     "message": "Action logged successfully"
        # }
        
        # Temporary response until SupplyLog model is added
        return {
            "success": True,
            "message": "Action logged successfully (add SupplyLog model to database.py to enable)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging action: {str(e)}")
