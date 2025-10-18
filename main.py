


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.login import router as login_router
from api.register import router as register_router
from database import engine, Base

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(login_router, prefix="/api")
app.include_router(register_router, prefix="/api")
