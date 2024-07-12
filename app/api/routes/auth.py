import os
import logging
from typing import Annotated
from passlib.hash import sha256_crypt
from datetime import datetime, timedelta
from app.core.db import get_db
from pydantic import BaseModel
from app.core.models import Users
import jwt
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException, Header

logging.basicConfig(level=logging.INFO)

router = APIRouter()

load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or ""

def authenticate_user(username: str, password: str, db: Session) -> bool:
    try:
        users_data = db.query(Users.password).filter(Users.username == username).first()
        if users_data and sha256_crypt.verify(password, users_data.password):
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Error authenticate_user insert or update: {e}")
    except Exception as e:
        logging.error(f"Error authenticate_user insert or update: {e}")
        return False

def user_info(username: str, db: Session) -> dict:
    try:
        user_data = db.query(Users.first_name, Users.last_name, Users.username, Users.email, Users.avatar).filter(Users.username == username).first()
        if user_data:
            return {
                "first_name": user_data.first_name or " ",
                "last_name": user_data.last_name or " ",
                "username": user_data.username or " ",
                "email": user_data.email or " ",
                "avatar": user_data.avatar
            }
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Error user_info insert or update: {e}")
    except Exception as e:
        logging.error(f"Error user_info insert or update: {e}")
        return None

def generate_tokens(username: str) -> tuple:
    try:
        access_token_expiry = datetime.now() + timedelta(minutes=15)
        refresh_token_expiry = datetime.now() + timedelta(days=1)

        access_token = jwt.encode({"username": username, "exp": access_token_expiry, "token_type": "access"}, JWT_SECRET_KEY, algorithm="HS256")
        refresh_token = jwt.encode({"username": username, "exp": refresh_token_expiry, "token_type": "refresh"}, JWT_SECRET_KEY, algorithm="HS256")

        return access_token, refresh_token
    except Exception as e:
        print("Error generating tokens:", e)
        return None, None

class LoginItem(BaseModel):
    username: str
    password: str

@router.post('/login')
async def login(item: LoginItem, db: Session = Depends(get_db)):
    try:
        username = item.username
        password = item.password

        if authenticate_user(username, password, db):
            access_token, refresh_token = generate_tokens(username)
            if access_token and refresh_token:
                return {"access_token": access_token, "refresh_token": refresh_token, "status": "ok"}
            else:
                raise HTTPException(status_code=500, detail="Failed to generate tokens")
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@router.get('/user_info')
async def get_protected_resource(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing access token in Authorization header")

    try:
        access_token = authorization.split(' ')[1]
        decoded = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=["HS256"])
        username = decoded.get('username')
        
        user_data = user_info(username, db)
        if user_data:
            return user_data
        else:
            raise HTTPException(status_code=404, detail="User not found")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"error": "Refresh token has expired", "status": "expired"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={"error": "Invalid refresh token"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.post('/refresh')
async def refresh(authorization: Annotated[str | None, Header()] = None,):
    try:
        if not authorization:
                raise HTTPException(status_code=401, detail="Missing refresh token in Authorization header")
        refresh_token = authorization.split(' ')[1]
        decoded = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=["HS256"])
        username = decoded.get('username')
        access_token, refresh_token = generate_tokens(username)
        if access_token is not None and refresh_token is not None:
            payload = {"access_token": access_token,"refresh_token": refresh_token,"status" : "ok"}
            return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    
class RegisterItem(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str
    password: str
    email: str | None = None
    avatar_base64: str | None = None

@router.post('/register')
async def register(item: RegisterItem, db: Session = Depends(get_db)):
    try:
        hashed_password = sha256_crypt.hash(item.password)
        existing_user = db.query(Users).filter(Users.username == item.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        user = Users(
            first_name=item.first_name or '',
            last_name=item.last_name or '',
            username=item.username,
            password=hashed_password,
            email=item.email or '',
            avatar=item.avatar_base64 or ''
        )
        db.add(user)
        db.commit()
        return {"message": "User registered successfully", "status": "ok"}
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Error register insert or update: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
