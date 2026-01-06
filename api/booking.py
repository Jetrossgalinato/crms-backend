from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from database import get_db, Booking, User, Facility
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from api.auth_utils import get_current_user, get_philippine_time

router = APIRouter()

class BookingCreate(BaseModel):
    bookers_id: int
    facility_id: int
    purpose: str
    start_date: str
    end_date: str
    return_date: Optional[str] = None  # Optional for facility bookings

@router.post("/booking")
async def create_booking(
    booking: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new facility booking request"""
    try:
        # Validate dates - support both YYYY-MM-DD and ISO datetime formats
        try:
            # Try parsing as datetime first (handles ISO format like 2025-10-23T15:03:23.000Z)
            # If it fails, try parsing as date only (YYYY-MM-DD)
            def parse_date_flexible(date_str):
                """Parse date from either YYYY-MM-DD or ISO datetime format"""
                if not date_str:
                    return None
                # Clean up string
                clean_str = date_str.split('.')[0].split('Z')[0].split('+')[0]
                
                try:
                    if 'T' in clean_str:
                         # Handle YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM
                        if len(clean_str.split(':')) == 2:
                            return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M")
                        return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
                    elif ' ' in clean_str:
                         # Handle YYYY-MM-DD HH:MM:SS or YYYY-MM-DD HH:MM
                        if len(clean_str.split(':')) == 2:
                            return datetime.strptime(clean_str, "%Y-%m-%d %H:%M")
                        return datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
                    else:
                         return datetime.strptime(clean_str, "%Y-%m-%d")
                except ValueError:
                     # Fallback to date only if complex parsing fails
                     try:
                        return datetime.strptime(clean_str.split('T')[0].split(' ')[0], "%Y-%m-%d")
                     except ValueError as e:
                         raise ValueError(f"Invalid date format: {date_str}")
            
            start_date = parse_date_flexible(booking.start_date)
            end_date = parse_date_flexible(booking.end_date)
            return_date = parse_date_flexible(booking.return_date) if booking.return_date else None
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD or ISO datetime format: {str(e)}")
        
        # Check if dates are logical
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
        
        # Only validate return_date if it's provided
        if return_date and end_date > return_date:
            raise HTTPException(status_code=400, detail="Return date must be after or equal to end date")
        
        # Check if start date is in the past
        if start_date.date() < get_philippine_time().date():
            raise HTTPException(status_code=400, detail="Start date cannot be in the past")
        
        # Verify user exists
        user_result = await db.execute(
            select(User).where(User.id == booking.bookers_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify facility exists
        facility_result = await db.execute(
            select(Facility).where(Facility.facility_id == booking.facility_id)
        )
        facility = facility_result.scalar_one_or_none()
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        
        # Check for booking conflicts (overlapping approved bookings)
        # Convert dates to string format for comparison - Use simpler format for query
        # Ideally, DB should store timestamps for proper comparison
        
        # When checking overlap: 
        # Existing.start < New.End AND Existing.End > New.Start
        # We'll stick to string comparison for now if Schema is VARCHAR
        # If storing full datetime, we should format as such
        if start_date.hour == 0 and start_date.minute == 0 and start_date.second == 0:
             start_date_str = start_date.strftime("%Y-%m-%d")
        else:
             start_date_str = start_date.strftime("%Y-%m-%d %H:%M")
             
        if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
             end_date_str = end_date.strftime("%Y-%m-%d")
        else:
             end_date_str = end_date.strftime("%Y-%m-%d %H:%M")

        conflict_query = select(Booking).where(
            and_(
                Booking.facility_id == booking.facility_id,
                Booking.status == "Approved",
                or_(
                    # New booking starts during existing booking
                    and_(
                        Booking.start_date <= start_date_str,
                        Booking.end_date >= start_date_str
                    ),
                    # New booking ends during existing booking
                    and_(
                        Booking.start_date <= end_date_str,
                        Booking.end_date >= end_date_str
                    ),
                    # New booking completely contains existing booking
                    and_(
                        Booking.start_date >= start_date_str,
                        Booking.end_date <= end_date_str
                    )
                )
            )
        )
        
        conflict_result = await db.execute(conflict_query)
        conflict = conflict_result.scalar_one_or_none()
        
        if conflict:
            raise HTTPException(
                status_code=409,
                detail="Facility is already booked for the selected dates"
            )
        
        # Create new booking - store dates in proper format with time if present
        # If time is 00:00:00, we might want to store just date to be compatible with old data?
        # But user wants time. Let's store full format if time exists.
        
        formatted_start = start_date.strftime("%Y-%m-%d %H:%M") if (start_date.hour != 0 or start_date.minute != 0) else start_date.strftime("%Y-%m-%d")
        formatted_end = end_date.strftime("%Y-%m-%d %H:%M") if (end_date.hour != 0 or end_date.minute != 0) else end_date.strftime("%Y-%m-%d")
        formatted_return = None
        if return_date:
             formatted_return = return_date.strftime("%Y-%m-%d %H:%M") if (return_date.hour != 0 or return_date.minute != 0) else return_date.strftime("%Y-%m-%d")

        new_booking = Booking(
            bookers_id=booking.bookers_id,
            facility_id=booking.facility_id,
            purpose=booking.purpose,
            start_date=formatted_start,
            end_date=formatted_end,
            return_date=formatted_return,
            status="Pending",
            request_type="Facility",
            created_at=get_philippine_time()
        )
        
        db.add(new_booking)
        await db.commit()
        await db.refresh(new_booking)
        
        return {
            "message": "Booking request created successfully",
            "booking": {
                "id": new_booking.id,
                "bookers_id": new_booking.bookers_id,
                "facility_id": new_booking.facility_id,
                "purpose": new_booking.purpose,
                "start_date": new_booking.start_date,
                "end_date": new_booking.end_date,
                "return_date": new_booking.return_date,
                "status": new_booking.status,
                "request_type": new_booking.request_type,
                "created_at": new_booking.created_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating booking: {str(e)}")
