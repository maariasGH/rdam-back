import json
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import crud, models, schemas
from .database import SessionLocal, engine
from .crypto_pay import encrypt_string
from fastapi import Body
from typing import List, Optional
from fastapi.responses import RedirectResponse

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
@app.post("/api/auth/login", response_model=dict)
def login(auth_data: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    # 1. Buscar al usuario
    db_user = crud.get_usuario_by_login(db, login=auth_data.login)
    
    # 2. Si no existe, error 401
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Credenciales incorrectas"
        )
    
    # 3. LÓGICA DE VALIDACIÓN POR ROL
    # Si es CIUDADANO, entra directo (o podrías pedir que el password venga vacío)
    if db_user.rol == models.RolUsuario.CIUDADANO:
        # Opcional: podrías verificar que el password enviado sea null o vacío
        pass 
    else:
        # Si es OPERADOR o ADMINISTRADOR, la contraseña es OBLIGATORIA
        if not db_user.password_hash or db_user.password_hash != auth_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Contraseña incorrecta para perfil administrativo"
            )
    
    # 4. Verificar si la cuenta está activa
    if db_user.estado != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Usuario inactivo"
        )

    return {
        "message": "Login exitoso",
        "user": schemas.UsuarioRespuesta.from_orm(db_user)
    }

# --- ENTIDAD: TRÁMITE ---

@app.get("/api/tramites", response_model=List[schemas.Tramite])
def list_i(
    estado: Optional[models.EstadoTramite] = None, 
    cuil: Optional[str] = None, # Usamos CUIL que es lo que tenés en la entidad
    fecha: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """ Lista todos los trámites con filtros para el OPERADOR/ADMIN """
    return crud.get_todos_los_tramites(db, estado=estado, cuil=cuil, fecha=fecha)

@app.post("/api/tramites", response_model=schemas.Tramite)
def crear_tramite_endpoint(tramite: schemas.TramiteCreate, db: Session = Depends(get_db)):
    """ Crea un nuevo trámite de adopción (Función crearTramite) """
    # En el curso, aquí usarías el ID del usuario que inició sesión
    return crud.crear_tramite(db=db, tramite=tramite, usuario_id=1) 

@app.get("/api/tramites/me", response_model=List[schemas.Tramite])
def list_c(db: Session = Depends(get_db)):
    """ Lista solo los trámites del CIUDADANO logueado """
    # Simulamos que el usuario logueado es el ID 3
    return db.query(models.Tramite).filter(models.Tramite.usuario_creador_id == 3).all()

@app.patch("/api/tramites/{id}")
def procesar(id: int, estado: models.EstadoTramite, db: Session = Depends(get_db)):
    """ 
    Cambia el estado del trámite (Aprobar/Rechazar/Emitir).
    Ejemplo: de PENDIENTE a EMITIDA
    """
    db_tramite = crud.actualizar_estado_tramite(db, tramite_id=id, nuevo_estado=estado)
    if not db_tramite:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    return {"message": f"Trámite {id} actualizado a {estado}", "tramite": db_tramite}

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
@app.get("/api/certificados/{tramite_id}")
def ver_certificado(tramite_id: int, db: Session = Depends(get_db)):
    """ 
    Función verCertificado(). 
    Busca el certificado asociado al trámite y redirige a la descarga en S3. 
    """
    # 1. Buscar el certificado en la base de datos vinculado al trámite
    db_certificado = db.query(models.Certificado).filter(models.Certificado.tramite_id == tramite_id).first()
    
    # 2. Si no existe el certificado, es porque el trámite no fue emitido aún
    if not db_certificado:
        raise HTTPException(
            status_code=404, 
            detail="Certificado no encontrado. Verifique que el trámite esté en estado EMITIDO."
        )
    
    # En lugar de RedirectResponse, devolvemos el objeto
    return {
        "tramite_id": tramite_id,
        "download_url": db_certificado.url_archivo_s3,
        "fecha_emision": db_certificado.fecha_emision
    }

@app.post("/api/certificados/emitir", response_model=dict, status_code=201)
def emitir_certificado_endpoint(
    tramite_id: int, 
    url_s3: str, 
    operador_id: int, 
    db: Session = Depends(get_db)
):
    """
    Función emitirCertificado().
    Crea el registro del certificado y actualiza el trámite a 'EMITIDA'.
    """
    # 1. Verificar si el trámite existe
    db_tramite = db.query(models.Tramite).filter(models.Tramite.tramite_id == tramite_id).first()
    if not db_tramite:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")

    # 2. Verificar si el trámite ya está pagado para poder emitir
    if db_tramite.estado != models.EstadoTramite.PAGADA:
        raise HTTPException(status_code=400, detail="El trámite debe estar PAGADO para emitir el certificado")

    # 3. Llamar al CRUD para realizar la transacción
    try:
        nuevo_certificado = crud.emitir_certificado(
            db=db, 
            tramite_id=tramite_id, 
            operador_id=operador_id, 
            url_s3=url_s3
        )
        return {
            "message": "Certificado emitido con éxito",
            "certificado_id": nuevo_certificado.certificado_id,
            "nuevo_estado_tramite": "EMITIDA"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al emitir: {str(e)}")

# --- ENTIDAD: USUARIOS ---
@app.get("/api/admin/users")
def list_u(db: Session = Depends(get_db)):
    """ Renderiza list-u (Gestión de Usuarios) """
    return db.query(models.Usuario).all()

@app.put("/api/admin/users/{id}")
def save_user(id: int, usuario: schemas.UsuarioUpdate, db: Session = Depends(get_db)):
    """ Función saveUser() (Edición/Creación) """
    
    # 1. Verificación de Regla de Negocio
    if usuario.rol != models.RolUsuario.CIUDADANO:
        if not usuario.password or len(usuario.password) < 3:
            raise HTTPException(
                status_code=400, 
                detail=f"Los usuarios con rol {usuario.rol} deben tener una contraseña válida."
            )

    # 2. Llamar al CRUD para actualizar
    db_user = crud.actualizar_usuario(db, usuario_id=id, datos=usuario)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return {"message": "Usuario actualizado exitosamente", "user": db_user}

@app.post("/api/usuarios", response_model=schemas.UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def crear_usuario_endpoint(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """ 
    Endpoint para registrar un nuevo usuario (ADMIN/OPERADOR/CIUDADANO).
    Si el rol no es CIUDADANO, requiere contraseña.
    """
    # 1. Verificar si el login ya existe para evitar duplicados
    db_user = crud.get_usuario_by_login(db, login=usuario.login)
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="El nombre de usuario (login) ya está en uso."
        )

    # 2. Validación de contraseña según rol (Regla de Negocio RDAM)
    if usuario.rol != models.RolUsuario.CIUDADANO:
        if not usuario.password or len(usuario.password) < 3:
            raise HTTPException(
                status_code=400, 
                detail="Los administradores y operadores requieren una contraseña de al menos 3 caracteres."
            )

    # 3. Llamar al CRUD para insertar en la DB
    nuevo_usuario = crud.crear_usuario(db=db, usuario=usuario)
    return nuevo_usuario