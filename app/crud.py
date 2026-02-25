from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

# --- FUNCIONES DE USUARIO ---

def get_usuario_by_login(db: Session, login: str):
    return db.query(models.Usuario).filter(models.Usuario.login == login).first()

def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    # En un entorno real, aquí se usaría passlib para el hash
    db_usuario = models.Usuario(
        nombre_completo=usuario.nombre_completo,
        login=usuario.login,
        password_hash=usuario.password,  # Recordar hashear antes de guardar
        rol=usuario.rol
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# --- GESTIÓN DE TRÁMITES ---

def crear_tramite(db: Session, tramite: schemas.TramiteCreate, usuario_id: int):
    db_tramite = models.Tramite(
        **tramite.dict(),
        usuario_creador_id=usuario_id,
        estado=models.EstadoTramite.PENDIENTE
    )
    db.add(db_tramite)
    db.commit()
    db.refresh(db_tramite)
    return db_tramite

def get_tramites_by_usuario(db: Session, usuario_id: int):
    return db.query(models.Tramite).filter(models.Tramite.usuario_creador_id == usuario_id).all()

def get_todos_los_tramites(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tramite).offset(skip).limit(limit).all()

# --- ORQUESTACIÓN DE ESTADOS (Lógica Central) ---

def actualizar_estado_tramite(db: Session, tramite_id: int, nuevo_estado: models.EstadoTramite):
    db_tramite = db.query(models.Tramite).filter(models.Tramite.tramite_id == tramite_id).first()
    if db_tramite:
        db_tramite.estado = nuevo_estado
        db.commit()
        db.refresh(db_tramite)
    return db_tramite

# --- PROCESO DE PAGO (PlusPagos Webhook) ---

def registrar_pago_exitoso(db: Session, tramite_id: int, external_ref: str):
    # 1. Crear el registro en la tabla de pagos
    db_pago = models.Pago(
        tramite_id=tramite_id,
        external_reference=external_ref,
        pagado=True,
        fecha_pago=datetime.now()
    )
    db.add(db_pago)
    
    # 2. Actualizar el trámite a 'PAGADA'
    actualizar_estado_tramite(db, tramite_id, models.EstadoTramite.PAGADO)
    
    db.commit()
    return db_pago

# --- EMISIÓN DE CERTIFICADO ---

def emitir_certificado(db: Session, tramite_id: int, operador_id: int, url_s3: str):
    # 1. Crear el registro del certificado vinculado al operador (relación 'emite')
    db_certificado = models.Certificado(
        tramite_id=tramite_id,
        usuario_id=operador_id,
        url_archivo_s3=url_s3
    )
    db.add(db_certificado)
    
    # 2. Actualizar el trámite a 'EMITIDA'
    actualizar_estado_tramite(db, tramite_id, models.EstadoTramite.EMITIDO)
    
    db.commit()
    db.refresh(db_certificado)
    return db_certificado