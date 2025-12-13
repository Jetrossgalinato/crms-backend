from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from database import get_db, MaintenanceLog, User
from api.auth import get_current_user
from api.notifications import create_notification
from pydantic import BaseModel
from typing import List

router = APIRouter()

class MaintenanceLogCreate(BaseModel):
    laboratory: str
    date: str
    checklist_data: str
    additional_concerns: str | None = None

class MaintenanceLogResponse(BaseModel):
    id: int
    user_id: int
    laboratory: str
    date: str
    checklist_data: str
    additional_concerns: str | None
    status: str
    created_at: str

    class Config:
        orm_mode = True

class StatusUpdate(BaseModel):
    status: str

@router.get("/maintenance", response_model=List[MaintenanceLogResponse])
async def get_maintenance_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Allow only Super Admin roles to view logs
    # Super Admin roles: CCIS Dean, Lab Technician, Comlab Adviser, Super Admin
    
    allowed_roles = [
        "ccis dean", 
        "lab technician", 
        "comlab adviser", 
        "super admin"
    ]
    
    user_role = current_user.acc_role.strip().lower() if current_user.acc_role else ""
    
    print(f"DEBUG: User {current_user.email} attempting to access maintenance logs. Role: '{current_user.acc_role}' -> Normalized: '{user_role}'")
    
    if user_role not in allowed_roles:
        print(f"DEBUG: Access denied for role '{current_user.acc_role}'")
        raise HTTPException(status_code=403, detail=f"Not authorized. Role: {current_user.acc_role}")

    result = await db.execute(select(MaintenanceLog).order_by(MaintenanceLog.created_at.desc()))
    logs = result.scalars().all()
    
    # Convert datetime to string for response
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "laboratory": log.laboratory,
            "date": log.date,
            "checklist_data": log.checklist_data,
            "additional_concerns": log.additional_concerns,
            "status": log.status,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]

@router.put("/maintenance/{log_id}/status")
async def update_maintenance_status(
    log_id: int,
    status_update: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_roles = [
        "ccis dean", 
        "lab technician", 
        "comlab adviser", 
        "super admin"
    ]
    user_role = current_user.acc_role.strip().lower() if current_user.acc_role else ""

    if user_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(MaintenanceLog).where(MaintenanceLog.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    log.status = status_update.status
    
    # Notify Student Assistant
    await create_notification(
        db,
        user_id=log.user_id,
        title="Maintenance Log Update",
        message=f"Your maintenance log for {log.laboratory} on {log.date} has been {status_update.status.lower()}.",
        type="success" if status_update.status == "Confirmed" else "info"
    )
    
    await db.commit()
    
    return {"message": "Status updated successfully"}

@router.post("/maintenance", status_code=status.HTTP_201_CREATED)
async def create_maintenance_log(
    log_data: MaintenanceLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ideally check for role here
    # if current_user.acc_role != "Student Assistant":
    #     raise HTTPException(status_code=403, detail="Not authorized")

    new_log = MaintenanceLog(
        user_id=current_user.id,
        laboratory=log_data.laboratory,
        date=log_data.date,
        checklist_data=log_data.checklist_data,
        additional_concerns=log_data.additional_concerns
    )
    
    db.add(new_log)
    
    # Notify Admins
    # Find all users with admin roles
    stmt = select(User).where(
        or_(
            User.acc_role == "CCIS Dean",
            User.acc_role == "Lab Technician",
            User.acc_role == "Comlab Adviser",
            User.acc_role == "Super Admin"
        )
    )
    result = await db.execute(stmt)
    admins = result.scalars().all()
    
    for admin in admins:
        await create_notification(
            db,
            user_id=admin.id,
            title="New Maintenance Log",
            message=f"Student Assistant {current_user.first_name} {current_user.last_name} submitted a maintenance log for {log_data.laboratory}.",
            type="info"
        )

    await db.commit()
    await db.refresh(new_log)
    
    return {"message": "Maintenance log submitted successfully", "id": new_log.id}
