from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

base_dir = Path(__file__).resolve().parent
env_path = base_dir / '.env'
# 2. Cargar el archivo explícitamente
load_dotenv(dotenv_path=env_path)
# Tu clave secreta debe estar en el .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def crear_token_jwt(data: dict):
    print(f"DEBUG: SECRET_KEY cargada es: {os.getenv('SECRET_KEY')}")
    to_encode = data.copy()
    # El token durará 60 minutos
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    
    # Firmamos el token con tu clave secreta
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verificar_token(token: str):
    try:
        # Decodifica y valida la firma y expiración
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Retorna el email (sub)
    except Exception:
        return None

# Configuramos el contexto de hasheo
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """Transforma texto plano en un hash seguro"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Compara la clave ingresada con el hash de la base de datos"""
    return pwd_context.verify(plain_password, hashed_password)