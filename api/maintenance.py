from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MaintenanceLog, User
from api.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class MaintenanceLogCreate(BaseModel):
    laboratory: str
    date: str
    checklist_data: str
    additional_concerns: str | None = None

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
