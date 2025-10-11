from pydantic import BaseModel, EmailStr
import datetime
from classes import User, Profile

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    def to_domain(self):
        return User(username=self.username, email=self.email, password=self.password)

class UserInfo(BaseModel):
    id: str
    username: str
    email: EmailStr
    created_at: datetime.date

    @classmethod
    def to_schema(_, user: User):
        return UserInfo(id=user.id, username=user.username, email=user.email, 
                        created_at=user.created_at)

class ProfileCreate(BaseModel):
    display_name: str
    avatar_url: str

    def to_domain(self):
        return Profile(display_name=self.display_name, avatar_url=self.avatar_url)

class ProfileInfo(BaseModel):
    id: str
    display_name: str
    avatar_url: str
    created_at: datetime.date

    @classmethod
    def to_schema(_, profile: Profile):
        return ProfileInfo(id=profile.id, display_name=profile.display_name, 
                           avatar_url=profile.avatar_url, created_at=profile.created_at)

class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class ResponseMessage(BaseModel):
    msg: str