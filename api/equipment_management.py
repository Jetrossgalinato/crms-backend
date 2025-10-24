from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from database import get_db, Equipment, Facility, User, EquipmentLog
from pydantic import BaseModel
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
from typing import Optional, List
from datetime import datetime
import os
import shutil
import uuid
import math

router = APIRouter()

# File upload configuration
UPLOAD_DIR = "uploads/equipment-images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

class EquipmentCreate(BaseModel):
    name: str
    po_number: Optional[str] = None
    unit_number: Optional[str] = None
    brand_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    availability: Optional[str] = "Available"
    date_acquire: Optional[str] = None
    supplier: Optional[str] = None
    amount: Optional[str] = None
    estimated_life: Optional[str] = None
    item_number: Optional[str] = None
    property_number: Optional[str] = None
    control_number: Optional[str] = None
    serial_number: Optional[str] = None
    person_liable: Optional[str] = None
    facility_id: Optional[int] = None
    remarks: Optional[str] = None
    image: Optional[str] = None

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    po_number: Optional[str] = None
    unit_number: Optional[str] = None
    brand_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    availability: Optional[str] = None
    date_acquire: Optional[str] = None
    supplier: Optional[str] = None
    amount: Optional[str] = None
    estimated_life: Optional[str] = None
    item_number: Optional[str] = None
    property_number: Optional[str] = None
    control_number: Optional[str] = None
    serial_number: Optional[str] = None
    person_liable: Optional[str] = None
    facility_id: Optional[int] = None
    remarks: Optional[str] = None
    image: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class BulkImportRequest(BaseModel):
    equipments: List[EquipmentCreate]

class EquipmentLogCreate(BaseModel):
    action: str
    equipment_name: Optional[str] = None
    details: Optional[str] = None

