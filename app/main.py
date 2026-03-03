import json
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import crud, models, schemas
from .database import SessionLocal, engine
from .crypto_pay import encrypt_string
from fastapi import Body

# Estos valores deben coincidir con los del archivo README.md del mock
MERCHANT_GUID = "test-merchant-001"
SECRET_KEY = "clave-secreta-campus-2026"
PLUSPAGOS_URL = "http://localhost:3000"

# Inicialización de la DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RDAM Santa Fe - Backend Oficial")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ENTIDAD: AUTH ---
@app.post("/api/auth/login")
def login(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """ Función validarInterno() y login() """
    db_user = crud.get_usuario_by_login(db, login=usuario.login)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Login exitoso", "user": db_user}

# --- ENTIDAD: TRÁMITE ---
@app.get("/api/tramites", response_model=List[schemas.Tramite])
def list_i(
    estado: Optional[str] = None, 
    dni: Optional[str] = None, 
    fecha: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """ Renderiza list-i (Filtros: estado, dni, fecha) """
    # Aquí se implementaría la lógica de filtrado en el CRUD
    return crud.get_todos_los_tramites(db)

@app.post("/api/tramites", response_model=schemas.Tramite)
def crear_tramite_endpoint(tramite: schemas.TramiteCreate, db: Session = Depends(get_db)):
    """ Función crearTramite() """
    # Nota: El usuario_id se sacaría del token en producción
    return crud.crear_tramite(db=db, tramite=tramite, usuario_id=1)

@app.get("/api/tramites/me", response_model=List[schemas.Tramite])
def list_c(db: Session = Depends(get_db)):
    """ Renderiza list-c (Trámites del usuario logueado) """
    return crud.get_tramites_by_usuario(db, usuario_id=1)

@app.patch("/api/tramites/{id}")
def procesar(id: int, estado: models.EstadoTramite, db: Session = Depends(get_db)):
    """ Función procesar(est) (Aprobar/Rechazar/Emitir) """
    return crud.actualizar_estado_tramite(db, tramite_id=id, nuevo_estado=estado)

# --- ENTIDAD: PAGOS ---
@app.post("/api/pagos/checkout")
def abrir_pago(tramite_id: int, db: Session = Depends(get_db)):
    # 1. Buscamos el trámite en la DB
    tramite = db.query(models.Tramite).filter(models.Tramite.tramite_id == tramite_id).first()
    if not tramite:
        return {"error": "Trámite no encontrado"}

    # 2. Convertir monto a centavos (str) como pide el mock
    # Si el costo es 1250.00, el monto_centavos es "125000"
    monto_centavos = str(int(tramite.pago.monto * 100))
    
    # 3. Encriptar datos sensibles
    encrypted_data = {
        "Comercio": MERCHANT_GUID,
        "TransaccionComercioId": f"TR-ID-{tramite.tramite_id}",
        "Monto": encrypt_string(monto_centavos, SECRET_KEY),
        "UrlSuccess": encrypt_string(f"http://localhost:8000/api/pagos/exito", SECRET_KEY),
        "UrlError": encrypt_string(f"http://localhost:8000/api/pagos/error", SECRET_KEY),
        "Informacion": encrypt_string(json.dumps({"tramite": tramite.nombre_solicitante}), SECRET_KEY)
    }
    
    return {
        "pluspagos_url": PLUSPAGOS_URL,
        "payload": encrypted_data
    }

@app.post("/api/pagos/webhook")
async def plus_pagos_webhook(payload: dict = Body(...), db: Session = Depends(get_db)):
    """ Recibe el POST del Mock de PlusPagos """
    
    # El mock manda: Estado, TransaccionComercioId, etc.
    estado = payload.get("Estado") # "REALIZADA" si está OK
    referencia = payload.get("TransaccionComercioId") # "TR-ID-10"
    
    if estado == "REALIZADA":
        # Extraemos el ID del trámite de la referencia "TR-ID-10"
        t_id = int(referencia.split("-")[-1])
        
        # Guardamos en la DB usando tu CRUD
        crud.registrar_pago_exitoso(db, tramite_id=t_id, external_ref=payload.get("TransaccionPlataformaId"))
        print(f"✅ Pago confirmado para trámite {t_id}")
        
    return {"status": "received"}

# --- ENTIDAD: CERTIFICADO ---
@app.get("/api/certificados/{id}")
def ver_certificado(id: int, db: Session = Depends(get_db)):
    """ Función verCertificado(). Descarga el PDF """
    # Aquí se busca la URL en S3 y se redirige o se sirve el archivo
    return {"download_url": "https://s3.santafe.gov.ar/..."}

# --- ENTIDAD: USUARIOS ---
@app.get("/api/admin/users")
def list_u(db: Session = Depends(get_db)):
    """ Renderiza list-u (Gestión de Usuarios) """
    return db.query(models.Usuario).all()

@app.put("/api/admin/users/{id}")
def save_user(id: int, usuario: schemas.UsuarioBase, db: Session = Depends(get_db)):
    """ Función saveUser() (Edición) """
    # Lógica de actualización de usuario
    return {"message": "Usuario actualizado"}