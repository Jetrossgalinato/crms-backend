from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from database import get_db, MaintenanceLog, TechnicianMaintenanceLog, User
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
    user_first_name: str
    user_last_name: str
    user_role: str
    checklist_type: str
    log_type: str

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
    
    if user_role not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Not authorized. Role: {current_user.acc_role}")

    # Fetch Student Assistant Logs (MaintenanceLog)
    stmt_student = select(MaintenanceLog, User).join(User, MaintenanceLog.user_id == User.id).order_by(MaintenanceLog.created_at.desc())
    result_student = await db.execute(stmt_student)
    student_logs = result_student.all()

    # Fetch Technician Logs (TechnicianMaintenanceLog)
    stmt_tech = select(TechnicianMaintenanceLog, User).join(User, TechnicianMaintenanceLog.user_id == User.id).order_by(TechnicianMaintenanceLog.created_at.desc())
    result_tech = await db.execute(stmt_tech)
    tech_logs = result_tech.all()
    
    combined_logs = []

    # Process Student Logs
    for log, user in student_logs:
        combined_logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "laboratory": log.laboratory,
            "date": log.date,
            "checklist_data": log.checklist_data,
            "additional_concerns": log.additional_concerns,
            "status": log.status,
            "created_at": log.created_at.isoformat(),
            "user_first_name": user.first_name,
            "user_last_name": user.last_name,
            "user_role": user.acc_role,
            "checklist_type": "Daily", # Default for student logs
            "log_type": "student"
        })

    # Process Technician Logs
    for log, user in tech_logs:
        combined_logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "laboratory": log.laboratory,
            "date": log.date,
            "checklist_data": log.checklist_data,
            "additional_concerns": log.additional_concerns,
            "status": log.status,
            "created_at": log.created_at.isoformat(),
            "user_first_name": user.first_name,
            "user_last_name": user.last_name,
            "user_role": user.acc_role,
            "checklist_type": log.checklist_type,
            "log_type": "technician"
        })

    # Sort combined logs by created_at desc
    combined_logs.sort(key=lambda x: x["created_at"], reverse=True)

    return combined_logs

@router.delete("/maintenance/{log_id}")
async def delete_maintenance_log(
    log_id: int,
    log_type: str,
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

    if log_type == "student":
        stmt = select(MaintenanceLog).where(MaintenanceLog.id == log_id)
        result = await db.execute(stmt)
        log = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        await db.delete(log)
        
    elif log_type == "technician":
        stmt = select(TechnicianMaintenanceLog).where(TechnicianMaintenanceLog.id == log_id)
        result = await db.execute(stmt)
        log = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        await db.delete(log)
        
    else:
        raise HTTPException(status_code=400, detail="Invalid log type")

    await db.commit()
    return {"message": "Log deleted successfully"}


@router.put("/maintenance/{log_id}/status")
async def update_maintenance_status(
    log_id: int,
    status_update: StatusUpdate,
    log_type: str = "student",
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

    if log_type == "student":
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
        
    elif log_type == "technician":
        result = await db.execute(select(TechnicianMaintenanceLog).where(TechnicianMaintenanceLog.id == log_id))
        log = result.scalar_one_or_none()
        
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
            
        log.status = status_update.status
        
        # Notify Technician (optional, since they might be the one confirming or it's a self-check)
        # But if a Dean confirms a Technician's log, we might want to notify.
        if log.user_id != current_user.id:
             await create_notification(
                db,
                user_id=log.user_id,
                title="Maintenance Log Update",
                message=f"Your maintenance log for {log.laboratory} on {log.date} has been {status_update.status.lower()}.",
                type="success" if status_update.status == "Confirmed" else "info"
            )
            
    else:
        raise HTTPException(status_code=400, detail="Invalid log type")
    
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
            message=f"Student Assistant submitted a maintenance log for {log_data.laboratory}.",
            type="info"
        )

    await db.commit()
    await db.refresh(new_log)
    
    return {"message": "Maintenance log submitted successfully", "id": new_log.id}


class TechnicianMaintenanceLogCreate(BaseModel):
    laboratory: str
    date: str
    checklist_type: str
    checklist_data: str
    additional_concerns: str | None = None

class TechnicianMaintenanceLogResponse(BaseModel):
    id: int
    user_id: int
    laboratory: str
    date: str
    checklist_type: str
    checklist_data: str
    additional_concerns: str | None
    status: str
    created_at: str

    class Config:
        orm_mode = True

@router.post("/technician-maintenance", status_code=status.HTTP_201_CREATED)
async def create_technician_maintenance_log(
    log_data: TechnicianMaintenanceLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is Lab Technician
    if current_user.acc_role != "Lab Technician":
        raise HTTPException(status_code=403, detail="Not authorized. Only Lab Technicians can submit this log.")

    new_log = TechnicianMaintenanceLog(
        user_id=current_user.id,
        laboratory=log_data.laboratory,
        date=log_data.date,
        checklist_type=log_data.checklist_type,
        checklist_data=log_data.checklist_data,
        additional_concerns=log_data.additional_concerns
    )
    
    db.add(new_log)
    
    # Notify Admins (Dean, Comlab Adviser, Super Admin)
    # Exclude Lab Technician from receiving their own notification if they are in the admin list?
    # The requirement says "in the notifications lab technician should be displayed not Student Assistant Technician"
    
    stmt = select(User).where(
        or_(
            User.acc_role == "CCIS Dean",
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
            title="New Technician Maintenance Log",
            message=f"Lab Technician submitted a {log_data.checklist_type} maintenance log for {log_data.laboratory}.",
            type="info"
        )

    await db.commit()
    await db.refresh(new_log)
    
    return {"message": "Technician maintenance log submitted successfully", "id": new_log.id}
