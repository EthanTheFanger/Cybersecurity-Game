from fastapi import APIRouter, HTTPException, status, Request
from models import UserRegister, UserLogin, UserResponse, Token
from utils.auth import get_password_hash, verify_password, create_access_token
from datetime import datetime

router = APIRouter()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, request: Request):
    """Register a new user"""
    db = request.app.mongodb
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user document
    user_doc = {
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
        "role": user.role.value,
        "created_at": datetime.utcnow()
    }
    
    # Insert into database
    result = await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Return response
    return {
        "message": "User registered successfully",
        "token": access_token,
        "user": {
            "id": str(result.inserted_id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value
        }
    }

@router.post("/login", response_model=dict)
async def login(credentials: UserLogin, request: Request):
    """Login user"""
    db = request.app.mongodb
    
    # Find user
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})
    
    # Return response
    return {
        "message": "Login successful",
        "token": access_token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }