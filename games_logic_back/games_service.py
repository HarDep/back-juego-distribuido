from schemas import GameInfo, Response, DamageInfo, ChestOpenInfo, GameResponse, WaveData, FinalWaveData, GameState, FinalGameData, to_weapon_info, to_player_info, to_atack_info, to_prefab_info, to_static_object_info, to_wave_info
from database_service import get_game, change_state, update_game
from game_manager import GameManager
from classes import PrefabData
import socketio
import asyncio
import datetime

games = {}

DEFAULT_GAME_WIDTH = 1360
DEFAULT_GAME_HEIGHT = 765

def save_game_data(game_data: GameResponse):
    res = update_game(game_data)
    if not res:
        print("Error al guardar el juego")

def create_game(game_info: GameInfo, sid: str):
    game = get_game(game_info.id, game_info.user_id)
    if not game:
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No se pudo crear el juego", game_id=game_info.id, success=False)
    game_manager = GameManager(DEFAULT_GAME_WIDTH, DEFAULT_GAME_HEIGHT)
    player = game.players[0]
    game_manager.add_player(player.profile_id)
    games[game.id] = {
        "manager" : game_manager,
        "players" : { sid: player.profile_id },
        "game_terminated" : False,
        "info" : game,
        "players_defeated" : []
    }
    return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Juego creado", game_id=game.id, players_info=[to_player_info(player)])

def start_all_game(game_info: GameInfo, sio: socketio.AsyncServer):
    has_change_state = change_state(game_info.id, game_info.user_id)
    if has_change_state:
        game_data = games[game_info.id]
        defeated_list: list[str] = game_data["players_defeated"]
        game_schema: GameResponse = game_data["info"]
        game_schema.started_at = datetime.datetime.now()
        game_schema.final_game_data = FinalGameData()
        manager : GameManager = game_data["manager"]
        manager.generate_player_weapons()
        attack_func = lambda x, y: sio.emit("enemy_attack", to_atack_info(y, x).model_dump(exclude_none=True), room=game_info.id)
        move_func = lambda x: sio.emit("enemy_move", to_prefab_info(x).model_dump(exclude_none=True), room=game_info.id)
        enemy_gen_func = lambda x: sio.emit("enemy_spawn", to_prefab_info(x).model_dump(exclude_none=True), room=game_info.id)
        chest_gen_func = lambda x: sio.emit("chest_generated", to_static_object_info(x).model_dump(exclude_none=True), room=game_info.id)
        async def on_enemy_defeated(x: PrefabData, id:str):
            await sio.emit("enemy_defeated", to_prefab_info(x).model_dump(exclude_none=True), room=game_info.id)
            game_schema.final_game_data.enemies_defeated += 1
            player_info = list(filter(lambda x: x.profile_id == id, game_schema.players))[0]
            player_info.total_kills += 1
            player_info.score += 10
            wave_info: WaveData | FinalWaveData = player_info.first_wave_data if game_schema.final_game_data.waves_completed == 1 else player_info.second_wave_data if game_schema.final_game_data.waves_completed == 2 else player_info.third_wave_data if game_schema.final_game_data.waves_completed == 3 else player_info.final_wave_data
            if x.type == "final":
                game_schema.final_game_data.boss_defeated = True
                player_info.final_wave_data.boss_defeated = True
            elif x.type == "type1":
                wave_info.enemy_shadow_defeated += 1
            elif x.type == "type2":
                wave_info.enemy_strange_shadow_defeated += 1
            elif x.type == "type3":
                wave_info.enemy_special_shadow_defeated += 1
        async def on_player_defeated(x: PrefabData):
            await sio.emit("player_defeated", to_prefab_info(x).model_dump(exclude_none=True), room=game_info.id)
            defeated_list.append(x.id)
        damage_func = lambda x, y, z, w: sio.emit("enemy" if y else "player" + "_damage", DamageInfo(
                                            prefab_info=to_prefab_info(x), 
                                            attack_info=to_atack_info(z, w)).model_dump(exclude_none=True), room=game_info.id)
        async def end_game(won: bool):
            game_data["game_terminated"] = True
            await sio.emit("game_state_update", Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message=f"Juego terminado, {"has ganado" if won else "te han derrotado"}", game_id=game_info.id, 
                    game_initialized=True, game_won=won).model_dump(exclude_none=True), room=game_info.id)
            game_schema.finished_at = datetime.datetime.now()
            game_schema.state = GameState.FINISHED
            save_game_data(game_schema)
        async def game_server_actions():
            while not game_data["game_terminated"]:
                await manager.evaluate_character_position_action(attack_func, move_func, 
                                                                 enemy_gen_func)
                await manager.move_shoots_attacks()
                await manager.evaluate_attacks(chest_gen_func, on_enemy_defeated, 
                                               on_player_defeated, lambda: end_game(False), damage_func)
                await asyncio.sleep(0.3)
        async def on_wave_func(x, y, z, w):
            wave = str(x) if x != 4 else "final"
            await sio.emit("wave_start", to_wave_info(wave, y, z, w).model_dump(exclude_none=True), room=game_info.id)
            game_schema.final_game_data.waves_completed = x
            for ply in game_schema.players:
                if x in [1, 2, 3] and ply.profile_id not in defeated_list:
                    wave_info: WaveData | None = ply.first_wave_data if x == 1 else ply.second_wave_data if x == 2 else ply.third_wave_data
                    if not wave_info:
                        wave_info = WaveData()
                elif not ply.final_wave_data and ply.profile_id not in defeated_list:
                    ply.final_wave_data = FinalWaveData()
        asyncio.create_task(manager.generate_waves_and_enemies(enemy_gen_func, on_wave_func, lambda: end_game(True)))
        asyncio.create_task(game_server_actions())
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Partida iniciada", game_id=game_info.id, game_initialized=True)
    return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No se pudo iniciar el juego", game_id=game_info.id, success=False)

