from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class GameState(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class UserInfo(BaseModel):
    user_id: str
    username: str

class WaveData(BaseModel):
    ememy_shadow_defeated: int = 0
    ememy_strange_shadow_defeated: int = 0
    ememy_special_shadow_defeated: int = 0

class FinalWaveData(WaveData):
    boss_defeated: bool = False

class Player(BaseModel):
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
    waves_completed: int = 0
    enemies_defeated: int = 0
    boss_defeated: bool = False

class GameResponse(BaseModel):
    id: str | None = Field(alias="_id", default=None)
    code: str
    created_by: UserInfo
    players: List[Player] = []
    state: GameState
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    final_game_data: Optional[FinalGameData] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Response(BaseModel):
    message: str
