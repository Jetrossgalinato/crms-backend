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
    is_employee = Column(Integer, nullable=False, default=1)
    is_approved = Column(Integer, nullable=False, default=0)
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


