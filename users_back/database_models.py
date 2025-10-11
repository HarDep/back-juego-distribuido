from sqlalchemy import Column, String, Date, UUID, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserEntity(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=func.uuid_generate_v4())
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    encrypted_password = Column(String, nullable=False)
    created_at = Column(Date, default=func.now(), nullable=False)

class ProfileEntity(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=func.uuid_generate_v4())
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    display_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=False)
    created_at = Column(Date, default=func.now(), nullable=False)