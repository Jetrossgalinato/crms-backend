from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/postgres")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    acc_role = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Pending")
    is_employee = Column(Boolean, nullable=False, default=True)
    is_approved = Column(Boolean, nullable=False, default=False)
    hashed_password = Column(String, nullable=False)

class AccountRequest(Base):
    __tablename__ = "account_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Pending")  # Pending, Approved, Rejected
    department = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    acc_role = Column(String, nullable=True)
    approved_acc_role = Column(String, nullable=True)
    is_supervisor = Column(Boolean, nullable=False, default=False)
    is_intern = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, nullable=False)  # info, success, warning, error
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Facility(Base):
    __tablename__ = "facilities"
    facility_id = Column(Integer, primary_key=True, index=True)
    facility_name = Column(String, nullable=False)
    facility_type = Column(String, nullable=False)
    floor_level = Column(String, nullable=False)
    capacity = Column(Integer, nullable=True)  # Made optional
    connection_type = Column(String, nullable=True)
    cooling_tools = Column(String, nullable=True)
    building = Column(String, nullable=True)
    description = Column(String, nullable=True)
    remarks = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Available")
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    bookers_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.facility_id", ondelete="CASCADE"), nullable=True)
    equipment_id = Column(Integer, nullable=True)
    supply_id = Column(Integer, nullable=True)
    purpose = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    return_date = Column(String, nullable=True)  # Optional for facility bookings
    status = Column(String, nullable=False, default="Pending")
    request_type = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

class Equipment(Base):
    __tablename__ = "equipments"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    name = Column(String, nullable=False)
    po_number = Column(String, nullable=True)
    unit_number = Column(String, nullable=True)
    brand_name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    facility = Column(String, nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.facility_id"), nullable=True)
    category = Column(String, nullable=True)
    status = Column(String, nullable=True)  # Working, In Use, For Repair
    date_acquire = Column(String, nullable=True)
    supplier = Column(String, nullable=True)
    amount = Column(String, nullable=True)
    estimated_life = Column(String, nullable=True)
    item_number = Column(String, nullable=True)
    property_number = Column(String, nullable=True)
    control_number = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    person_liable = Column(String, nullable=True)
    remarks = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    image = Column(String, nullable=True)

class Borrowing(Base):
    __tablename__ = "borrowing"
    id = Column(Integer, primary_key=True, index=True)
    borrowed_item = Column(Integer, ForeignKey("equipments.id", ondelete="CASCADE"), nullable=False)
    borrowers_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    return_date = Column(String, nullable=False)
    request_status = Column(String, nullable=True)  # Pending, Approved, Rejected
    return_status = Column(String, nullable=True)  # Returned, Not Returned, Overdue
    availability = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Supply(Base):
    __tablename__ = "supplies"
    supply_id = Column(Integer, primary_key=True, index=True)
    supply_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    stocking_point = Column(Integer, nullable=False, default=0)
    stock_unit = Column(String, nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.facility_id"), nullable=True)
    remarks = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

class Acquiring(Base):
    __tablename__ = "acquiring"
    id = Column(Integer, primary_key=True, index=True)
    acquirers_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    supply_id = Column(Integer, ForeignKey("supplies.supply_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    purpose = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


