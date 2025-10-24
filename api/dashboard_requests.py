from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from database import (
    get_db, Borrowing, Booking, Acquiring, Equipment, Facility, Supply, User,
    Notification, ReturnNotification, DoneNotification,
    EquipmentLog, FacilityLog, SupplyLog
)
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
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Pydantic models
class BulkUpdateStatusRequest(BaseModel):
    ids: List[int]
    status: str  # "Approved" or "Rejected"

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class ConfirmReturnRequest(BaseModel):
    notification_id: int
    borrowing_id: int

class RejectReturnRequest(BaseModel):
    notification_id: int

class ConfirmDoneRequest(BaseModel):
    notification_id: int
    booking_id: int

class DismissDoneRequest(BaseModel):
    notification_id: int

# ==================== BORROWING REQUESTS ENDPOINTS ====================

@router.get("/borrowing/requests")
async def get_borrowing_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get paginated borrowing requests with equipment and borrower details"""
    try:
        # Get total count
        count_result = await db.execute(select(func.count(Borrowing.id)))
        total = count_result.scalar() or 0
        
        # Calculate pagination
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # Get borrowing requests with joins
        query = (
            select(Borrowing, Equipment, User)
            .join(Equipment, Borrowing.borrowed_item == Equipment.id)
            .join(User, Borrowing.borrowers_id == User.id)
            .order_by(Borrowing.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await db.execute(query)
        borrowings = result.all()
        
        # Format response
        data = []
        for borrowing, equipment, user in borrowings:
            # Check for return notification
            return_notif_result = await db.execute(
                select(ReturnNotification).where(
                    ReturnNotification.borrowing_id == borrowing.id
                ).order_by(ReturnNotification.created_at.desc())
            )
            return_notif = return_notif_result.scalar_one_or_none()
            
            data.append({
                "id": borrowing.id,
                "borrowers_id": borrowing.borrowers_id,
                "borrowed_item": borrowing.borrowed_item,
                "equipment_name": equipment.name,
                "borrower_name": f"{user.first_name} {user.last_name}",
                "purpose": borrowing.purpose,
                "request_status": borrowing.request_status or "Pending",
                "availability": borrowing.availability or "Available",
                "return_status": borrowing.return_status,
                "start_date": borrowing.start_date,
                "end_date": borrowing.end_date,
                "date_returned": borrowing.return_date if borrowing.return_status == "Returned" else None,
                "created_at": borrowing.created_at.isoformat() if borrowing.created_at else None,
                "return_notification": {
                    "id": return_notif.id,
                    "receiver_name": return_notif.receiver_name,
                    "status": return_notif.status
                } if return_notif else None
            })
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching borrowing requests: {str(e)}")

@router.get("/borrowing/return-notifications")
async def get_return_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Fetch pending return notifications"""
    try:
        query = (
            select(ReturnNotification, Borrowing, Equipment, User)
            .join(Borrowing, ReturnNotification.borrowing_id == Borrowing.id)
            .join(Equipment, Borrowing.borrowed_item == Equipment.id)
            .join(User, Borrowing.borrowers_id == User.id)
            .where(ReturnNotification.status == "pending_confirmation")
            .order_by(ReturnNotification.created_at.desc())
        )
        
        result = await db.execute(query)
        notifications = result.all()
        
        data = []
        for notif, borrowing, equipment, user in notifications:
            data.append({
                "id": notif.id,
                "borrowing_id": notif.borrowing_id,
                "receiver_name": notif.receiver_name,
                "status": notif.status,
                "message": notif.message,
                "created_at": notif.created_at.isoformat() if notif.created_at else None,
                "equipment_name": equipment.name,
                "borrower_name": f"{user.first_name} {user.last_name}"
            })
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching return notifications: {str(e)}")

