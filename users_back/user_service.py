from sqlalchemy.orm import Session
from database_models import UserEntity, ProfileEntity
from classes import User, Profile

def create_user(db: Session, user: User) -> User | None:
    exists = db.query(UserEntity).filter(
        (UserEntity.username == user.username) | (UserEntity.email == user.email)
    ).first()
    if exists:
        return None
    user_entity = UserEntity(username=user.username, email=user.email, encrypted_password=user.password)
    db.add(user_entity)
    db.commit()
    db.flush()
    user.id = str(user_entity.id)
    user.created_at = user_entity.created_at
    return user

def get_user(db: Session, username: str) -> User | None:
    user_entity = db.query(UserEntity).filter(UserEntity.username == username).first()
    if not user_entity:
        return None
    user = User(id=str(user_entity.id), username=user_entity.username, email=user_entity.email, 
                password=user_entity.encrypted_password, created_at=user_entity.created_at)
    return user

def change_password(db: Session, username: str, new_password: str) -> None:
    user_entity = db.query(UserEntity).filter(UserEntity.username == username).first()
    if not user_entity:
        return None
    user_entity.encrypted_password = new_password
    db.commit()

def create_profile(db: Session, username: str, profile: Profile) -> Profile | None:
    user_entity = db.query(UserEntity).filter(UserEntity.username == username).first()
    if not user_entity:
        return None
    profile_entity = ProfileEntity(user_id=str(user_entity.id), display_name=profile.display_name, 
                                   avatar_url=profile.avatar_url)
    db.add(profile_entity)
    db.commit()
    db.flush()
    profile.id = str(profile_entity.id)
    profile.created_at = profile_entity.created_at
    return profile

def get_profiles(db: Session, username: str) -> list[Profile]:
    profiles_entity = db.query(ProfileEntity).join(
                                    UserEntity, ProfileEntity.user_id == UserEntity.id).filter(
                                        UserEntity.username == username).all()
    profiles = []
    for profile_entity in profiles_entity:
        profile = Profile(id=str(profile_entity.id), display_name=profile_entity.display_name, 
                          avatar_url=profile_entity.avatar_url, created_at=profile_entity.created_at)
        profiles.append(profile)
    return profiles

def update_profile(db: Session, id: str, profile: Profile, username: str) -> Profile | None:
    profile_entity = db.query(ProfileEntity).join(
                                    UserEntity, ProfileEntity.user_id == UserEntity.id).filter(
                                        UserEntity.username == username, ProfileEntity.id == id).first()
    if not profile_entity:
        return None
    profile_entity.display_name = profile.display_name
    profile_entity.avatar_url = profile.avatar_url
    db.commit()
    db.flush()
    profile.id = id
    profile.created_at = profile_entity.created_at
    return profile