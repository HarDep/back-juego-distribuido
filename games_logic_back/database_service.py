from mongo_database import db_mongo_manager
from schemas import GameResponse, GameState, model_from_db, model_to_db
from bson.objectid import ObjectId

def magane_database(func):
    def wrapper(*args, **kwargs):
        db_mongo_manager.connect()
        res = func(*args, **kwargs)
        db_mongo_manager.disconnect()
        return res
    return wrapper

@magane_database
def get_game(game_id: str, user_id: str, creator: bool = True) -> GameResponse:
    search = "created_by.user_id" if creator else "players.user_id"
    res = db_mongo_manager.get_collection().find_one({"_id": ObjectId(game_id), search: user_id, 
                                                      "state": GameState.WAITING})
    if res:
        return model_from_db(GameResponse, res)
    return None

@magane_database
def change_state(game_id: str, user_id: str) -> bool:
    res = db_mongo_manager.get_collection().update_one({"_id": ObjectId(game_id), 
                                                  "created_by.user_id": user_id, 
                                                  "state": GameState.WAITING}, 
                                                  {"$set": {"state": GameState.IN_PROGRESS}})
    return res.modified_count > 0

@magane_database
def update_game(game: GameResponse):
    dict_inf = model_to_db(game)
    res = db_mongo_manager.get_collection().update_one({"_id": ObjectId(game.id)}, {"$set": dict_inf})
    return res.modified_count > 0