@router.put("/borrowing/bulk-update-status")
async def bulk_update_borrowing_status(
    request: BulkUpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Approve or reject multiple borrowing requests"""
    try:
        if request.status not in ["Approved", "Rejected"]:
            raise HTTPException(status_code=400, detail="Status must be 'Approved' or 'Rejected'")
        
        if not request.ids:
            raise HTTPException(status_code=400, detail="No IDs provided")
        
        # Get all borrowing requests
        query = select(Borrowing).where(Borrowing.id.in_(request.ids))
        result = await db.execute(query)
        borrowings = result.scalars().all()
        
        updated_count = 0
        for borrowing in borrowings:
            # Update borrowing status
            borrowing.request_status = request.status
            
            # Set availability based on status
            if request.status == "Approved":
                borrowing.availability = "Borrowed"
            elif request.status == "Rejected":
                borrowing.availability = "Available"
            
            # Create notification for borrower
            notification = Notification(
                user_id=borrowing.borrowers_id,
                title=f"Borrowing Request {request.status}",
                message=f"Your borrowing request for equipment has been {request.status.lower()}",
                type="info" if request.status == "Approved" else "warning",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            
            # Log action
            equipment_result = await db.execute(
                select(Equipment).where(Equipment.id == borrowing.borrowed_item)
            )
            equipment = equipment_result.scalar_one_or_none()
            
            if equipment:
                log = EquipmentLog(
                    equipment_id=equipment.id,
                    action=f"Borrowing {request.status}",
                    details=f"Borrowing request ID {borrowing.id} {request.status.lower()} for {equipment.name}",
                    user_email=current_user["email"],
                    created_at=datetime.utcnow()
                )
                db.add(log)
            
            updated_count += 1
        
        await db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Successfully {request.status.lower()} {updated_count} borrowing requests"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating borrowing status: {str(e)}")

@router.delete("/borrowing/bulk-delete")
async def bulk_delete_borrowing_requests(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple borrowing requests"""
    try:
        if not request.ids:
            raise HTTPException(status_code=400, detail="No IDs provided")
        
        # Get borrowings for notifications
        query = select(Borrowing).where(Borrowing.id.in_(request.ids))
        result = await db.execute(query)
        borrowings = result.scalars().all()
        
        # Delete related return_notifications first (foreign key constraint)
        await db.execute(
            delete(ReturnNotification).where(ReturnNotification.borrowing_id.in_(request.ids))
        )
        
        # Create notifications for affected borrowers
        for borrowing in borrowings:
            notification = Notification(
                user_id=borrowing.borrowers_id,
                title="Borrowing Request Deleted",
                message="Your borrowing request has been deleted by an administrator",
                type="warning",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            
            # Log action
            log = EquipmentLog(
                equipment_id=borrowing.borrowed_item,
                action="Borrowing Deleted",
                details=f"Borrowing request ID {borrowing.id} deleted",
                user_email=current_user["email"],
                created_at=datetime.utcnow()
            )
            db.add(log)
        
        # Delete borrowing records
        deleted_result = await db.execute(
            delete(Borrowing).where(Borrowing.id.in_(request.ids))
        )
        deleted_count = deleted_result.rowcount
        
        await db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} borrowing requests"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting borrowing requests: {str(e)}")

