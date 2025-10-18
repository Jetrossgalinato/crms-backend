


from fastapi import FastAPI
from api.login import router as login_router

app = FastAPI()
app.include_router(login_router, prefix="/api")
