
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.auth_utils import verify_password, create_access_token, get_password_hash

router = APIRouter()

# Example user database (replace with real DB integration)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("password")
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    user = fake_users_db.get(request.username)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}
