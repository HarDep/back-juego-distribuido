from sqlalchemy.orm import Session
from database_models import UserEntity, ProfileEntity
from mongo_database import db_mongo_manager
import string
import random
import datetime
from schemas import (GameResponse, Player, UserInfo, GameState)

def magane_database(func):
    def wrapper(*args, **kwargs):
        db_mongo_manager.connect()
        res = func(*args, **kwargs)
        db_mongo_manager.disconnect()
        return res
    return wrapper

@magane_database
def register_game(username: str, profile_id: str, rel_db: Session) -> GameResponse | None:
    profile = rel_db.query(ProfileEntity).join(UserEntity, 
                                               ProfileEntity.user_id == UserEntity.id).filter(
                                        UserEntity.username == username, ProfileEntity.id == profile_id).first()
    if profile is None:
        return None
    inv_code = __generate_unique_code()
    created_by = UserInfo(user_id=str(profile.user_id), username=username)
    players = [Player(user_id=str(profile.user_id), username=username, profile_id=str(profile.id), 
                      player_name=profile.display_name, avatar_url=profile.avatar_url)]
    game_info = GameResponse(code=inv_code, created_by=created_by, players=players, 
                             state=GameState.WAITING, created_at=datetime.datetime.now())
    info = game_info.model_dump()
    res = db_mongo_manager.get_collection().insert_one(info)
    id : str = res.inserted_id
    game_info.id = id
    return game_info

@magane_database
def get_games(username: str, profile_id: str) -> list[GameResponse]:
    res = db_mongo_manager.get_collection().find({"players.profile_id": profile_id, 
                                                       "players.username": username}, 
                                                        {"created_by": 1, "state": 1, "created_at": 1,
                                                        "started_at": 1, "finished_at": 1})
    list = [GameResponse(**game) for game in res]
    return list

@magane_database
def get_game(game_id: str, profile_id: str, username: str) -> GameResponse | None:
    res = db_mongo_manager.get_collection().find_one({"_id": game_id, 
                                                      "players.profile_id": profile_id, 
                                                      "players.username": username})
    if res is None:
        return None
    game_info = GameResponse(**res)
    return game_info

@magane_database
def join_player(username: str, profile_id: str, invitation_code: str, rel_db: Session) -> bool | None:    
    profile = rel_db.query(ProfileEntity).join(UserEntity, 
                                               ProfileEntity.user_id == UserEntity.id).filter(
                                        UserEntity.username == username, ProfileEntity.id == profile_id).first()
    if profile is None:
        return None
    player = Player(user_id=str(profile.user_id), username=username, profile_id=str(profile.id), 
                    player_name=profile.display_name, avatar_url=profile.avatar_url)
    res = db_mongo_manager.get_collection().update_one({"code": invitation_code, 
                                                        "state": GameState.WAITING}, 
                                                 {"$push": {"players": player.model_dump()}})
    return res.modified_count > 0

@magane_database
def change_state(game_id: str, username: str) -> bool:
    res = db_mongo_manager.get_collection().update_one({"_id": game_id, 
                                                  "created_by.username": username, 
                                                  "state": GameState.WAITING}, 
                                                  {"$set": {"state": GameState.IN_PROGRESS}})
    return res.modified_count > 0

@magane_database
def delete_game(game_id: str, username: str) -> bool:
    res = db_mongo_manager.get_collection().delete_one({"_id": game_id, 
                                                        "created_by.username": username, 
                                                        "$not": {"state": GameState.FINISHED}})
    return res.deleted_count > 0

def __generate_code(length: int = 7) -> str:
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

def __generate_unique_code() -> str:
    max_attempts = 10
    for _ in range(max_attempts):
        code = __generate_code()
        if not __code_exists(code):
            return code
    raise Exception("No se pudo generar un código único")

def __code_exists(code: str) -> bool:
    return db_mongo_manager.get_collection().count_documents({"code": code}) > 0