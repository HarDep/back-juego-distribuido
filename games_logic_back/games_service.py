from schemas import GameInfo, Response, DamageInfo, ChestOpenInfo, to_weapon_info, to_player_info, to_atack_info, to_prefab_info, to_static_object_info, to_wave_info
from database_service import get_game, change_state
from game_manager import GameManager
import socketio
import asyncio

games = {}

DEFAULT_GAME_WIDTH = 1360
DEFAULT_GAME_HEIGHT = 765

def create_game(game_info: GameInfo, sid: str):
    game = get_game(game_info.id, game_info.user_id)
    if not game:
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No se pudo crear el juego", game_id=game_info.id, success=False)
    game_manager = GameManager(DEFAULT_GAME_WIDTH, DEFAULT_GAME_HEIGHT)
    player = game.players[0]
    game_manager.add_player(player.profile_id)
    games[game.id] = {
        "creator" : game_info.user_id,
        "manager" : game_manager,
        "players" : { sid: player.profile_id },
        "game_terminated" : False
    }
    return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Juego creado", game_id=game.id, players_info=[to_player_info(player)])

def start_all_game(game_info: GameInfo, sio: socketio.AsyncServer):
    has_change_state = change_state(game_info.id, game_info.user_id)
    if has_change_state:
        game_data = games[game_info.id]
        manager : GameManager = game_data["manager"]
        manager.generate_player_weapons()
        attack_func = lambda x, y: sio.emit("enemy_attack", to_atack_info(y, x), room=game_info.id)
        move_func = lambda x: sio.emit("enemy_move", to_prefab_info(x), room=game_info.id)
        enemy_gen_func = lambda x: sio.emit("enemy_spawn", to_prefab_info(x), room=game_info.id)
        chest_gen_func = lambda x: sio.emit("chest_generated", to_static_object_info(x), room=game_info.id)
        enemy_def_func = lambda x: sio.emit("enemy_defeated", to_prefab_info(x), room=game_info.id)
        player_def_func = lambda x: sio.emit("player_defeated", to_prefab_info(x), room=game_info.id)
        damage_func = lambda x, y, z, w: sio.emit("enemy" if y else "player" + "_damage", DamageInfo(
                                            prefab_info=to_prefab_info(x), 
                                            attack_info=to_atack_info(z, w)), room=game_info.id)
        async def end_game():
            game_data["game_terminated"] = True
            await sio.emit("game_state_update", Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Juego terminado, te han derrotado", game_id=game_info.id), 
                     room=game_info.id)
        async def game_server_actions():
            while not game_data["game_terminated"]:
                await manager.evaluate_character_position_action(attack_func, move_func, 
                                                                 enemy_gen_func)
                await manager.move_shoots_attacks()
                await manager.evaluate_attacks(chest_gen_func, enemy_def_func, 
                                               player_def_func, end_game, damage_func)
                await asyncio.sleep(0.3)
        new_wave_func = lambda x, y, z, w: sio.emit("wave_start", to_wave_info(x, y, z, w),
                                              room=game_info.id)
        async def game_won():
            game_data["game_terminated"] = True
            await sio.emit("game_state_update", Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Juego terminado, has ganado", game_id=game_info.id, game_won=True), 
                     room=game_info.id)
        asyncio.create_task(manager.generate_waves_and_enemies(enemy_gen_func, new_wave_func, game_won))
        asyncio.create_task(game_server_actions())
        # TODO: guardar datos en la DB segun la info que se necesite o cuando se deba guardar
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="Partida iniciada", game_id=game_info.id)
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
                    message="No se pudo mover el jugador", game_id=game_id, success=False)
    return to_prefab_info(player)

def do_player_shoot(sid: str, game_id: str):
    game_manager: GameManager = games[game_id]["manager"]
    id: str = games[game_id]["players"][sid]
    data = game_manager.do_player_shoot(id)
    if not data:
        return Response(game_width=DEFAULT_GAME_WIDTH, game_height=DEFAULT_GAME_HEIGHT, 
                    message="No se pudo disparar", game_id=game_id, success=False)
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
        await sio.emit("chest_open", chest_info, room=game_id)

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