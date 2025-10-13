from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

base_model_config = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True,
    from_attributes=True,
)

class GameState(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class UserInfo(BaseModel):
    model_config = base_model_config
    user_id: str
    username: str

class WaveData(BaseModel):
    model_config = base_model_config
    ememy_shadow_defeated: int = 0
    ememy_strange_shadow_defeated: int = 0
    ememy_special_shadow_defeated: int = 0

class FinalWaveData(WaveData):
    boss_defeated: bool = False

class Player(BaseModel):
    model_config = base_model_config
    user_id: str
    username: str
    profile_id: str
    player_name: str
    avatar_url: str
    score: Optional[int] = None
    total_kills: Optional[int] = None
    first_wave_data: Optional[WaveData] = None
    second_wave_data: Optional[WaveData] = None
    third_wave_data: Optional[WaveData] = None
    final_wave_data: Optional[FinalWaveData] = None

class FinalGameData(BaseModel):
    model_config = base_model_config
    waves_completed: int = 0
    enemies_defeated: int = 0
    boss_defeated: bool = False

class GameResponse(BaseModel):
    model_config = base_model_config
    id: str | None = None
    code: str
    created_by: UserInfo
    players: List[Player] = []
    state: GameState
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    final_game_data: Optional[FinalGameData] = None

class Response(BaseModel):
    model_config = base_model_config
    message: str

def model_to_db(model: BaseModel) -> dict:
    data = model.model_dump(exclude_none=True)
    if isinstance(model, GameResponse):
        if "id" in data:
            del data["id"]
    return data

def model_from_db(model_class: type[BaseModel], data: dict) -> BaseModel:
    if "_id" in data:
        data["id"] = str(data["_id"])
        del data["_id"]
    return model_class(**data)