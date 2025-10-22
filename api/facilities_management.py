from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db, Facility
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
import os
import uuid

router = APIRouter()

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
class FacilityCreate(BaseModel):
    facility_name: str
    facility_type: str
    floor_level: str
    capacity: Optional[int] = None
    connection_type: Optional[str] = None
    cooling_tools: Optional[str] = None
    building: Optional[str] = None
    description: Optional[str] = None
    remarks: Optional[str] = None
    status: str = "Available"

class FacilityUpdate(BaseModel):
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    floor_level: Optional[str] = None
    capacity: Optional[int] = None
    connection_type: Optional[str] = None
    cooling_tools: Optional[str] = None
    building: Optional[str] = None
    description: Optional[str] = None
    remarks: Optional[str] = None
    status: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    facility_ids: List[int]

class FacilityLogCreate(BaseModel):
    facility_id: int
    action: str
    details: Optional[str] = None

# Ensure upload directory exists
UPLOAD_DIR = "uploads/facility-images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    return f"/uploads/facility-images/{unique_filename}"

@router.get("/facilities/all")
async def get_all_facilities(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get all facilities for dashboard management"""
    try:
        result = await db.execute(select(Facility))
        facilities = result.scalars().all()
        
        facilities_list = []
        for facility in facilities:
            facilities_list.append({
                "facility_id": facility.facility_id,
                "facility_name": facility.facility_name,
                "facility_type": facility.facility_type,
                "floor_level": facility.floor_level,
                "capacity": facility.capacity,
                "connection_type": facility.connection_type,
                "cooling_tools": facility.cooling_tools,
                "building": facility.building,
                "description": facility.description,
                "remarks": facility.remarks,
                "status": facility.status,
                "image_url": facility.image_url,
                "created_at": facility.created_at.isoformat() if facility.created_at else None,
                "updated_at": facility.updated_at.isoformat() if facility.updated_at else None
            })
        
        return {"facilities": facilities_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching facilities: {str(e)}")

@router.post("/facilities")
async def create_facility_json(
    facility_data: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Create a new facility with JSON data (no image upload)"""
    try:
        # Create new facility
        new_facility = Facility(
            facility_name=facility_data.facility_name,
            facility_type=facility_data.facility_type,
            floor_level=facility_data.floor_level,
            capacity=facility_data.capacity,
            connection_type=facility_data.connection_type,
            cooling_tools=facility_data.cooling_tools,
            building=facility_data.building,
            description=facility_data.description,
            remarks=facility_data.remarks,
            status=facility_data.status,
            created_at=datetime.utcnow()
        )
        
        db.add(new_facility)
        await db.commit()
        await db.refresh(new_facility)
        
        return {
            "message": "Facility created successfully",
            "facility": {
                "facility_id": new_facility.facility_id,
                "facility_name": new_facility.facility_name,
                "facility_type": new_facility.facility_type,
                "floor_level": new_facility.floor_level,
                "capacity": new_facility.capacity,
                "connection_type": new_facility.connection_type,
                "cooling_tools": new_facility.cooling_tools,
                "building": new_facility.building,
                "description": new_facility.description,
                "remarks": new_facility.remarks,
                "status": new_facility.status,
                "image_url": new_facility.image_url,
                "created_at": new_facility.created_at.isoformat()
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating facility: {str(e)}")

@router.post("/facilities/with-image")
async def create_facility_with_image(
    facility_name: str = Form(...),
    facility_type: str = Form(...),
    floor_level: str = Form(...),
    capacity: Optional[int] = Form(None),
    connection_type: Optional[str] = Form(None),
    cooling_tools: Optional[str] = Form(None),
    building: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    status: str = Form("Available"),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Create a new facility with optional image upload (Form data)"""
    try:
        # Handle image upload
        image_url = None
        if image:
            image_url = await save_upload_file(image)
        
        # Create new facility
        new_facility = Facility(
            facility_name=facility_name,
            facility_type=facility_type,
            floor_level=floor_level,
            capacity=capacity,
            connection_type=connection_type,
            cooling_tools=cooling_tools,
            building=building,
            description=description,
            remarks=remarks,
            status=status,
            image_url=image_url,
            created_at=datetime.utcnow()
        )
        
        db.add(new_facility)
        await db.commit()
        await db.refresh(new_facility)
        
        return {
            "message": "Facility created successfully",
            "facility": {
                "facility_id": new_facility.facility_id,
                "facility_name": new_facility.facility_name,
                "facility_type": new_facility.facility_type,
                "floor_level": new_facility.floor_level,
                "capacity": new_facility.capacity,
                "connection_type": new_facility.connection_type,
                "cooling_tools": new_facility.cooling_tools,
                "building": new_facility.building,
                "description": new_facility.description,
                "remarks": new_facility.remarks,
                "status": new_facility.status,
                "image_url": new_facility.image_url,
                "created_at": new_facility.created_at.isoformat()
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating facility: {str(e)}")

@router.put("/facilities/{facility_id}")
async def update_facility(
    facility_id: int,
    facility_name: Optional[str] = Form(None),
    facility_type: Optional[str] = Form(None),
    floor_level: Optional[str] = Form(None),
    capacity: Optional[int] = Form(None),
    connection_type: Optional[str] = Form(None),
    cooling_tools: Optional[str] = Form(None),
    building: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Update an existing facility"""
    try:
        # Get facility
        result = await db.execute(select(Facility).where(Facility.facility_id == facility_id))
        facility = result.scalar_one_or_none()
        
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        
        # Handle image upload
        if image:
            # Delete old image if exists
            if facility.image_url:
                old_image_path = facility.image_url.replace("/uploads/facility-images/", "")
                old_file_path = os.path.join(UPLOAD_DIR, old_image_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Save new image
            facility.image_url = await save_upload_file(image)
        
        # Update fields
        if facility_name is not None:
            facility.facility_name = facility_name
        if facility_type is not None:
            facility.facility_type = facility_type
        if floor_level is not None:
            facility.floor_level = floor_level
        if capacity is not None:
            facility.capacity = capacity
        if connection_type is not None:
            facility.connection_type = connection_type
        if cooling_tools is not None:
            facility.cooling_tools = cooling_tools
        if building is not None:
            facility.building = building
        if description is not None:
            facility.description = description
        if remarks is not None:
            facility.remarks = remarks
        if status is not None:
            facility.status = status
        
        facility.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(facility)
        
        return {
            "message": "Facility updated successfully",
            "facility": {
                "facility_id": facility.facility_id,
                "facility_name": facility.facility_name,
                "facility_type": facility.facility_type,
                "floor_level": facility.floor_level,
                "capacity": facility.capacity,
                "connection_type": facility.connection_type,
                "cooling_tools": facility.cooling_tools,
                "building": facility.building,
                "description": facility.description,
                "remarks": facility.remarks,
                "status": facility.status,
                "image_url": facility.image_url,
                "updated_at": facility.updated_at.isoformat() if facility.updated_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating facility: {str(e)}")

@router.delete("/facilities/{facility_id}")
async def delete_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete a single facility"""
    try:
        # Get facility
        result = await db.execute(select(Facility).where(Facility.facility_id == facility_id))
        facility = result.scalar_one_or_none()
        
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        
        # Delete image if exists
        if facility.image_url:
            image_path = facility.image_url.replace("/uploads/facility-images/", "")
            file_path = os.path.join(UPLOAD_DIR, image_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete facility
        await db.delete(facility)
        await db.commit()
        
        return {"message": "Facility deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting facility: {str(e)}")

@router.delete("/facilities/bulk-delete")
@router.post("/facilities/bulk-delete")
async def bulk_delete_facilities(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple facilities (supports both DELETE and POST methods)"""
    try:
        if not request.facility_ids:
            raise HTTPException(status_code=400, detail="No facility IDs provided")
        
        # Get facilities to delete
        result = await db.execute(
            select(Facility).where(Facility.facility_id.in_(request.facility_ids))
        )
        facilities = result.scalars().all()
        
        # Delete associated images
        for facility in facilities:
            if facility.image_url:
                image_path = facility.image_url.replace("/uploads/facility-images/", "")
                file_path = os.path.join(UPLOAD_DIR, image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Delete facilities
        await db.execute(
            delete(Facility).where(Facility.facility_id.in_(request.facility_ids))
        )
        await db.commit()
        
        return {
            "message": f"Successfully deleted {len(facilities)} facilities",
            "deleted_count": len(facilities)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting facilities: {str(e)}")

@router.post("/facilities/bulk-import")
async def bulk_import_facilities(
    facilities_data: List[FacilityCreate],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Import multiple facilities at once"""
    try:
        created_facilities = []
        
        for facility_data in facilities_data:
            new_facility = Facility(
                facility_name=facility_data.facility_name,
                facility_type=facility_data.facility_type,
                floor_level=facility_data.floor_level,
                capacity=facility_data.capacity,
                description=facility_data.description,
                status=facility_data.status,
                created_at=datetime.utcnow()
            )
            
            db.add(new_facility)
            created_facilities.append(new_facility)
        
        await db.commit()
        
        # Refresh all created facilities
        for facility in created_facilities:
            await db.refresh(facility)
        
        return {
            "message": f"Successfully imported {len(created_facilities)} facilities",
            "imported_count": len(created_facilities),
            "facilities": [
                {
                    "facility_id": f.facility_id,
                    "facility_name": f.facility_name,
                    "facility_type": f.facility_type,
                    "status": f.status
                }
                for f in created_facilities
            ]
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing facilities: {str(e)}")

@router.post("/facility-logs")
async def create_facility_log(
    log_data: FacilityLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Create a facility log entry
    Note: This endpoint is ready but requires FacilityLog model to be added to database.py
    """
    try:
        # TODO: Uncomment when FacilityLog model is added to database.py
        # from database import FacilityLog
        # 
        # new_log = FacilityLog(
        #     facility_id=log_data.facility_id,
        #     action=log_data.action,
        #     details=log_data.details,
        #     user_email=current_user["email"],
        #     created_at=datetime.utcnow()
        # )
        # 
        # db.add(new_log)
        # await db.commit()
        # await db.refresh(new_log)
        # 
        # return {
        #     "message": "Facility log created successfully",
        #     "log_id": new_log.id
        # }
        
        # Temporary response until FacilityLog model is added
        return {
            "message": "Facility log endpoint ready (add FacilityLog model to database.py to enable)",
            "facility_id": log_data.facility_id,
            "action": log_data.action
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating facility log: {str(e)}")
