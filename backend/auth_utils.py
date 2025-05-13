import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Aunque no es OAuth2 de contraseña, se usa para el Bearer token
from jose import JWTError, jwt
from pydantic import ValidationError
from typing import Optional
from uuid import UUID

from .models.game_models import User 

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    raise ValueError("La variable de entorno SUPABASE_JWT_SECRET no está configurada.")

ALGORITHM = "HS256" # Supabase usa HS256 para los JWTs firmados con el secret

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # "token" es una URL dummy aquí

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[ALGORITHM], audience="authenticated")

        user_id_str: Optional[str] = payload.get("sub") # "sub" es el user_id en los JWT de Supabase
        email: Optional[str] = payload.get("email")

        if user_id_str is None:
            raise credentials_exception

        # Intenta convertir user_id_str a UUID
        try:
            user_id_uuid = UUID(user_id_str)
        except ValueError:
            raise credentials_exception # Si el 'sub' no es un UUID válido

        # Crear el modelo User Pydantic
        # Aquí puedes añadir más campos si los extraes del token y los tienes en tu modelo User
        user_data = {"id": user_id_uuid, "email": email}
        current_user = User(**user_data)

    except JWTError as e:
        # print(f"JWTError: {e}") # Para depuración
        raise credentials_exception
    except ValidationError as e: # Si User(**user_data) falla la validación de Pydantic
        # print(f"Pydantic ValidationError: {e}") # Para depuración
        raise credentials_exception

    if current_user is None: # Doble chequeo, aunque la lógica anterior debería cubrirlo
        raise credentials_exception

    return current_user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # Aquí podrías añadir lógica para verificar si el usuario está "activo"
    # (ej. no baneado), si tuvieras esa funcionalidad.
    # Por ahora, simplemente devuelve el usuario si el token es válido.
    # if not current_user.is_active: # Ejemplo si tuvieras un campo is_active
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user