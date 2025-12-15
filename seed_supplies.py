import asyncio
import sys
import os
import random
from datetime import datetime

# Add the current directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Supply, get_ph_time

async def seed_supplies():
    async with SessionLocal() as session:
        supplies = []
        
        categories = ["Office", "Cleaning", "Electronics", "Medical", "Laboratory", "Sports"]
        stock_units = ["pcs", "boxes", "packs", "liters", "kg", "sets", "rolls"]
        
        print("Generating 500 supply records...")
        
        for i in range(500):
            category = random.choice(categories)
            unit = random.choice(stock_units)
            
            supply = Supply(
                supply_name=f"Supply Item {i+1}",
                description=f"Description for supply item {i+1}",
                category=category,
                quantity=random.randint(0, 500),
                stocking_point=random.randint(10, 50),
                stock_unit=unit,
                facility_id=None, # Keeping it simple
                remarks="Seeded data",
                image_url=None,
                created_at=get_ph_time(),
                updated_at=get_ph_time()
            )
            supplies.append(supply)
            
            if len(supplies) >= 100:
                session.add_all(supplies)
                await session.commit()
                supplies = []
                print(f"Seeded {i+1} supplies...")
        
        if supplies:
            session.add_all(supplies)
            await session.commit()
            print(f"Seeded remaining {len(supplies)} supplies.")
            
        print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_supplies())
