from fastapi import APIRouter, HTTPException, status
from database_rel import db_dependency
from jwt_service import token_dependency
from games_service import get_games, get_game, register_game, join_player, delete_game, change_state
from schemas import GameResponse, Response

games_control_router = APIRouter(prefix="/games", tags=["games"])

# GET /games/{profile_id}
@games_control_router.get("/{profile_id}")
async def find_all_games(username: token_dependency, profile_id: str) -> list[GameResponse]:
    games = get_games(username, profile_id)
    return games

# GET /games/{game_id}?profile_id={profile_id}
@games_control_router.get("/{game_id}")
async def find_game(username: token_dependency, game_id: str, profile_id: str) -> GameResponse:
    game = get_game(game_id, profile_id, username)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game

# POST /games/register?profile_id={profile_id}
@games_control_router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_game(db: db_dependency, username: token_dependency, profile_id: str) -> GameResponse:
    game = register_game(username, profile_id, db)
    if game is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="User or profile not found")
    return game

# DELETE /games/{game_id}
@games_control_router.delete("/{game_id}")
async def cancel_game(username: token_dependency, game_id: str) -> Response:
    res = delete_game(game_id, username)
    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game not found or finished, or you are not the creator")
    return Response(message="Game deleted")

# POST /games/{invitation_code}/join?profile_id={profile_id}
@games_control_router.post("/{invitation_code}/join")
async def join_game(db: db_dependency, username: token_dependency, invitation_code: str, 
                    profile_id: str) -> Response:
    res = join_player(username, profile_id, invitation_code, db)
    if res is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Player info are incorrect")
    elif not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invitation incorrect or game are not waiting for invitation")
    return Response(message="Game joined")

# POST /games/{game_id}/start
@games_control_router.post("/{game_id}/start")
async def start_game(username: token_dependency, game_id: str) -> Response:
    res = change_state(game_id, username)
    if not res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game not found or finished, or you are not the creator")
    return Response(message="Game started")