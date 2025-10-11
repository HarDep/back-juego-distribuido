from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schemas import Token
from classes import User
from user_service import get_user
from typing import Annotated
from jwt_service import get_token_data, create_access_token
from crypto_service import verify_password
from database import db_dependency
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN_URL = os.getenv("TOKEN_URL", "/api/v1/auth/token")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)
auth_router = APIRouter(prefix="/auth", tags=["auth"])

async def verify_token(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username: str | None = get_token_data(token, "sub")
    if username is None:
        raise credentials_exception
    return username

token_dependency = Annotated[str, Depends(verify_token)]

def authenticate_user(db: Session, username: str, password: str) ->  User:
    user : User | None = get_user(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

@auth_router.post("/login")
async def login(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    if not form_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Form data is required")
    user : User = authenticate_user(db=db, username=form_data.username, password=form_data.password)
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")