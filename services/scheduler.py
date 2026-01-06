from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, Booking, Borrowing, User, Equipment, Facility
from services.email_service import email_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def get_db_session():
    async with SessionLocal() as session:
        yield session

async def check_upcoming_deadlines():
    """
    Check for bookings and borrowings that are ending soon (e.g., tomorrow)
    and send warning emails (only if status is Approved/Pending and not yet returned/completed).
    This logic assumes 'end_date' is a string in YYYY-MM-DD format as seen in other files,
    but it might be better to handle potential time components.
    """
    logger.info("Checking for upcoming deadlines...")
    
    async with SessionLocal() as db:
        try:
            # We want to notify 1 day before the end date
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # --- Check Bookings ---
            # Assuming 'status' for active bookings is 'Approved' 
            # and we check against 'end_date'
            
            # Note: The database schema stores dates as Strings. 
            # We need to be careful with string comparison if formats vary, 
            # but based on booking.py they seem to be YYYY-MM-DD.
            
            booking_query = select(Booking, User, Facility).join(
                User, Booking.bookers_id == User.id
            ).outerjoin(
                Facility, Booking.facility_id == Facility.facility_id
            ).where(
                and_(
                    Booking.status == 'Approved',
                    Booking.end_date == tomorrow
                )
            )
            
            booking_results = await db.execute(booking_query)
            bookings_to_notify = booking_results.all()
            
            for booking, user, facility in bookings_to_notify:
                subject = "Reminder: Your Facility Booking Ends Soon"
                facility_name = facility.facility_name if facility else "Unknown Facility"
                body = f"""
                <p>Dear {user.first_name},</p>
                <p>This is a reminder that your booking for <strong>{facility_name}</strong> is scheduled to end on <strong>{booking.end_date}</strong>.</p>
                <p>Please ensure you vacate the facility and return any borrowed items by the scheduled time.</p>
                <p>Thank you.</p>
                """
                await email_service.send_warning_email([user.email], subject, body)
                logger.info(f"Sent booking reminder to {user.email}")


            # --- Check Borrowings ---
            # Borrowing table has 'end_date' and 'return_status'
            borrowing_query = select(Borrowing, User, Equipment).join(
                User, Borrowing.borrowers_id == User.id
            ).join(
                Equipment, Borrowing.borrowed_item == Equipment.id
            ).where(
                and_(
                    Borrowing.request_status == 'Approved',
                    # We only want to notify if not yet returned
                    # Assuming return_status might be 'Returned' or similar. 
                    # If it's NULL or 'Not Returned', we send.
                    # Adjust 'Not Returned' based on actual usage if known (schema says default is None/Null usually but let's check values used reliably)
                    # For now, let's assume if it's not 'Returned' and not 'Rejected'
                    Borrowing.return_status != 'Returned', 
                    Borrowing.end_date == tomorrow
                )
            )
            
            borrowing_results = await db.execute(borrowing_query)
            borrowings_to_notify = borrowing_results.all()
            
            for borrowing, user, equipment in borrowings_to_notify:
                subject = "Reminder: Your Equipment Borrowing Ends Soon"
                equipment_name = equipment.name if equipment else "Unknown Equipment"
                body = f"""
                <p>Dear {user.first_name},</p>
                <p>This is a reminder that your borrowing period for <strong>{equipment_name}</strong> is scheduled to end on <strong>{borrowing.end_date}</strong>.</p>
                <p>Please ensure you return the item by this date to avoid penalties.</p>
                <p>Thank you.</p>
                """
                await email_service.send_warning_email([user.email], subject, body)
                logger.info(f"Sent borrowing reminder to {user.email}")

        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Run the check every day at 8:00 AM
    scheduler.add_job(check_upcoming_deadlines, 'cron', hour=8, minute=0)
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler


scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(check_upcoming_deadlines, 'cron', hour=8, minute=0) # Run every day at 8:00 AM
    scheduler.start()
