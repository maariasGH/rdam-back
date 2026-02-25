from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import crud, models, schemas
from .database import SessionLocal, engine

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
    """ Función abrirPago(). Crea sesión en PlusPagos """
    # Lógica para conectar con la API de PlusPagos y devolver link de pago
    return {"checkout_url": "https://pluspagos.com.ar/check/..."}

@app.post("/api/pagos/webhook")
def plus_pagos_ok(tramite_id: int, external_reference: str, db: Session = Depends(get_db)):
    """ Recibe confirmación de PlusPagos (Función plusPagosOK) """
    return crud.registrar_pago_exitoso(db, tramite_id=tramite_id, external_ref=external_reference)

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