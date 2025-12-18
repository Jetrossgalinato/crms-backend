


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.login import router as login_router
from api.register import router as register_router
from api.account_requests import router as account_requests_router
from api.auth import router as auth_router
from api.notifications import router as notifications_router
from api.equipment import router as equipment_router
from api.facilities import router as facilities_router
from api.booking import router as booking_router
from api.acquiring import router as acquiring_router
from api.profile import router as profile_router
from api.dashboard import router as dashboard_router
from api.equipment_management import router as equipment_management_router
from api.sidebar import router as sidebar_router
from api.facilities_management import router as facilities_management_router
from api.supplies_management import router as supplies_management_router
from api.my_requests import router as my_requests_router
from api.dashboard_requests import router as dashboard_requests_router
from api.users_management import router as users_management_router
from api.maintenance import router as maintenance_router
from database import engine, Base
import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception occurred: {exc}", exc_info=True)
    
    # Manually add CORS headers to ensure the frontend can read the error details
    origin = request.headers.get("origin")
    headers = {
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    else:
        headers["Access-Control-Allow-Origin"] = "*"

    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
        headers=headers
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://erma-frontend.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all vercel subdomains
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# @app.on_event("startup")
# async def on_startup():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

# Mount static files for uploaded images
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(login_router, prefix="/api")
app.include_router(register_router, prefix="/api")
app.include_router(account_requests_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(equipment_router, prefix="/api")
app.include_router(facilities_router, prefix="/api")
app.include_router(booking_router, prefix="/api")
app.include_router(acquiring_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(sidebar_router, prefix="/api")
app.include_router(equipment_management_router, prefix="/api")
app.include_router(facilities_management_router, prefix="/api")
app.include_router(supplies_management_router, prefix="/api")
app.include_router(dashboard_requests_router, prefix="/api")
app.include_router(my_requests_router, prefix="/api")
app.include_router(users_management_router, prefix="/api")
app.include_router(maintenance_router, prefix="/api")
