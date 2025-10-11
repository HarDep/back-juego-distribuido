from fastapi import APIRouter, HTTPException, status
from database import db_dependency
from schemas import UserCreate, UserInfo, ProfileCreate, ProfileInfo, PasswordChange, ResponseMessage
from user_service import create_user, get_user, change_password, create_profile, get_profiles, update_profile
from crypto_service import encrypt, verify_password
from auth import token_dependency

users_router = APIRouter(prefix="/users", tags=["users"])

# POST /users/register
@users_router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: db_dependency) -> UserInfo:
    user_to_create = user.to_domain()
    user_to_create.password = encrypt(user.password)
    created_user = create_user(db, user_to_create)
    if not created_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")
    return UserInfo.to_schema(created_user)

# GET /users/me
@users_router.get("/me")
def get_me(db: db_dependency, username: token_dependency) -> UserInfo:
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserInfo.to_schema(user)

# PUT /users/password
@users_router.put("/password")
def change_user_password(db: db_dependency, username: token_dependency, 
                         data: PasswordChange) -> ResponseMessage:
    user = get_user(db, username)
    if not verify_password(data.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect old password")
    new_psswrd = encrypt(data.new_password)
    change_password(db, username, new_psswrd)
    return ResponseMessage(msg="Password updated successfully")

# GET /users/profiles
@users_router.get("/profiles")
def list_profiles(db: db_dependency, username: token_dependency) -> list[ProfileInfo]:
    profiles = get_profiles(db, username)
    if profiles is None:
        return []
    return [ProfileInfo.to_schema(p) for p in profiles]

# POST /users/profiles/register
@users_router.post("/profiles/register", status_code=status.HTTP_201_CREATED)
def register_profile(db: db_dependency, username: token_dependency, 
                     profile: ProfileCreate) -> ProfileInfo:
    profile_domain = profile.to_domain()
    created_profile = create_profile(db, username, profile_domain)
    if not created_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile creation failed")
    return ProfileInfo.to_schema(created_profile)

# PUT /users/profiles/{id}
@users_router.put("/profiles/{id}")
def update_user_profile(db: db_dependency, username: token_dependency, profile: ProfileCreate, 
                        id: str) -> ProfileInfo:
    # Only allow updating own profiles
    profile_domain = profile.to_domain()
    updated_profile = update_profile(db, id, profile_domain, username)
    if not updated_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile does not exist")
    return ProfileInfo.to_schema(updated_profile)
