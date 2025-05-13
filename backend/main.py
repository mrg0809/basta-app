import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client

from .supabase_client import get_supabase_client

from .routers import game_config_router, rooms_router

logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(name)s - %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Basta App API",
    description="API para el juego de BASTA multijugador.",
    version="0.1.0"
)

logger.info("Iniciando la aplicación Basta App API...")

origins = [
    "http://localhost",         # Si accedes sin puerto especificado
    "http://localhost:9000",    # Puerto por defecto de Quasar dev
    "http://localhost:8080",    # Otro puerto común de desarrollo
    # "https://tu-dominio-de-frontend.com" # Para producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Permite los orígenes especificados
    allow_credentials=True, # Permite cookies (importante para autenticación)
    allow_methods=["*"],    # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],    # Permite todos los headers
)

app.include_router(game_config_router.router, prefix="/api/v1")
app.include_router(rooms_router.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "¡Bienvenido al API de BASTA Futbolera!"}

@app.get("/ping")
async def ping():
    return {"message": "pong"}
