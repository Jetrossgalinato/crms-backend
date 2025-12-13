import asyncio
import sys
import os

# Add the current directory to sys.path to allow imports
# seed command: ./venv/bin/python seed_super_admins.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, User
from api.auth_utils import get_password_hash
from sqlalchemy import select

async def seed_super_admins():
    async with SessionLocal() as session:
        admins = [
            {
                "first_name": "Ronnel",
                "last_name": "Cacho",
                "email": "rocacho@gmail.com",
                "password": "Password123!",
                "department": "BSIT",
                "phone_number": "09123456789",
                "acc_role": "Comlab Adviser",
                "status": "Approved",
                "is_employee": True,
                "is_approved": True
            },
            {
                "first_name": "Jetross",
                "last_name": "Galinato",
                "email": "jetrossgalinato@email.com",
                "password": "Password123!",
                "department": "BSIT",
                "phone_number": "09123456789",
                "acc_role": "Lab Technician",
                "status": "Approved",
                "is_employee": True,
                "is_approved": True
            }
        ]

        for admin_data in admins:
            # Check if user exists
            result = await session.execute(select(User).where(User.email == admin_data["email"]))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"User {admin_data['email']} already exists.")
                continue

            hashed_password = get_password_hash(admin_data["password"])
            new_user = User(
                email=admin_data["email"],
                first_name=admin_data["first_name"],
                last_name=admin_data["last_name"],
                department=admin_data["department"],
                phone_number=admin_data["phone_number"],
                acc_role=admin_data["acc_role"],
                status=admin_data["status"],
                is_employee=admin_data["is_employee"],
                is_approved=admin_data["is_approved"],
                hashed_password=hashed_password
            )
            session.add(new_user)
            print(f"Created super admin: {admin_data['first_name']} {admin_data['last_name']} ({admin_data['email']})")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_super_admins())
