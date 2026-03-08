from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv 

load_dotenv()  # carga el archivo .env
# Cambia estos datos por tus credenciales de PostgreSQL o Neon.tech
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", SQLALCHEMY_DATABASE_URL)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()