@router.get("/equipments")
async def get_all_equipments(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get all equipments ordered by ID
    """
    try:
        result = await db.execute(
            select(Equipment).order_by(Equipment.id)
        )
        equipments = result.scalars().all()
        
        return [
            {
                "id": eq.id,
                "name": eq.name,
                "po_number": eq.po_number,
                "unit_number": eq.unit_number,
                "brand_name": eq.brand_name,
                "description": eq.description,
                "category": eq.category,
                "status": eq.status,
                "availability": "Available",  # Default, can be calculated based on borrowing
                "date_acquire": eq.date_acquire,
                "supplier": eq.supplier,
                "amount": eq.amount,
                "estimated_life": eq.estimated_life,
                "item_number": eq.item_number,
                "property_number": eq.property_number,
                "control_number": eq.control_number,
                "serial_number": eq.serial_number,
                "person_liable": eq.person_liable,
                "facility_id": eq.facility_id,
                "remarks": eq.remarks,
                "image": eq.image,
                "created_at": eq.created_at.isoformat() if eq.created_at else None,
                "updated_at": eq.updated_at.isoformat() if eq.updated_at else None
            }
            for eq in equipments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching equipments: {str(e)}")

@router.get("/facilities")
async def get_all_facilities(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get all facilities ordered by name
    """
    try:
        result = await db.execute(
            select(Facility).order_by(Facility.facility_name)
        )
        facilities = result.scalars().all()
        
        return [
            {
                "id": facility.facility_id,
                "name": facility.facility_name
            }
            for facility in facilities
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching facilities: {str(e)}")

@router.post("/equipments", status_code=201)
async def create_equipment(
    equipment: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Create a new equipment record
    """
    try:
        if not equipment.name or not equipment.name.strip():
            raise HTTPException(status_code=400, detail="Equipment name is required")
        
        new_equipment = Equipment(
            name=equipment.name,
            po_number=equipment.po_number,
            unit_number=equipment.unit_number,
            brand_name=equipment.brand_name,
            description=equipment.description,
            category=equipment.category,
            status=equipment.status,
            date_acquire=equipment.date_acquire,
            supplier=equipment.supplier,
            amount=equipment.amount,
            estimated_life=equipment.estimated_life,
            item_number=equipment.item_number,
            property_number=equipment.property_number,
            control_number=equipment.control_number,
            serial_number=equipment.serial_number,
            person_liable=equipment.person_liable,
            facility_id=equipment.facility_id,
            remarks=equipment.remarks,
            image=equipment.image,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_equipment)
        await db.commit()
        await db.refresh(new_equipment)
        
        return {
            "id": new_equipment.id,
            "name": new_equipment.name,
            "po_number": new_equipment.po_number,
            "brand_name": new_equipment.brand_name,
            "category": new_equipment.category,
            "facility_id": new_equipment.facility_id,
            "image": new_equipment.image,
            "created_at": new_equipment.created_at.isoformat(),
            "updated_at": new_equipment.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating equipment: {str(e)}")

@router.put("/equipments/{equipment_id}")
async def update_equipment(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Update an existing equipment record
    """
    try:
        result = await db.execute(
            select(Equipment).where(Equipment.id == equipment_id)
        )
        equipment = result.scalar_one_or_none()
        
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        # Update only provided fields
        update_data = equipment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(equipment, field, value)
        
        equipment.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(equipment)
        
        return {
            "id": equipment.id,
            "name": equipment.name,
            "status": equipment.status,
            "remarks": equipment.remarks,
            "amount": equipment.amount,
            "updated_at": equipment.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating equipment: {str(e)}")

@router.delete("/equipments/bulk-delete")
async def bulk_delete_equipments(
    delete_request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Delete multiple equipment records by IDs
    """
    try:
        if not delete_request.ids:
            raise HTTPException(status_code=400, detail="No equipment IDs provided")
        
        result = await db.execute(
            delete(Equipment).where(Equipment.id.in_(delete_request.ids))
        )
        
        await db.commit()
        deleted_count = result.rowcount
        
        return {
            "message": f"Successfully deleted {deleted_count} equipments",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting equipments: {str(e)}")

@router.post("/equipments/upload-image")
async def upload_equipment_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """
    Upload equipment image and return the URL
    """
    try:
        # Validate file extension
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only PNG, JPG, and JPEG are allowed"
            )
        
        # Read file content to check size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 5MB limit"
            )
        
        # Generate unique filename
        timestamp = int(datetime.now().timestamp())
        random_string = str(uuid.uuid4())[:8]
        filename = f"{timestamp}-{random_string}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Return URL (adjust based on your server configuration)
        image_url = f"http://localhost:8000/uploads/equipment-images/{filename}"
        
        return {
            "image_url": image_url,
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@router.post("/equipments/bulk-import")
async def bulk_import_equipments(
    import_request: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Bulk import equipment records
    """
    try:
        if not import_request.equipments:
            raise HTTPException(status_code=400, detail="No equipments provided")
        
        imported = 0
        failed = 0
        errors = []
        
        for index, eq_data in enumerate(import_request.equipments):
            try:
                if not eq_data.name or not eq_data.name.strip():
                    failed += 1
                    errors.append({
                        "index": index,
                        "error": "Equipment name is required"
                    })
                    continue
                
                new_equipment = Equipment(
                    name=eq_data.name,
                    po_number=eq_data.po_number,
                    unit_number=eq_data.unit_number,
                    brand_name=eq_data.brand_name,
                    description=eq_data.description,
                    category=eq_data.category,
                    status=eq_data.status,
                    date_acquire=eq_data.date_acquire,
                    supplier=eq_data.supplier,
                    amount=eq_data.amount,
                    estimated_life=eq_data.estimated_life,
                    item_number=eq_data.item_number,
                    property_number=eq_data.property_number,
                    control_number=eq_data.control_number,
                    serial_number=eq_data.serial_number,
                    person_liable=eq_data.person_liable,
                    facility_id=eq_data.facility_id,
                    remarks=eq_data.remarks,
                    image=eq_data.image,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(new_equipment)
                imported += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "index": index,
                    "error": str(e)
                })
        
        await db.commit()
        
        total = len(import_request.equipments)
        
        if failed > 0:
            return {
                "imported": imported,
                "failed": failed,
                "total": total,
                "message": f"Imported {imported} equipments, {failed} failed",
                "errors": errors
            }
        
        return {
            "imported": imported,
            "failed": failed,
            "total": total,
            "message": f"Successfully imported {imported} equipments"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing equipments: {str(e)}")

@router.post("/equipment-logs", status_code=201)
async def create_equipment_log(
    log_data: EquipmentLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Log equipment action for audit trail
    """
    try:
        if not log_data.action:
            raise HTTPException(status_code=400, detail="Action is required")
        
        # Get user information from token
        user_email = current_user["email"]
        
        # Get user name from database
        user_result = await db.execute(
            select(User).where(User.email == user_email)
        )
        user = user_result.scalar_one_or_none()
        user_name = f"{user.first_name} {user.last_name}" if user else user_email
        
        # Construct log message
        if log_data.equipment_name:
            log_message = f"{user_name} {log_data.action} equipment: {log_data.equipment_name}"
            if log_data.details:
                log_message += f" - {log_data.details}"
        else:
            log_message = f"{user_name} {log_data.action}"
            if log_data.details:
                log_message += f" - {log_data.details}"
        
        # For now, just return the log data since we don't have equipment_logs table in database.py
        # You can add the EquipmentLog model to database.py and uncomment the code below
        
        """
        from database import EquipmentLog
        
        new_log = EquipmentLog(
            log_message=log_message,
            action=log_data.action,
            equipment_name=log_data.equipment_name,
            details=log_data.details,
            user_email=user_email,
            created_at=datetime.utcnow()
        )
        
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)
        
        return {
            "id": new_log.id,
            "log_message": new_log.log_message,
            "action": new_log.action,
            "equipment_name": new_log.equipment_name,
            "details": new_log.details,
            "user_email": new_log.user_email,
            "created_at": new_log.created_at.isoformat()
        }
        """
        
        # Temporary response until EquipmentLog model is added
        return {
            "id": 1,
            "log_message": log_message,
            "action": log_data.action,
            "equipment_name": log_data.equipment_name,
            "details": log_data.details,
            "user_email": user_email,
            "created_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating equipment log: {str(e)}")

@router.get("/equipment/logs")
async def get_equipment_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get paginated equipment logs for monitoring page
    Returns logs with formatted log_message field for frontend display
    """
    try:
        # Get total count
        count_result = await db.execute(select(func.count(EquipmentLog.id)))
        total_count = count_result.scalar() or 0
        
        # Calculate pagination
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
        offset = (page - 1) * limit
        
        # Get logs with pagination
        query = (
            select(EquipmentLog)
            .order_by(EquipmentLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Get user information for better log messages
        user_result = await db.execute(
            select(User).where(User.email == current_user["email"])
        )
        user = user_result.scalar_one_or_none()
        
        # Format response with log_message field
        logs_data = []
        for log in logs:
            # Get equipment name if equipment_id exists
            equipment_name = "Unknown Equipment"
            if log.equipment_id:
                equipment_result = await db.execute(
                    select(Equipment).where(Equipment.id == log.equipment_id)
                )
                equipment = equipment_result.scalar_one_or_none()
                if equipment:
                    equipment_name = equipment.name
            
            # Construct log_message based on action and details
            # Format: "Admin {user} {action} for {equipment_name} - {details}"
            user_identifier = log.user_email.split("@")[0] if log.user_email else "User"
            
            if log.details:
                log_message = f"Admin {user_identifier} {log.action} for {equipment_name} - {log.details}"
            else:
                log_message = f"Admin {user_identifier} {log.action} for {equipment_name}"
            
            logs_data.append({
                "id": log.id,
                "log_message": log_message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })
        
        return {
            "logs": logs_data,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching equipment logs: {str(e)}")
