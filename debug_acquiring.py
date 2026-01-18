import asyncio
import sys
import os
from sqlalchemy import select

# We are in backend directory
sys.path.append(os.getcwd())

from database import SessionLocal, Acquiring, Supply, User

async def check_data():
    async with SessionLocal() as session:
        # Check Acquiring records
        result = await session.execute(select(Acquiring))
        acquiring_records = result.scalars().all()
        print(f"Total Acquiring Records: {len(acquiring_records)}")
        
        for record in acquiring_records:
            print(f"Acquiring ID: {record.id}, Supply ID: {record.supply_id}, Acquirer ID: {record.acquirers_id}")
            
        # Check Supplies
        result = await session.execute(select(Supply).limit(5))
        supplies = result.scalars().all()
        print("\nFirst 5 Supplies:")
        for s in supplies:
             print(f"Supply ID: {s.supply_id}, Name: {s.supply_name}")

if __name__ == "__main__":
    asyncio.run(check_data())