def terminate_game(game_info: GameInfo):
    game = get_game(game_info.id, game_info.user_id)
    if not game:
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No existe el juego, o ya esta en curso", game_id=game_info.id, 
                        success=False)
    del games[game.id]
    return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Juego terminado", game_id=game.id)

def add_player(game_info: GameInfo, sid: str):
    game = get_game(game_info.id, game_info.user_id, creator=False)
    if not game:
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No existe el juego, o ya esta en curso", game_id=game_info.id, 
                        success=False)
    if sid not in games[game.id]["players"]:
        player = list(filter(lambda x: x.user_id == game_info.user_id, game.players))[0]
        games[game.id]["players"][sid] = player.profile_id
        game_manager: GameManager = games[game.id]["manager"]
        game_manager.add_player(player.profile_id)
        players = [ to_player_info(x) for x in game.players ]
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Jugador agregado", game_id=game.id, players_info=players)
    return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="El jugador ya se encuentra en el juego", game_id=game.id, success=False)

def move_player(move_direction:str, sid:str, game_id:str):
    game_manager: GameManager = games[game_id]["manager"]
    player = game_manager.move_player(games[game_id]["players"][sid], move_direction)
    if not player:
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No se pudo mover el jugador", game_id=game_id, success=False, 
                    game_initialized=True)
    return to_prefab_info(player)

def do_player_shoot(sid: str, game_id: str):
    game_manager: GameManager = games[game_id]["manager"]
    id: str = games[game_id]["players"][sid]
    data = game_manager.do_player_shoot(id)
    if not data:
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No se pudo disparar", game_id=game_id, success=False, 
                    game_initialized=True)
    return to_atack_info(data, id)

async def do_chest_selection(sid: str, game_id: str, sio: socketio.AsyncServer):
    game_manager: GameManager = games[game_id]["manager"]
    data = await game_manager.open_chest(games[game_id]["players"][sid])
    if data:
        chest, res = data
        if chest.chest_type == "health":
            chest_info = ChestOpenInfo(id=chest.id, type=chest.chest_type, prefab_info=to_prefab_info(res))
        else:
            chest_info = ChestOpenInfo(id=chest.id, type=chest.chest_type, weapon_info=to_weapon_info(res))
        await sio.emit("chest_open", chest_info.model_dump(exclude_none=True), room=game_id)

def do_weapon_player_action(action:str, sid: str, game_id: str):
    game_manager: GameManager = games[game_id]["manager"]
    id: str = games[game_id]["players"][sid]
    if action == "select":
        res = game_manager.add_weapon_to_player(id)
    elif action == "change":
        res = game_manager.change_player_weapon(id)
    elif action == "leave":
        res = game_manager.leave_player_weapon(id)
    else:
        return None
    if res:
        return to_weapon_info(res)
