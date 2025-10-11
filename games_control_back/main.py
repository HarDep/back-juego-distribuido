from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from games_endpoints import games_control_router

app = FastAPI(title="Games control API", version="1.0.0", description="Games control API ...")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(games_control_router, prefix="/api/v1")