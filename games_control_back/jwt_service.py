from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "changeme_secret_key_should_be_long")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
TOKEN_URL = os.getenv("TOKEN_URL", "/api/v1/auth/token")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

def get_token_data(token: str, key: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        data: str | None = payload.get(key)
    except JWTError:
        return None
    return data

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