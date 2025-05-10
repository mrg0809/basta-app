
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client

import supabase_client
from supabase_client import get_supabase_client

from routers import game_config_router

app = FastAPI(
    title="Basta App API",
    description="API para el juego de BASTA multijugador.",
    version="0.1.0"
)
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

@app.get("/")
async def root():
    return {"message": "¡Bienvenido al API de BASTA Futbolera!"}

@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.get("/test-supabase")
async def test_supabase_connection(client: Client = Depends(get_supabase_client)):
    try:
        # Intentar listar las tablas (o cualquier operación simple)
        # Esto puede requerir permisos o que existan tablas,
        # una prueba más simple sería solo verificar si el cliente se creó.
        # Por ahora, solo confirmamos que el cliente se inyecta.
        if client:
            # Ejemplo: Listar esquemas (esto puede variar o requerir permisos específicos)
            # Para una prueba simple, solo devolvemos que se obtuvo el cliente
            return {"status": "Supabase client created and injected successfully"}
        else:
            return {"status": "Failed to get Supabase client"}
    except Exception as e:
        return {"status": "Error connecting to Supabase or performing operation", "error": str(e)}

# Más adelante aquí añadiremos los routers para las diferentes funcionalidades:
# from .routers import game, users # Ejemplo
# app.include_router(game.router)
# app.include_router(users.router)

# Para ejecutar la app (desde la terminal, en la carpeta 'backend'):
# uvicorn main:app --reload