from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, MaintenanceLog, User
from api.auth import get_current_user
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
    # Allow Admin and Staff to view logs
    if current_user.acc_role not in ["Admin", "Staff"]:
        raise HTTPException(status_code=403, detail="Not authorized")

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
    if current_user.acc_role not in ["Admin", "Staff"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(MaintenanceLog).where(MaintenanceLog.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    log.status = status_update.status
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
    await db.commit()
    await db.refresh(new_log)
    
    return {"message": "Maintenance log submitted successfully", "id": new_log.id}
