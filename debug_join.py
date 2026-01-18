import asyncio
import sys
import os
from sqlalchemy import select

# We are in backend directory
sys.path.append(os.getcwd())

from database import SessionLocal, Acquiring, Supply, User

async def check_data_with_join():
    async with SessionLocal() as session:
        supply_id = 3 # Ballpen
        
        query = (
            select(Acquiring, User)
            .join(User, Acquiring.acquirers_id == User.id)
            .where(Acquiring.supply_id == supply_id)
            .order_by(Acquiring.created_at.desc())
        )
        
        result = await session.execute(query)
        records = result.all()
        
        print(f"Query returned {len(records)} records for Supply ID {supply_id}")
        
        for record in records:
            # record is a Row(Acquiring, User)
            acquiring = record[0]
            user = record[1]
            print(f"ID: {acquiring.id}, User: {user.first_name}")

if __name__ == "__main__":
    asyncio.run(check_data_with_join())
