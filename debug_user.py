import asyncio
import sys
import os
from sqlalchemy import select

# We are in backend directory
sys.path.append(os.getcwd())

from database import SessionLocal, User

async def check_user():
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == 13))
        user = result.scalar_one_or_none()
        if user:
            print(f"User 13 found: {user.first_name} {user.last_name}")
        else:
            print("User 13 NOT found!")

if __name__ == "__main__":
    asyncio.run(check_user())
