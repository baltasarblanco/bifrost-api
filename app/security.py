from passlib.context import CryptContext

# Configuramos el contexto de encriptación para usar el algoritmo bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Toma una contraseña en texto plano y devuelve su hash seguro."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña ingresada con el hash guardado en la base de datos."""
    return pwd_context.verify(plain_password, hashed_password)