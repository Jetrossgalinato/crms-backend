import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/postgres")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def add_column():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.connect() as conn:
        try:
            # Check if column exists
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='equipments' AND column_name='availability';"
            ))
            if result.scalar():
                print("Column 'availability' already exists.")
            else:
                print("Adding 'availability' column to 'equipments' table...")
                await conn.execute(text("ALTER TABLE equipments ADD COLUMN availability VARCHAR DEFAULT 'Available';"))
                await conn.commit()
                print("Column added successfully.")
        except Exception as e:
            print(f"Error adding column: {e}")
        finally:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(add_column())
