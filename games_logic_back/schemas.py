from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import ValidationError
from classes import PrefabData, AttackData, StaticObject, Weapon

async def validate_data(sid, data, func_error, model_class: type[BaseModel]):
    try:
        model = model_class(**data)
        return model
    except ValidationError as e:
        await func_error(sid, e.errors())
        return None

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


class PlayerInfo(BaseModel):
    model_config = base_model_config
    user_id: str
    username: str
    profile_id: str
    player_name: str
    avatar_url: str

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

class GameInfo(BaseModel):
    id: str
    user_id: str

class PlayerAction(BaseModel):
    model_config = base_model_config
    game_id: str
    direction: str | None = None
    weapon_action: Optional[str] = Field(default=None, pattern="^(select|change|leave)$")

class Response(BaseModel):
    model_config = base_model_config
    message: str
    game_id: str
    players_info: Optional[List[PlayerInfo]] = None
    success: bool = True

class WeaponInfo(BaseModel):
    model_config = base_model_config
    id: int
    x: int
    y: int
    type: str
    max_munition: int
    remaining_munition: int
    max_dimensions: dict[str, tuple[int, int]]

class PrefabDataInfo(BaseModel):
    model_config = base_model_config
    x: int
    y: int
    direction: str
    life: int
    max_life: int
    id: str
    type: str | None
    max_dimensions: dict[str, tuple[int, int]]
    weapons: list[WeaponInfo]
    frame_direction: str
    current_weapon_index: int

class AttackInfo(BaseModel):
    model_config = base_model_config
    id: int
    x: int
    y: int
    damage: int
    direction: str
    type: str
    max_dimensions: dict[str, tuple[int, int]]
    attacker_id: str

class StaticObjectInfo(BaseModel):
    model_config = base_model_config
    id: int
    x: int
    y: int
    chest_type: str | None = None
    max_dimensions: dict[str, tuple[int, int]]

class WaveInfo(BaseModel):
    model_config = base_model_config
    wave: str
    wait_to_next: bool
    players: Optional[List[PrefabDataInfo]] = None
    static_objects: Optional[List[StaticObjectInfo]] = None

class DamageInfo(BaseModel):
    model_config = base_model_config
    attack_info: AttackInfo
    prefab_info: PrefabDataInfo

class ChestOpenInfo(BaseModel):
    model_config = base_model_config
    id: str
    prefab_info: Optional[PrefabDataInfo] = None
    weapon_info: Optional[WeaponInfo] = None
    type: str

class WeaponActionResponse(BaseModel):
    model_config = base_model_config
    action: str
    weapon_info: WeaponInfo

def to_weapon_info(weapon: Weapon) -> WeaponInfo:
    weapon_info = {key: value for key, value in weapon.__dict__ if key != 'bullet_damage'}
    return WeaponInfo(weapon_info)

def to_prefab_info(prefab: PrefabData) -> PrefabDataInfo:
    weapon_info = [to_weapon_info(weapon) for weapon in prefab.weapons]
    prefab_info = {key: value for key, value in prefab.__dict__ if key not in ['attacks', 'weapons', 'in_strategy', 'speed', 'generation_enemies_counter', 'character_points', 'total_character_points']}
    prefab_info["weapons"] = weapon_info
    return PrefabDataInfo(prefab_info)

def to_atack_info(attack: AttackData, attacker_id: str) -> AttackInfo:
    attack_info = {key: value for key, value in attack.__dict__ if key != 'alive'}
    attack_info["attacker_id"] = attacker_id
    return AttackInfo(attack_info)

def to_static_object_info(static_object: StaticObject) -> StaticObjectInfo:
    static_object_info = { key: value for key, value in static_object.__dict__ }
    return StaticObjectInfo(static_object_info)

def to_player_info(player: Player) -> PlayerInfo:
    return PlayerInfo(**player.model_dump(exclude_none=True))

def to_wave_info(wave: str, wait_to_next: bool, players: list[PrefabData] | None, 
                 static_obs: list[StaticObject] | None) -> WaveInfo:
    if players and static_obs:
        plys = [ to_prefab_info(x) for x in players ]
        sts = [ to_static_object_info(x) for x in static_obs ]
    else:
        plys = None
        sts = None
    return WaveInfo(wave=wave, wait_to_next=wait_to_next, players=plys, static_objects=sts)

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