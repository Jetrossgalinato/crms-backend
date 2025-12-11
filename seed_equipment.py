import asyncio
import sys
import os
import random
import string
from datetime import datetime, timedelta

# Add the current directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Equipment

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_date():
    start_date = datetime(2020, 1, 1)
    end_date = datetime.now()
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return (start_date + timedelta(days=random_number_of_days)).strftime("%Y-%m-%d")

async def seed_equipment():
    async with SessionLocal() as session:
        equipments = []
        categories = ["IT", "Furniture", "Lab", "AudioVisual", "Sports"]
        statuses = ["Working", "In Use", "For Repair", "Condemned"]
        brands = ["Dell", "HP", "Lenovo", "Apple", "Samsung", "Logitech", "Canon"]
        
        print("Generating 1000 equipment records...")
        
        for i in range(1000):
            equipment = Equipment(
                name=f"Equipment {i+1}",
                po_number=f"PO-{random_string(6)}",
                unit_number=f"UNIT-{random_string(4)}",
                brand_name=random.choice(brands),
                description=f"Description for equipment {i+1}",
                category=random.choice(categories),
                status=random.choice(statuses),
                date_acquire=random_date(),
                supplier=f"Supplier {random_string(5)}",
                amount=str(random.randint(1000, 50000)),
                estimated_life=f"{random.randint(1, 10)} years",
                item_number=f"ITEM-{random_string(6)}",
                property_number=f"PROP-{random_string(6)}",
                control_number=f"CTRL-{random_string(6)}",
                serial_number=f"SN-{random_string(10)}",
                person_liable=f"Person {random_string(5)}",
                remarks="Seeded data",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            equipments.append(equipment)
            
            if len(equipments) >= 100:
                session.add_all(equipments)
                await session.commit()
                equipments = []
                print(f"Seeded {i+1} equipments...")

        if equipments:
            session.add_all(equipments)
            await session.commit()
            print(f"Seeded remaining {len(equipments)} equipments.")
            
        print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_equipment())
