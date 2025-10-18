

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from .database import engine, SessionLocal, Base, ItemDB

class Item(BaseModel):
    id: int | None = None
    name: str
    description: str | None = None

app = FastAPI()

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is running!"}

@app.post("/items/", response_model=Item)
async def create_item(item: Item, db: AsyncSession = Depends(get_db)):
    db_item = ItemDB(name=item.name, description=item.description)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return Item(id=db_item.id, name=db_item.name, description=db_item.description)

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.get(ItemDB, item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(id=result.id, name=result.name, description=result.description)

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item, db: AsyncSession = Depends(get_db)):
    db_item = await db.get(ItemDB, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.description = item.description
    await db.commit()
    await db.refresh(db_item)
    return Item(id=db_item.id, name=db_item.name, description=db_item.description)

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    db_item = await db.get(ItemDB, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(db_item)
    await db.commit()
    return {"detail": "Item deleted"}
