import random
import string

def generate_room_code(length: int = 6) -> str:
    """Generates a random alphanumeric room code."""
    # Usaremos letras mayúsculas y dígitos para evitar ambigüedades (ej. O vs 0, I vs 1)
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))