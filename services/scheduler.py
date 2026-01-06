from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, Booking, Borrowing, User, Equipment, Facility
from services.email_service import email_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def parse_date_flexible(date_str):
    """Parses date string that might be YYYY-MM-DD or YYYY-MM-DD HH:MM or with T separator"""
    if not date_str:
        return None
    
    clean_str = date_str.strip()
    
    # Try formats with time
    if 'T' in clean_str:
        try:
            return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass
    
    if ' ' in clean_str and ':' in clean_str:
        try:
            return datetime.strptime(clean_str, "%Y-%m-%d %H:%M")
        except ValueError:
            pass
            
    # Fallback to date only
    try:
        return datetime.strptime(clean_str, "%Y-%m-%d")
    except ValueError:
        return None

async def get_db_session():
    async with SessionLocal() as session:
        yield session

async def check_upcoming_deadlines():
    """
    Check for bookings and borrowings that are ending soon (e.g., within 24 hours from now)
    and send warning emails.
    """
    logger.info("Checking for upcoming deadlines...")
    
    async with SessionLocal() as db:
        try:
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            
            # --- Check Bookings ---
            # Fetch all active bookings to filter in python (safest for mixed date formats)
            booking_query = select(Booking, User, Facility).join(
                User, Booking.bookers_id == User.id
            ).outerjoin(
                Facility, Booking.facility_id == Facility.facility_id
            ).where(
                Booking.status == 'Approved' # Only process approved bookings
            )
            
            booking_results = await db.execute(booking_query)
            active_bookings = booking_results.all()
            
            for booking, user, facility in active_bookings:
                end_dt = parse_date_flexible(booking.end_date)
                if not end_dt:
                    continue
                
                # Check if end date is within the next 24 hours (Yellow zone) and in the future
                # Or specifically match "tomorrow" logic if preferred. 
                # User asked for logic matching "End date is near (Yellow)"
                
                # Logic: If 0 < (end_date - now) <= 24 hours
                time_diff = end_dt - now
                if timedelta(hours=0) < time_diff <= timedelta(hours=24):
                     subject = "Reminder: Your Facility Booking Ends Soon"
                     facility_name = facility.facility_name if facility else "Unknown Facility"
                     body = f"""
                        <p>Dear {user.first_name},</p>
                        <p>This is a reminder that your booking for <strong>{facility_name}</strong> is ending soon on <strong>{booking.end_date}</strong>.</p>
                        <p>Please ensure you vacate the facility on time.</p>
                        <p>Thank you.</p>
                     """
                     await email_service.send_warning_email([user.email], subject, body)
                     logger.info(f"Sent booking reminder to {user.email}")


            # --- Check Borrowings ---
            borrowing_query = select(Borrowing, User, Equipment).join(
                User, Borrowing.borrowers_id == User.id
            ).join(
                Equipment, Borrowing.borrowed_item == Equipment.id
            ).where(
                and_(
                    Borrowing.request_status == 'Approved', # Only process approved borrowings
                    or_(Borrowing.return_status == None, Borrowing.return_status != 'Returned')
                )
            )
            
            borrowing_results = await db.execute(borrowing_query)
            active_borrowings = borrowing_results.all()
            
            for borrowing, user, equipment in active_borrowings:
                end_dt = parse_date_flexible(borrowing.end_date)
                if not end_dt:
                    continue
                    
                time_diff = end_dt - now
                if timedelta(hours=0) < time_diff <= timedelta(hours=24):
                    subject = "Reminder: Your Equipment Borrowing Ends Soon"
                    equipment_name = equipment.name if equipment else "Unknown Equipment"
                    body = f"""
                    <p>Dear {user.first_name},</p>
                    <p>This is a reminder that your borrowing period for <strong>{equipment_name}</strong> is scheduled to end on <strong>{borrowing.end_date}</strong>.</p>
                    <p>Please ensure you return the item by this date.</p>
                    <p>Thank you.</p>
                    """
                    await email_service.send_warning_email([user.email], subject, body)
                    logger.info(f"Sent borrowing reminder to {user.email}")

        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")

async def check_overdue_deadlines():
    """
    Check for bookings and borrowings that are past their end date (Red zone)
    and send overdue emails.
    """
    logger.info("Checking for overdue items...")
    
    async with SessionLocal() as db:
        try:
            now = datetime.now()
            
            # --- Check Overdue Bookings ---
            booking_query = select(Booking, User, Facility).join(
                User, Booking.bookers_id == User.id
            ).outerjoin(
                Facility, Booking.facility_id == Facility.facility_id
            ).where(
                Booking.status == 'Approved' # Only process approved bookings
            )
            
            booking_results = await db.execute(booking_query)
            active_bookings = booking_results.all()
            
            for booking, user, facility in active_bookings:
                end_dt = parse_date_flexible(booking.end_date)
                if not end_dt:
                    continue
                
                # Check if end date is in the past
                if end_dt < now:
                    subject = "URGENT: Facility Booking Overdue"
                    facility_name = facility.facility_name if facility else "Unknown Facility"
                    body = f"""
                    <p>Dear {user.first_name},</p>
                    <p style="color: red;"><strong>This is an urgent notification.</strong></p>
                    <p>Your booking for <strong>{facility_name}</strong> ended on <strong>{booking.end_date}</strong> and is now OVERDUE.</p>
                    <p>Please vacate the facility immediately and contact the administrator.</p>
                    <p>Thank you.</p>
                    """
                    await email_service.send_warning_email([user.email], subject, body)
                    logger.info(f"Sent booking overdue notice to {user.email}")

            # --- Check Overdue Borrowings ---
            borrowing_query = select(Borrowing, User, Equipment).join(
                User, Borrowing.borrowers_id == User.id
            ).join(
                Equipment, Borrowing.borrowed_item == Equipment.id
            ).where(
                and_(
                    Borrowing.request_status == 'Approved', # Only process approved borrowings
                    or_(Borrowing.return_status == None, Borrowing.return_status != 'Returned')
                )
            )
            
            borrowing_results = await db.execute(borrowing_query)
            active_borrowings = borrowing_results.all()
            
            for borrowing, user, equipment in active_borrowings:
                end_dt = parse_date_flexible(borrowing.end_date)
                if not end_dt:
                    continue
                
                if end_dt < now:
                    subject = "URGENT: Equipment Return Overdue"
                    equipment_name = equipment.name if equipment else "Unknown Equipment"
                    body = f"""
                    <p>Dear {user.first_name},</p>
                    <p style="color: red;"><strong>This is an urgent notification.</strong></p>
                    <p>Your borrowed item <strong>{equipment_name}</strong> was due on <strong>{borrowing.end_date}</strong> and is now OVERDUE.</p>
                    <p>Please return the item immediately to avoid further penalties.</p>
                    <p>Thank you.</p>
                    """
                    await email_service.send_warning_email([user.email], subject, body)
                    logger.info(f"Sent borrowing overdue notice to {user.email}")

        except Exception as e:
            logger.error(f"Error checking overdue deadlines: {e}")

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Run the warning check every day at 8:00 AM
    scheduler.add_job(check_upcoming_deadlines, 'cron', hour=8, minute=0)
    
    # Run the overdue check every day at 8:05 AM
    scheduler.add_job(check_overdue_deadlines, 'cron', hour=8, minute=5)
    
    scheduler.start()
    logger.info("Scheduler started with warning and overdue checks")
    return scheduler

