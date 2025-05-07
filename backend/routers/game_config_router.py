# backend/routers/game_config_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import List
from uuid import UUID

from models.game_models import Theme, ThemeCreate, Category, CategoryCreate
from supabase_client import get_supabase_client # Ajusta el path si es necesario

router = APIRouter()

# --- Endpoints para THEMES ---

@router.post("/themes/", response_model=Theme, status_code=status.HTTP_201_CREATED, tags=["Themes"])
async def create_theme_endpoint(
    theme_data: ThemeCreate,
    supabase: Client = Depends(get_supabase_client)
):
    try:
        response = supabase.table("themes").insert(theme_data.model_dump()).execute()
        if response.data:
            return response.data[0]
        else:
            # Supabase puede devolver data vacía si hubo un error no capturado como excepción
            # o si la inserción no devolvió datos (depende de la configuración de Supabase/Postgres)
            # Es importante revisar la estructura de la respuesta de Supabase
            # print("Error data from Supabase:", response.error) # Para depuración
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create theme")
    except Exception as e:
        # print(f"Exception creating theme: {e}") # Para depuración
        # podrías querer loguear el 'e' real y devolver un mensaje más genérico
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create theme: {str(e)}")


@router.get("/themes/", response_model=List[Theme], tags=["Themes"])
async def list_themes_endpoint(
    supabase: Client = Depends(get_supabase_client)
):
    try:
        response = supabase.table("themes").select("*").order("created_at", desc=False).execute()
        if response.data is not None: # Verificar que data no sea None
             return response.data
        else: # Si data es None, puede ser un error o simplemente no hay datos
            # print("Error data from Supabase (list themes):", response.error) # Para depuración
            return [] # Devolver lista vacía si no hay datos o si response.error tiene algo
    except Exception as e:
        # print(f"Exception listing themes: {e}") # Para depuración
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list themes")


# --- Endpoints para CATEGORIES ---

@router.post("/categories/", response_model=Category, status_code=status.HTTP_201_CREATED, tags=["Categories"])
async def create_category_endpoint(
    category_data: CategoryCreate,
    supabase: Client = Depends(get_supabase_client)
):
    # Validar que el theme_id existe sería una buena mejora
    try:
        insert_payload = category_data.model_dump(mode="json")
        insert_payload["theme_id"] = str(category_data.theme_id)

        response = supabase.table("categories").insert(insert_payload).execute()
        if response.data:
            return response.data[0]
        else:
            # print("Error data from Supabase (create category):", response.error) # Para depuración
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create category")
    except Exception as e:
        # print(f"Exception creating category: {e}") # Para depuración
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create category: {str(e)}")


@router.get("/categories/", response_model=List[Category], tags=["Categories"])
async def list_categories_by_theme_endpoint(
    theme_id: UUID, # Parámetro de consulta para filtrar por theme_id
    supabase: Client = Depends(get_supabase_client)
):
    try:
        response = supabase.table("categories").select("*").eq("theme_id", str(theme_id)).order("order", desc=False).execute() # str(theme_id) es importante para Supabase
        if response.data is not None:
            return response.data
        else:
            # print("Error data from Supabase (list categories):", response.error) # Para depuración
            return []
    except Exception as e:
        # print(f"Exception listing categories: {e}") # Para depuración
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list categories")