@router.post("/borrowing/confirm-return")
async def confirm_equipment_return(
    request: ConfirmReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Confirm equipment return"""
    try:
        # Get return notification
        notif_result = await db.execute(
            select(ReturnNotification).where(ReturnNotification.id == request.notification_id)
        )
        notification = notif_result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Return notification not found")
        
        # Get borrowing record
        borrowing_result = await db.execute(
            select(Borrowing).where(Borrowing.id == request.borrowing_id)
        )
        borrowing = borrowing_result.scalar_one_or_none()
        
        if not borrowing:
            raise HTTPException(status_code=404, detail="Borrowing record not found")
        
        # Update borrowing record
        borrowing.return_status = "Returned"
        borrowing.availability = "Available"
        # Set date_returned to current date (not return_date which is expected return date)
        from datetime import date
        today = date.today()
        
        # Update notification status
        notification.status = "confirmed"
        
        # Create notification for borrower
        borrower_notification = Notification(
            user_id=borrowing.borrowers_id,
            title="Equipment Return Confirmed",
            message="Your equipment return has been confirmed",
            type="success",
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(borrower_notification)
        
        # Log action
        log = EquipmentLog(
            equipment_id=borrowing.borrowed_item,
            action="Return Confirmed",
            details=f"Equipment return confirmed for borrowing ID {borrowing.id}",
            user_email=current_user["email"],
            created_at=datetime.utcnow()
        )
        db.add(log)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Equipment return confirmed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error confirming return: {str(e)}")

@router.post("/borrowing/reject-return")
async def reject_equipment_return(
    request: RejectReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Reject equipment return request"""
    try:
        # Get return notification
        notif_result = await db.execute(
            select(ReturnNotification).where(ReturnNotification.id == request.notification_id)
        )
        notification = notif_result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Return notification not found")
        
        # Get borrowing to notify user
        borrowing_result = await db.execute(
            select(Borrowing).where(Borrowing.id == notification.borrowing_id)
        )
        borrowing = borrowing_result.scalar_one_or_none()
        
        # Update notification status
        notification.status = "rejected"
        
        # Create notification for borrower
        if borrowing:
            borrower_notification = Notification(
                user_id=borrowing.borrowers_id,
                title="Equipment Return Rejected",
                message="Your equipment return has been rejected. Please contact admin.",
                type="error",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(borrower_notification)
            
            # Log action
            log = EquipmentLog(
                equipment_id=borrowing.borrowed_item,
                action="Return Rejected",
                details=f"Equipment return rejected for borrowing ID {borrowing.id}",
                user_email=current_user["email"],
                created_at=datetime.utcnow()
            )
            db.add(log)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Equipment return rejected"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error rejecting return: {str(e)}")

# ==================== BOOKING REQUESTS ENDPOINTS ====================

@router.get("/booking/requests")
async def get_booking_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get paginated booking requests with facility and booker details"""
    try:
        # Get total count
        count_result = await db.execute(select(func.count(Booking.id)))
        total = count_result.scalar() or 0
        
        # Calculate pagination
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # Get booking requests with joins
        query = (
            select(Booking, Facility, User)
            .join(Facility, Booking.facility_id == Facility.facility_id)
            .join(User, Booking.bookers_id == User.id)
            .order_by(Booking.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await db.execute(query)
        bookings = result.all()
        
        # Format response
        data = []
        for booking, facility, user in bookings:
            data.append({
                "id": booking.id,
                "bookers_id": booking.bookers_id,
                "facility_id": booking.facility_id,
                "facility_name": facility.facility_name,
                "booker_name": f"{user.first_name} {user.last_name}",
                "purpose": booking.purpose,
                "status": booking.status or "Pending",
                "start_date": booking.start_date,
                "end_date": booking.end_date,
                "return_date": booking.return_date,
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            })
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching booking requests: {str(e)}")

@router.get("/booking/done-notifications")
async def get_done_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Fetch pending completion notifications"""
    try:
        query = (
            select(DoneNotification, Booking, Facility, User)
            .join(Booking, DoneNotification.booking_id == Booking.id)
            .join(Facility, Booking.facility_id == Facility.facility_id)
            .join(User, Booking.bookers_id == User.id)
            .where(DoneNotification.status == "pending_confirmation")
            .order_by(DoneNotification.created_at.desc())
        )
        
        result = await db.execute(query)
        notifications = result.all()
        
        data = []
        for notif, booking, facility, user in notifications:
            data.append({
                "id": notif.id,
                "booking_id": notif.booking_id,
                "completion_notes": notif.completion_notes,
                "status": notif.status,
                "message": notif.message,
                "created_at": notif.created_at.isoformat() if notif.created_at else None,
                "facility_name": facility.facility_name,
                "booker_name": f"{user.first_name} {user.last_name}"
            })
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching done notifications: {str(e)}")

@router.put("/booking/bulk-update-status")
async def bulk_update_booking_status(
    request: BulkUpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Approve or reject multiple booking requests"""
    try:
        if request.status not in ["Approved", "Rejected"]:
            raise HTTPException(status_code=400, detail="Status must be 'Approved' or 'Rejected'")
        
        if not request.ids:
            raise HTTPException(status_code=400, detail="No IDs provided")
        
        # Get all booking requests
        query = select(Booking).where(Booking.id.in_(request.ids))
        result = await db.execute(query)
        bookings = result.scalars().all()
        
        updated_count = 0
        for booking in bookings:
            # Update booking status
            booking.status = request.status
            booking.updated_at = datetime.utcnow()
            
            # Create notification for booker
            notification = Notification(
                user_id=booking.bookers_id,
                title=f"Booking Request {request.status}",
                message=f"Your facility booking request has been {request.status.lower()}",
                type="info" if request.status == "Approved" else "warning",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            
            # Log action
            log = FacilityLog(
                facility_id=booking.facility_id,
                action=f"Booking {request.status}",
                details=f"Booking request ID {booking.id} {request.status.lower()}",
                user_email=current_user["email"],
                created_at=datetime.utcnow()
            )
            db.add(log)
            
            updated_count += 1
        
        await db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Successfully {request.status.lower()} {updated_count} booking requests"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating booking status: {str(e)}")

@router.delete("/booking/bulk-delete")
async def bulk_delete_booking_requests(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple booking requests"""
    try:
        if not request.ids:
            raise HTTPException(status_code=400, detail="No IDs provided")
        
        # Get bookings for notifications
        query = select(Booking).where(Booking.id.in_(request.ids))
        result = await db.execute(query)
        bookings = result.scalars().all()
        
        # Create notifications for affected bookers
        for booking in bookings:
            notification = Notification(
                user_id=booking.bookers_id,
                title="Booking Request Deleted",
                message="Your booking request has been deleted by an administrator",
                type="warning",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            
            # Log action
            log = FacilityLog(
                facility_id=booking.facility_id,
                action="Booking Deleted",
                details=f"Booking request ID {booking.id} deleted",
                user_email=current_user["email"],
                created_at=datetime.utcnow()
            )
            db.add(log)
        
        # Delete booking records
        deleted_result = await db.execute(
            delete(Booking).where(Booking.id.in_(request.ids))
        )
        deleted_count = deleted_result.rowcount
        
        await db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} booking requests"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting booking requests: {str(e)}")

@router.post("/booking/confirm-done")
async def confirm_booking_completion(
    request: ConfirmDoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Confirm booking completion"""
    try:
        # Get done notification
        notif_result = await db.execute(
            select(DoneNotification).where(DoneNotification.id == request.notification_id)
        )
        notification = notif_result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Done notification not found")
        
        # Get booking record
        booking_result = await db.execute(
            select(Booking).where(Booking.id == request.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking record not found")
        
        # Update booking status
        booking.status = "Completed"
        booking.updated_at = datetime.utcnow()
        
        # Update notification status
        notification.status = "confirmed"
        
        # Create notification for booker
        booker_notification = Notification(
            user_id=booking.bookers_id,
            title="Booking Completion Confirmed",
            message="Your booking completion has been confirmed",
            type="success",
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(booker_notification)
        
        # Log action
        log = FacilityLog(
            facility_id=booking.facility_id,
            action="Booking Completed",
            details=f"Booking completion confirmed for booking ID {booking.id}",
            user_email=current_user["email"],
            created_at=datetime.utcnow()
        )
        db.add(log)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Booking completion confirmed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error confirming booking completion: {str(e)}")

@router.post("/booking/dismiss-done")
async def dismiss_booking_completion(
    request: DismissDoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Dismiss booking completion notification"""
    try:
        # Get done notification
        notif_result = await db.execute(
            select(DoneNotification).where(DoneNotification.id == request.notification_id)
        )
        notification = notif_result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Done notification not found")
        
        # Get booking to notify user
        booking_result = await db.execute(
            select(Booking).where(Booking.id == notification.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        
        # Update notification status
        notification.status = "dismissed"
        
        # Create notification for booker
        if booking:
            booker_notification = Notification(
                user_id=booking.bookers_id,
                title="Booking Completion Dismissed",
                message="Your booking completion notification has been dismissed",
                type="info",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(booker_notification)
            
            # Log action
            log = FacilityLog(
                facility_id=booking.facility_id,
                action="Booking Completion Dismissed",
                details=f"Booking completion dismissed for booking ID {booking.id}",
                user_email=current_user["email"],
                created_at=datetime.utcnow()
            )
            db.add(log)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Booking completion dismissed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error dismissing booking completion: {str(e)}")

# ==================== ACQUIRING REQUESTS ENDPOINTS ====================

@router.get("/acquiring/requests")
async def get_acquiring_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get paginated acquiring requests with supply and acquirer details"""
    try:
        # Get total count
        count_result = await db.execute(select(func.count(Acquiring.id)))
        total = count_result.scalar() or 0
        
        # Calculate pagination
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # Get acquiring requests with joins
        query = (
            select(Acquiring, Supply, User, Facility)
            .join(Supply, Acquiring.supply_id == Supply.supply_id)
            .join(User, Acquiring.acquirers_id == User.id)
            .outerjoin(Facility, Supply.facility_id == Facility.facility_id)
            .order_by(Acquiring.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await db.execute(query)
        acquirings = result.all()
        
        # Format response
        data = []
        for acquiring, supply, user, facility in acquirings:
            data.append({
                "id": acquiring.id,
                "acquirers_id": acquiring.acquirers_id,
                "supply_id": acquiring.supply_id,
                "supply_name": supply.supply_name,
                "acquirer_name": f"{user.first_name} {user.last_name}",
                "facility_name": facility.facility_name if facility else None,
                "quantity": acquiring.quantity,
                "purpose": acquiring.purpose,
                "status": acquiring.status or "Pending",
                "created_at": acquiring.created_at.isoformat() if acquiring.created_at else None
            })
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching acquiring requests: {str(e)}")

@router.put("/acquiring/bulk-update-status")
async def bulk_update_acquiring_status(
    request: BulkUpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Approve or reject multiple acquiring requests"""
    try:
        if request.status not in ["Approved", "Rejected"]:
            raise HTTPException(status_code=400, detail="Status must be 'Approved' or 'Rejected'")
        
        if not request.ids:
            raise HTTPException(status_code=400, detail="No IDs provided")
        
        # Get all acquiring requests
        query = select(Acquiring).where(Acquiring.id.in_(request.ids))
        result = await db.execute(query)
        acquirings = result.scalars().all()
        
        updated_count = 0
        for acquiring in acquirings:
            # If approving, check and deduct supply quantity
            if request.status == "Approved":
                supply_result = await db.execute(
                    select(Supply).where(Supply.supply_id == acquiring.supply_id)
                )
                supply = supply_result.scalar_one_or_none()
                
                if not supply:
                    raise HTTPException(status_code=404, detail=f"Supply ID {acquiring.supply_id} not found")
                
                # Check if sufficient quantity
                if supply.quantity < acquiring.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient quantity for supply {supply.supply_name}. Available: {supply.quantity}, Requested: {acquiring.quantity}"
                    )
                
                # Deduct quantity
                supply.quantity -= acquiring.quantity
                supply.updated_at = datetime.utcnow()
            
            # Update acquiring status
            acquiring.status = request.status
            acquiring.updated_at = datetime.utcnow()
            
            # Create notification for acquirer
            notification = Notification(
                user_id=acquiring.acquirers_id,
                title=f"Acquiring Request {request.status}",
                message=f"Your supply acquiring request has been {request.status.lower()}",
                type="info" if request.status == "Approved" else "warning",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            
            # Log action
            log = SupplyLog(
                supply_id=acquiring.supply_id,
                action=f"Acquiring {request.status}",
                details=f"Acquiring request ID {acquiring.id} {request.status.lower()}, quantity: {acquiring.quantity}",
                user_email=current_user["email"],
                created_at=datetime.utcnow()
            )
            db.add(log)
            
            updated_count += 1
        
        await db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Successfully {request.status.lower()} {updated_count} acquiring requests"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating acquiring status: {str(e)}")

@router.delete("/acquiring/bulk-delete")
async def bulk_delete_acquiring_requests(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Delete multiple acquiring requests"""
    try:
        if not request.ids:
            raise HTTPException(status_code=400, detail="No IDs provided")
        
        # Get acquirings for notifications
        query = select(Acquiring).where(Acquiring.id.in_(request.ids))
        result = await db.execute(query)
        acquirings = result.scalars().all()
        
        # Create notifications for affected acquirers
        for acquiring in acquirings:
            notification = Notification(
                user_id=acquiring.acquirers_id,
                title="Acquiring Request Deleted",
                message="Your acquiring request has been deleted by an administrator",
                type="warning",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            
            # Log action
            log = SupplyLog(
                supply_id=acquiring.supply_id,
                action="Acquiring Deleted",
                details=f"Acquiring request ID {acquiring.id} deleted",
                user_email=current_user["email"],
                created_at=datetime.utcnow()
            )
            db.add(log)
        
        # Delete acquiring records
        deleted_result = await db.execute(
            delete(Acquiring).where(Acquiring.id.in_(request.ids))
        )
        deleted_count = deleted_result.rowcount
        
        await db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} acquiring requests"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting acquiring requests: {str(e)}")
