# backend/routers/rooms_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Path
from supabase import Client
from typing import List, Optional
from uuid import UUID
import logging
from postgrest.exceptions import APIError 

from ..supabase_client import get_supabase_client
from ..auth_utils import get_current_active_user
from ..models.game_models import (
    User,
    GameRoomCreate,
    GameRoomResponse,
    JoinRoomPayload,
    SetReadyPayload,
    RoomParticipant,
)
from ..utils import generate_room_code

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/rooms",
    tags=["Game Rooms"],
    responses={404: {"description": "Not found"}},
)

def get_user_nickname(user: User) -> str:
    if user.email:
        return user.email.split('@')[0][:20]
    return f"User_{str(user.id)[:8]}"

@router.post("/", response_model=GameRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_game_room(
    room_data: GameRoomCreate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    room_code = generate_room_code()
    logger.info(f"User {current_user.id} creating room. Generated room_code: {room_code}")

    new_room_payload = {
        "room_code": room_code,
        "theme_id": str(room_data.theme_id),
        "host_user_id": str(current_user.id),
        "max_players": room_data.max_players,
        "status": "waiting"
    }
    logger.info(f"Payload for new game_room: {new_room_payload}")

    try:
        # 3. Insertar la nueva sala
        room_insert_response = supabase.table("game_rooms").insert(new_room_payload).execute()
        # Si ocurre un error de PostgREST (4xx, 5xx), APIError se lanzará aquí.
        logger.info(f"Game_rooms insert response data: {room_insert_response.data}, count: {room_insert_response.count}")

        if not room_insert_response.data: # Después de un insert exitoso, data debería estar poblada
            detail = "Could not create game room: No data returned from Supabase after insert."
            logger.error(detail)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

        created_room_data = room_insert_response.data[0]
        game_room_id_str = str(created_room_data["id"])
        logger.info(f"Game room created with ID: {game_room_id_str}")

        # 4. Añadir al host como el primer participante
        host_nickname = get_user_nickname(current_user)
        participant_payload = {
            "game_room_id": game_room_id_str,
            "user_id": str(current_user.id),
            "nickname": host_nickname,
            "is_ready": False
        }
        logger.info(f"Payload for host participant: {participant_payload}")
        participant_insert_response = supabase.table("room_participants").insert(participant_payload).execute()
        # Si ocurre un error de PostgREST, APIError se lanzará aquí.
        logger.info(f"Room_participants insert response data: {participant_insert_response.data}, count: {participant_insert_response.count}")

        if not participant_insert_response.data:
            detail = "Failed to add host as participant: No data returned from Supabase after insert."
            logger.error(detail)
            # Considera rollback: await supabase.table("game_rooms").delete().eq("id", game_room_id_str).execute()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
        
        logger.info(f"Host participant added for user ID: {current_user.id} in room ID: {game_room_id_str}")

        # Ahora, recupera la sala con sus participantes
        logger.info(f"Fetching complete room details for response, room ID: {game_room_id_str}")
        final_room_details_response = supabase.table("game_rooms").select("*, room_participants(*)").eq("id", game_room_id_str).single().execute()
        # Si ocurre un error de PostgREST, APIError se lanzará aquí.
        
        logger.info(f"Data from Supabase for final response (before Pydantic): {final_room_details_response.data}")

        if not final_room_details_response.data: # Después de un select exitoso con .single()
            detail = "Newly created room not found for final response: No data returned."
            logger.error(detail)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        
        return GameRoomResponse(**final_room_details_response.data)

    except APIError as e: # <--- 2. CAPTURAR APIError ESPECÍFICAMENTE
        logger.error(f"Supabase APIError: Code: {e.code}, Message: {e.message}, Details: {e.details}, Hint: {e.hint}", exc_info=False)
        # Puedes mapear e.code (que es un string como '23505' para unique violation) a status_code HTTP si quieres.
        # Por ahora, un 500 genérico para errores de BD.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e.message}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error creating room: {type(e).__name__} - {str(e)}", exc_info=True)
        if isinstance(e, TypeError) and "UUID is not JSON serializable" in str(e): # Aunque esto ya no debería pasar con str()
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: Object of type UUID is not JSON serializable during database operation.")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the room.")


# --- Endpoint para UNIRSE a una sala de juego existente ---
@router.post("/{room_code}/join/", response_model=GameRoomResponse, status_code=status.HTTP_200_OK)
async def join_game_room(
    room_code: str = Path(..., title="The code of the room to join", min_length=6, max_length=6),
    payload: Optional[JoinRoomPayload] = None,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    logger.info(f"User {current_user.id} attempting to join room with code: {room_code.upper()}. Payload: {payload}")
    processed_room_code = room_code.upper() # Asumimos que los códigos son case-insensitive

    try:
        # 1. Buscar la sala por room_code y contar participantes actuales
        # Usamos count en una subconsulta o relación para eficiencia.
        # PostgREST: GET /game_rooms?room_code=eq.ABCDEF&select=*,room_participants(count)
        room_query = supabase.table("game_rooms").select("*, room_participants(count)").eq("room_code", processed_room_code).single().execute()

        if not room_query.data: # single() devuelve None en .data si no se encuentra, o APIError si hay otros problemas
            logger.warning(f"Room with code {processed_room_code} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with code '{processed_room_code}' not found.")
        
        room = room_query.data
        game_room_id_str = str(room["id"])
        
        current_participants_count = 0
        if room.get("room_participants") and isinstance(room["room_participants"], list) and len(room["room_participants"]) > 0:
            # La forma en que count se devuelve en relaciones anidadas puede variar.
            # Si es { "count": N }, accedemos a N.
            # Si es una lista de objetos (no debería ser para count), la lógica cambiaría.
            # Asumimos que devuelve algo como [{"count": X}]
            count_data = room["room_participants"][0]
            if isinstance(count_data, dict) and "count" in count_data:
                 current_participants_count = count_data["count"]
            else: # Fallback si la estructura de count no es la esperada
                 logger.warning(f"Unexpected structure for room_participants count: {room.get('room_participants')}. Re-fetching count.")
                 count_resp = supabase.table("room_participants").select("id", count="exact").eq("game_room_id", game_room_id_str).execute()
                 current_participants_count = count_resp.count


        logger.info(f"Room {game_room_id_str} found. Status: {room['status']}. Max players: {room['max_players']}. Current participants: {current_participants_count}")

        # 2. Validaciones
        if room["status"] != "waiting":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This room is not available for joining (game in progress or finished).")
        
        if current_participants_count >= room["max_players"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This room is full.")

        # Verificar si el usuario ya está en la sala
        # No es estrictamente necesario si la BD tiene la constraint unique_user_per_room,
        # ya que la inserción fallaría con un APIError (ej. código 23505), pero es más amigable chequear antes.
        # Sin embargo, para simplificar y confiar en la BD, podemos omitir este chequeo explícito
        # y dejar que la BD lo maneje. Si la inserción falla por la constraint, APIError se lanzará.
        
        # 3. Determinar el nickname
        nickname_to_use = payload.nickname if payload and payload.nickname else get_user_nickname(current_user)

        # 4. Insertar el nuevo participante
        new_participant_payload = {
            "game_room_id": game_room_id_str,
            "user_id": str(current_user.id),
            "nickname": nickname_to_use,
            "is_ready": False
        }
        logger.info(f"Payload for new participant: {new_participant_payload}")
        participant_insert_response = supabase.table("room_participants").insert(new_participant_payload).execute()

        # APIError se lanzará si hay problemas como unique_user_per_room violado

        if not participant_insert_response.data: # Chequeo por si el insert fue exitoso pero no devolvió data
            detail = "Failed to join room: No data returned from Supabase after insert."
            logger.error(detail)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

        logger.info(f"User {current_user.id} successfully joined room {game_room_id_str} as '{nickname_to_use}'")

        # 5. Devolver la información actualizada de la sala
        final_room_details_response = supabase.table("game_rooms").select("*, room_participants(*)").eq("id", game_room_id_str).single().execute()
        logger.info(f"Data from Supabase for final response after join (before Pydantic): {final_room_details_response.data}")

        if not final_room_details_response.data:
            logger.error(f"Could not fetch room details after join: {final_room_details_response.error if hasattr(final_room_details_response, 'error') else 'No data'}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve room details after joining.")

        return GameRoomResponse(**final_room_details_response.data)

    except APIError as e: # Capturar errores de Supabase/PostgREST
        logger.error(f"Supabase APIError joining room: Code: {e.code}, Message: {e.message}, Details: {e.details}, Hint: {e.hint}")
        if e.code == '23505': # Unique violation (ej. ya está en la sala)
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You are already in this room or another participation conflict occurred.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e.message}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error joining room: {type(e).__name__} - {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while trying to join the room.")

   
@router.get("/{room_identifier}/", response_model=GameRoomResponse, status_code=status.HTTP_200_OK)
async def get_room_details(
    room_identifier: str = Path(..., description="The ID (UUID) or room_code of the game room."),
    # current_user: User = Depends(get_current_active_user), # Descomenta si quieres que solo usuarios autenticados vean las salas
    supabase: Client = Depends(get_supabase_client)
):
    logger.info(f"Attempting to fetch details for room: {room_identifier}")
    
    is_uuid = False
    try:
        UUID(room_identifier, version=4)
        is_uuid = True
    except ValueError:
        is_uuid = False

    try:
        query = supabase.table("game_rooms").select("*, room_participants(*)")

        if is_uuid:
            logger.info(f"Querying by room ID (UUID): {room_identifier}")
            query = query.eq("id", room_identifier)
        else:
            processed_room_code = room_identifier.upper()
            logger.info(f"Querying by room_code: {processed_room_code}")
            query = query.eq("room_code", processed_room_code)

        room_details_response = query.single().execute()
        # Si PostgREST devuelve un error (ej. 406 Not Acceptable si .single() no encuentra nada y no hay exactly one row),
        # se lanzará un APIError.

        logger.info(f"Data from Supabase for get_room_details (before Pydantic): {room_details_response.data}")

        # Si .single() no encuentra un registro, .data será None y no se lanzará APIError (status 200 con data vacía).
        # Si .single() encuentra más de un registro (no debería pasar con id o room_code unique), PostgREST puede devolver un error.
        if not room_details_response.data:
            detail = f"Room '{room_identifier}' not found."
            logger.warning(detail)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

        return GameRoomResponse(**room_details_response.data)

    except APIError as e:
        logger.error(f"Supabase APIError fetching room details for '{room_identifier}': Code: {e.code}, Message: {e.message}, Details: {e.details}, Hint: {e.hint}")
        # PostgREST devuelve PGRST116 (code) y status 406 si .single() no encuentra un resultado único
        # o si no se encuentra ninguna fila.
        if e.code == 'PGRST116': # Not a single row was found
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room '{room_identifier}' not found.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e.message}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error fetching room details for '{room_identifier}': {type(e).__name__} - {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while fetching room details.")
    
    
@router.patch("/{room_id}/participants/me/ready", response_model=RoomParticipant, status_code=status.HTTP_200_OK)
async def set_participant_ready_status(
    payload: SetReadyPayload, # Recibe el nuevo estado is_ready
    room_id: UUID = Path(..., description="The ID of the game room."),
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    user_id_str = str(current_user.id)
    room_id_str = str(room_id)
    new_ready_status = payload.is_ready

    logger.info(f"User {user_id_str} in room {room_id_str} attempting to set ready status to: {new_ready_status}")

    try:
        # Primero, verificar que el usuario es realmente un participante de esta sala
        # y que la sala está en estado 'waiting'
        room_check_query = supabase.table("game_rooms").select("status").eq("id", room_id_str).single().execute()
        if not room_check_query.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
        if room_check_query.data["status"] != "waiting":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change ready status: Room is not in 'waiting' state.")

        # Actualizar el estado is_ready del participante
        # La cláusula 'returning="representation"' hace que Supabase devuelva el registro actualizado
        update_response = (
            supabase.table("room_participants")
            .update({"is_ready": new_ready_status})
            .eq("game_room_id", room_id_str)
            .eq("user_id", user_id_str)
            .execute()
        )
        # Si postgrest-py > 0.11.x, execute() ya no tiene `returning` como parámetro directo, se configura en el cliente
        # o se usa .select() después de .update() si es necesario, o se confía en el returning por defecto.
        # Para Supabase, `update` usualmente devuelve los datos actualizados si RLS lo permite.

        if not update_response.data:
            # Esto puede pasar si el filtro no encontró al participante (usuario no en la sala)
            logger.warning(f"Participant {user_id_str} not found in room {room_id_str} or update failed to return data.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found in this room, or update failed.")

        logger.info(f"User {user_id_str} in room {room_id_str} ready status updated to: {new_ready_status}. Data: {update_response.data[0]}")
        
        # El payload de Realtime para UPDATE ya se habrá enviado por el cambio en la BD.
        # Devolvemos el participante actualizado.
        return RoomParticipant(**update_response.data[0])

    except APIError as e:
        logger.error(f"Supabase APIError setting ready status for user {user_id_str} in room {room_id_str}: {e.message}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e.message}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error setting ready status for user {user_id_str} in room {room_id_str}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
    

@router.post("/{room_id}/start", response_model=GameRoomResponse, status_code=status.HTTP_200_OK)
async def start_game_in_room(
    room_id: UUID = Path(..., description="The ID of the game room to start."),
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    room_id_str = str(room_id)
    user_id_str = str(current_user.id)
    logger.info(f"User {user_id_str} attempting to start game in room {room_id_str}")

    try:
        # 1. Obtener detalles de la sala y verificar que el usuario es el host
        # y que la sala está en estado 'waiting'
        # También contamos los participantes listos
        # Usamos un string select más específico para obtener solo lo necesario
        # y la cuenta de participantes listos.
        # Podríamos hacer dos consultas si es más simple.

        # Consulta para la sala y el conteo de participantes listos
        room_query = supabase.table("game_rooms").select("*, room_participants(id, is_ready)").eq("id", room_id_str).single().execute()

        if not room_query.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
        
        room = room_query.data

        if str(room["host_user_id"]) != user_id_str:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the host can start the game.")
        
        if room["status"] != "waiting":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game cannot be started (not in 'waiting' state).")

        # 2. Verificar condiciones para iniciar (ej. todos listos y mínimo de jugadores)
        participants = room.get("room_participants", [])
        total_participants = len(participants)
        ready_participants = sum(1 for p in participants if p.get("is_ready", False))

        # Define tus condiciones de inicio. Ejemplo:
        min_players_to_start = 1 # Para pruebas, usualmente 2
        if total_participants < min_players_to_start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot start game: At least {min_players_to_start} players are required.")
        
        if total_participants > 0 and ready_participants < total_participants: # Todos deben estar listos
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start game: Not all players are ready.")
        
        # 3. Generar la primera letra del juego
        # Asumimos que tienes una función generate_random_letter en utils.py
        # from ..utils import generate_random_letter (asegúrate que esté importada)
        # Por ahora, la pongo aquí para simplicidad si no la tienes en utils:
        import random
        import string
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" # Podrías excluir letras si quieres
        first_letter = random.choice(alphabet)

        # 4. Actualizar la sala en la base de datos
        update_payload = {
            "status": "in_progress",
            "current_letter": first_letter,
            "current_round_number": 1 # Iniciamos la ronda 1
        }
        logger.info(f"Starting game in room {room_id_str}. Payload: {update_payload}")
        
        update_response = supabase.table("game_rooms").update(update_payload).eq("id", room_id_str).execute()

        if not update_response.data: # El update devuelve los registros actualizados
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update room status to start the game.")

        logger.info(f"Game started successfully in room {room_id_str}. Letter: {first_letter}")

        # 5. Devolver el estado actualizado de la sala (incluyendo la nueva letra y estado)
        # La consulta final en create_room y join_room ya incluye participantes anidados.
        # Hacemos lo mismo aquí para ser consistentes.
        final_room_details_response = supabase.table("game_rooms").select("*, room_participants(*)").eq("id", room_id_str).single().execute()
        
        if not final_room_details_response.data:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room details not found after starting game.")

        return GameRoomResponse(**final_room_details_response.data)

    except APIError as e:
        logger.error(f"Supabase APIError starting game in room {room_id_str}: {e.message}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e.message}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error starting game in room {room_id_str}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while starting the game.")

