import socketio
from schemas import validate_data, GameInfo, PlayerAction, PrefabDataInfo, AttackInfo, WeaponActionResponse
from games_service import create_game, do_weapon_player_action, start_all_game, terminate_game, add_player, move_player, do_player_shoot, do_chest_selection

sio = socketio.AsyncServer(cors_allowed_origins="*")
app = socketio.ASGIApp(sio)

async def on_error_data(sid, errors):
    print(f"❌ Datos inválidos: {errors}")
    await sio.emit("error", f"Datos inválidos: {errors}", to=sid)

@sio.event
async def connect(sid, _):
    print(f"✅ Cliente conectado: {sid}")

@sio.event
async def disconnect(sid):
    print(f"❌ Cliente desconectado: {sid}")

@sio.event
async def register_game(sid: str, data: dict):
    game_info: GameInfo = await validate_data(sid, data, on_error_data, GameInfo)
    if not game_info:
        return
    res = create_game(game_info, sid)
    if res.success:
        await sio.enter_room(sid, res.game_id)
        await sio.emit("game_state_update", res, to=sid)
    else:
        await sio.emit("error", res, to=sid)

@sio.event
async def start_game(sid, data):
    game_info: GameInfo = await validate_data(sid, data, on_error_data, GameInfo)
    if not game_info:
        return
    res = start_all_game(game_info, sio)
    if res.success:
        await sio.emit("game_state_update", res, room=game_info.id)
    else:
        await sio.emit("error", res, to=sid)

@sio.event
async def cancel_game(sid, data):
    game_info: GameInfo = await validate_data(sid, data, on_error_data, GameInfo)
    if not game_info:
        return
    res = terminate_game(game_info)
    if res.success:
        await sio.close_room(res.game_id)
        await sio.emit("game_state_update", res, room=game_info.id)
    else:
        await sio.emit("error", res, to=sid)

@sio.event
async def player_join(sid, data):
    game_info: GameInfo = await validate_data(sid, data, on_error_data, GameInfo)
    if not game_info:
        return
    res = add_player(game_info, sid)
    if res.success:
        await sio.enter_room(sid, res.game_id)
        await sio.emit("player_join", res, room=game_info.id)
    else:
        await sio.emit("error", res, to=sid)

@sio.event
async def player_move(sid, data):
    info: PlayerAction = await validate_data(sid, data, on_error_data, PlayerAction)
    if not info or not info.direction:
        return
    res = move_player(info.direction, sid, info.game_id)
    if isinstance(res, PrefabDataInfo):
        await sio.emit("player_move", res, room=info.game_id)
    else:
        await sio.emit("error", res, to=sid)

@sio.event
async def player_shoot(sid, data):
    info: PlayerAction = await validate_data(sid, data, on_error_data, PlayerAction)
    if not info:
        return
    res = do_player_shoot(sid, info.game_id)
    if isinstance(res, AttackInfo):
        await sio.emit("player_shoot", res, room=info.game_id)
    else:
        await sio.emit("error", res, to=sid)

@sio.event
async def chest_selection(sid, data):
    info: PlayerAction = await validate_data(sid, data, on_error_data, PlayerAction)
    if not info:
        return
    await do_chest_selection(sid, info.game_id, sio)

@sio.event
async def weapon_action(sid, data):
    info: PlayerAction = await validate_data(sid, data, on_error_data, PlayerAction)
    if not info or not info.weapon_action:
        return
    res = do_weapon_player_action(info.weapon_action, sid, info.game_id)
    if res:
        await sio.emit("weapon_action", WeaponActionResponse(action=info.weapon_action, 
                                                             weapon_info=res), room=info.game_id)