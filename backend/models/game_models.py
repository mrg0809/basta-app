# backend/models/game_models.py
from pydantic import BaseModel, Field 
from typing import Optional, List, Union, Dict
from uuid import UUID
from datetime import datetime

# --- Theme Models ---
class ThemeBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, examples=["Fútbol Clásico"])

class ThemeCreate(ThemeBase):
    pass

class Theme(ThemeBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Category Models ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, examples=["Nombre Jugador"])
    theme_id: UUID
    order: Optional[int] = 0

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- User Model ---
class User(BaseModel):
    id: UUID
    email: Optional[str] = None

# --- RoomParticipant Models ---
class RoomParticipantBase(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=50, examples=["Jugador Estrella"])

class RoomParticipantCreate(RoomParticipantBase):
    pass

class RoomParticipant(RoomParticipantBase): # Hereda nickname de RoomParticipantBase
    id: UUID
    user_id: UUID
    game_room_id: UUID
    score: int = 0
    is_ready: bool = False
    joined_at: datetime
    created_at: datetime # <--- AÑADIDO para que coincida con los datos de Supabase

    class Config:
        from_attributes = True

# --- GameRoom Models ---
class GameRoomCreate(BaseModel):
    theme_id: UUID
    max_players: Optional[int] = Field(default=8, ge=2, le=16)

class GameRoom(BaseModel):
    id: UUID
    room_code: str
    theme_id: UUID
    host_user_id: UUID
    status: str
    current_letter: Optional[str] = None
    current_round_number: Optional[int] = 0
    max_players: int
    created_at: datetime
    # El campo se llama 'participants' en nuestro modelo/API,
    # pero Pydantic lo llenará desde la clave 'room_participants' de los datos de entrada.
    participants: List[RoomParticipant] = Field(default=[], alias="room_participants") # <--- ESTE ES EL CAMBIO CLAVE

    class Config:
        from_attributes = True

class GameRoomResponse(GameRoom): # Hereda la configuración de GameRoom
    pass

class JoinRoomPayload(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=50, examples=["NuevoJugador"])

class SetReadyPayload(BaseModel):
    is_ready: bool

class PlayerAnswers(BaseModel):
    answers: Dict[str, Optional[str]]