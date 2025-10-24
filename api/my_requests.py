from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from database import get_db, Borrowing, Booking, Acquiring, Equipment, Facility, Supply, User, Notification, ReturnNotification, DoneNotification
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from jose import JWTError, jwt
from api.auth_utils import SECRET_KEY, ALGORITHM
import math

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
        return {"email": email, "user_id": payload.get("user_id")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Pydantic models
class MarkReturnedRequest(BaseModel):
    borrowing_ids: List[int]
    receiver_name: str

class MarkDoneRequest(BaseModel):
    booking_ids: List[int]
    completion_notes: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    ids: List[int]

# Helper function to get user_id from email
async def get_user_id_from_email(email: str, db: AsyncSession) -> int:
    """Get user ID from email"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id

@router.get("/borrowing/my-requests")
async def get_my_borrowing_requests(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get paginated borrowing requests for authenticated user"""
    try:
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Get total count
        count_query = select(func.count(Borrowing.id)).where(Borrowing.borrowers_id == user_id)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Calculate pagination
        page_size = 10
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # Get borrowing requests
        query = (
            select(Borrowing, Equipment)
            .join(Equipment, Borrowing.borrowed_item == Equipment.id)
            .where(Borrowing.borrowers_id == user_id)
            .order_by(Borrowing.id.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await db.execute(query)
        borrowings = result.all()
        
        # Format response
        data = []
        for borrowing, equipment in borrowings:
            data.append({
                "id": borrowing.id,
                "status": borrowing.request_status or "Pending",
                "equipment_name": equipment.name,
                "quantity": 1,  # Default quantity
                "borrow_date": borrowing.start_date,
                "expected_return_date": borrowing.end_date,
                "purpose": borrowing.purpose,
                "receiver_name": None  # Will be updated when returned
            })
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching borrowing requests: {str(e)}")

@router.get("/booking/my-requests")
async def get_my_booking_requests(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get paginated booking requests for authenticated user"""
    try:
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Get total count
        count_query = select(func.count(Booking.id)).where(Booking.bookers_id == user_id)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Calculate pagination
        page_size = 10
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # Get booking requests
        query = (
            select(Booking, Facility)
            .join(Facility, Booking.facility_id == Facility.facility_id)
            .where(Booking.bookers_id == user_id)
            .order_by(Booking.id.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await db.execute(query)
        bookings = result.all()
        
        # Format response
        data = []
        for booking, facility in bookings:
            # Extract time from date if it includes time, otherwise use default times
            start_time = "09:00"
            end_time = "17:00"
            booking_date = booking.start_date
            
            # If start_date contains time info (e.g., "2024-01-20 09:00"), split it
            if booking.start_date and " " in booking.start_date:
                booking_date, start_time = booking.start_date.split(" ", 1)
            if booking.end_date and " " in booking.end_date:
                _, end_time = booking.end_date.split(" ", 1)
            
            data.append({
                "id": booking.id,
                "status": booking.status or "Pending",
                "facility_name": facility.facility_name,
                "booking_date": booking_date,
                "start_time": start_time,
                "end_time": end_time,
                "purpose": booking.purpose
            })
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching booking requests: {str(e)}")

@router.get("/acquiring/my-requests")
async def get_my_acquiring_requests(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get paginated acquiring requests for authenticated user"""
    try:
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Get total count
        count_query = select(func.count(Acquiring.id)).where(Acquiring.acquirers_id == user_id)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Calculate pagination
        page_size = 10
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # Get acquiring requests
        query = (
            select(Acquiring, Supply)
            .join(Supply, Acquiring.supply_id == Supply.supply_id)
            .where(Acquiring.acquirers_id == user_id)
            .order_by(Acquiring.id.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await db.execute(query)
        acquirings = result.all()
        
        # Format response
        data = []
        for acquiring, supply in acquirings:
            data.append({
                "id": acquiring.id,
                "supply_name": supply.supply_name,
                "quantity": acquiring.quantity,
                "request_date": acquiring.created_at.strftime("%Y-%m-%d") if acquiring.created_at else None,
                "status": acquiring.status or "Pending",
                "purpose": acquiring.purpose or ""
            })
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching acquiring requests: {str(e)}")

@router.post("/borrowing/mark-returned")
async def mark_borrowing_returned(
    request: MarkReturnedRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Mark borrowing items as returned - creates return notification for admin"""
    try:
        # Validate receiver_name
        if not request.receiver_name or not request.receiver_name.strip():
            raise HTTPException(status_code=400, detail="receiver_name is required")
        
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Validate all borrowing IDs belong to user
        for borrowing_id in request.borrowing_ids:
            result = await db.execute(
                select(Borrowing).where(
                    Borrowing.id == borrowing_id,
                    Borrowing.borrowers_id == user_id
                )
            )
            borrowing = result.scalar_one_or_none()
            if not borrowing:
                raise HTTPException(
                    status_code=404,
                    detail=f"Borrowing ID {borrowing_id} not found or doesn't belong to you"
                )
        
        # Create return notifications for admin review
        for borrowing_id in request.borrowing_ids:
            # Create ReturnNotification
            return_notif = ReturnNotification(
                borrowing_id=borrowing_id,
                receiver_name=request.receiver_name.strip(),
                status="pending_confirmation",
                message=f"Equipment returned by {current_user['email']}",
                created_at=datetime.utcnow()
            )
            db.add(return_notif)
            
            # Also create admin notification
            admin_notification = Notification(
                user_id=1,  # Admin user ID
                title="Equipment Return Notification",
                message=f"User {current_user['email']} reported equipment return. Receiver: {request.receiver_name}",
                type="info",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(admin_notification)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Return notification sent successfully",
            "notified_count": len(request.borrowing_ids)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking as returned: {str(e)}")

@router.post("/booking/mark-done")
async def mark_booking_done(
    request: MarkDoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Mark booking as done - creates done notification for admin"""
    try:
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Validate all booking IDs belong to user
        for booking_id in request.booking_ids:
            result = await db.execute(
                select(Booking).where(
                    Booking.id == booking_id,
                    Booking.bookers_id == user_id
                )
            )
            booking = result.scalar_one_or_none()
            if not booking:
                raise HTTPException(
                    status_code=404,
                    detail=f"Booking ID {booking_id} not found or doesn't belong to you"
                )
        
        # Create done notifications for admin review
        notes = request.completion_notes or "No notes provided"
        for booking_id in request.booking_ids:
            # Create DoneNotification
            done_notif = DoneNotification(
                booking_id=booking_id,
                completion_notes=notes,
                status="pending_confirmation",
                message=f"Booking completed by {current_user['email']}",
                created_at=datetime.utcnow()
            )
            db.add(done_notif)
            
            # Also create admin notification
            admin_notification = Notification(
                user_id=1,  # Admin user ID
                title="Booking Completion Notification",
                message=f"User {current_user['email']} marked booking as done. Notes: {notes}",
                type="info",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(admin_notification)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Booking completion notification sent",
            "notified_count": len(request.booking_ids)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking booking as done: {str(e)}")

@router.delete("/borrowing/bulk-delete")
async def bulk_delete_borrowing(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple borrowing requests"""
    try:
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Validate ownership and check status
        for borrowing_id in request.ids:
            result = await db.execute(
                select(Borrowing).where(Borrowing.id == borrowing_id)
            )
            borrowing = result.scalar_one_or_none()
            
            if not borrowing:
                raise HTTPException(status_code=404, detail=f"Borrowing ID {borrowing_id} not found")
            
            if borrowing.borrowers_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete requests that don't belong to you"
                )
            
            if borrowing.request_status == "Approved":
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete approved requests"
                )
        
        # Delete borrowings
        await db.execute(
            delete(Borrowing).where(Borrowing.id.in_(request.ids))
        )
        await db.commit()
        
        return {
            "success": True,
            "deleted_count": len(request.ids),
            "message": "Borrowing requests deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting borrowing requests: {str(e)}")

@router.delete("/booking/bulk-delete")
async def bulk_delete_booking(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple booking requests"""
    try:
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Validate ownership and check status
        for booking_id in request.ids:
            result = await db.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            
            if not booking:
                raise HTTPException(status_code=404, detail=f"Booking ID {booking_id} not found")
            
            if booking.bookers_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete requests that don't belong to you"
                )
            
            if booking.status == "Approved":
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete approved requests"
                )
        
        # Delete bookings
        await db.execute(
            delete(Booking).where(Booking.id.in_(request.ids))
        )
        await db.commit()
        
        return {
            "success": True,
            "deleted_count": len(request.ids),
            "message": "Booking requests deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting booking requests: {str(e)}")

@router.delete("/acquiring/bulk-delete")
async def bulk_delete_acquiring(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple acquiring requests"""
    try:
        # Get user ID
        user_id = await get_user_id_from_email(current_user["email"], db)
        
        # Validate ownership and check status
        for acquiring_id in request.ids:
            result = await db.execute(
                select(Acquiring).where(Acquiring.id == acquiring_id)
            )
            acquiring = result.scalar_one_or_none()
            
            if not acquiring:
                raise HTTPException(status_code=404, detail=f"Acquiring ID {acquiring_id} not found")
            
            if acquiring.acquirers_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete requests that don't belong to you"
                )
            
            if acquiring.status == "Approved":
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete approved requests"
                )
        
        # Delete acquirings
        await db.execute(
            delete(Acquiring).where(Acquiring.id.in_(request.ids))
        )
        await db.commit()
        
        return {
            "success": True,
            "deleted_count": len(request.ids),
            "message": "Acquiring requests deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting acquiring requests: {str(e)}")
