import asyncio
import sys
import os
import random
from datetime import datetime

# Add the current directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Facility, get_ph_time

async def seed_facilities():
    async with SessionLocal() as session:
        facilities = []
        
        facility_types = ["Classroom", "Laboratory", "Conference Room", "Auditorium", "Study Area", "Computer Lab"]
        buildings = ["Main Building", "Science Wing", "Engineering Block", "Library Complex", "Arts Center"]
        statuses = ["Available", "In Use", "Under Maintenance", "Reserved"]
        connection_types = ["WiFi", "Ethernet", "Both", "None"]
        cooling_tools = ["AC", "Fan", "Centralized AC", "None"]
        
        print("Generating 50 facility records...")
        
        for i in range(50):
            f_type = random.choice(facility_types)
            building = random.choice(buildings)
            floor = random.randint(1, 5)
            room_num = random.randint(1, 20)
            
            facility = Facility(
                facility_name=f"{f_type} {floor}0{room_num:02d}",
                facility_type=f_type,
                floor_level=f"{floor}th Floor",
                capacity=random.choice([30, 40, 50, 60, 100, 150, 200, 15]),
                connection_type=random.choice(connection_types),
                cooling_tools=random.choice(cooling_tools),
                building=building,
                description=f"A {f_type.lower()} located in {building} on the {floor}th floor.",
                remarks="Seeded data",
                status=random.choice(statuses),
                image_url=None,
                created_at=get_ph_time(),
                updated_at=get_ph_time()
            )
            facilities.append(facility)
            
        session.add_all(facilities)
        await session.commit()
        print(f"Seeded {len(facilities)} facilities!")

if __name__ == "__main__":
    asyncio.run(seed_facilities())
