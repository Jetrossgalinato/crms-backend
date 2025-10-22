from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database import get_db, Facility, Booking
from datetime import datetime
from typing import Optional

router = APIRouter()

def calculate_facility_status(facility_id: int, bookings: list) -> str:
    """Calculate facility status based on active bookings"""
    now = datetime.now().date()
    
    for booking in bookings:
        if booking.facility_id == facility_id and booking.status == "Approved":
            try:
                start_date = datetime.strptime(booking.start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(booking.end_date, "%Y-%m-%d").date()
                
                if start_date <= now <= end_date:
                    return "Occupied"
            except:
                continue
    
    return "Available"

@router.get("/facilities")
async def get_facilities(db: AsyncSession = Depends(get_db)):
    """Get all facilities with dynamic status"""
    try:
        # Fetch all facilities
        result = await db.execute(select(Facility))
        facilities = result.scalars().all()
        
        # Fetch all active bookings
        bookings_result = await db.execute(select(Booking))
        bookings = bookings_result.scalars().all()
        
        # Build response with dynamic status
        facilities_list = []
        for facility in facilities:
            status = calculate_facility_status(facility.facility_id, bookings)
            
            # Override with manual status if set to "Under Maintenance"
            if facility.status == "Under Maintenance":
                status = "Under Maintenance"
            
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
                "status": status,
                "image_url": facility.image_url,
                "created_at": facility.created_at.isoformat() if facility.created_at else None,
                "updated_at": facility.updated_at.isoformat() if facility.updated_at else None
            })
        
        return {"facilities": facilities_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching facilities: {str(e)}")
