# backend/supabase_client.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
# Esto es útil para no tener que hardcodear las credenciales en el código.
load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY") # Usaremos la service_role key en el backend

# Validar que las variables de entorno estén configuradas
if not SUPABASE_URL:
    raise ValueError("La variable de entorno SUPABASE_URL no está configurada.")
if not SUPABASE_KEY:
    raise ValueError("La variable de entorno SUPABASE_SERVICE_KEY no está configurada.")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Conexión con Supabase establecida exitosamente.")
except Exception as e:
    print(f"Error al conectar con Supabase: {e}")
    supabase: Client = None # Asegurarse de que supabase sea None si falla la conexión

def get_supabase_client() -> Client:
    if supabase is None:
        raise Exception("El cliente de Supabase no está inicializado. Revisa la conexión y las credenciales.")
    return supabase