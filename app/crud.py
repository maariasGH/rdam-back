from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

# --- FUNCIONES DE USUARIO ---

def get_usuario_by_login(db: Session, login: str):
    return db.query(models.Usuario).filter(models.Usuario.login == login).first()

def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    db_usuario = models.Usuario(
        nombre_completo=usuario.nombre_completo,
        login=usuario.login,
        password_hash=usuario.password, 
        rol=usuario.rol
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# --- GESTIÓN DE TRÁMITES ---

def crear_tramite(db: Session, tramite: schemas.TramiteCreate, usuario_id: int):
    # 1. Crear el trámite
    db_tramite = models.Tramite(
        **tramite.dict(),
        usuario_creador_id=usuario_id,
        estado=models.EstadoTramite.PENDIENTE
    )
    db.add(db_tramite)
    db.commit() # Commiteamos para tener el tramite_id
    db.refresh(db_tramite)

    # 2. SOLUCIÓN AL ERROR NoneType: 
    # Creamos el registro de Pago vacío asociado al trámite inmediatamente
    db_pago = models.Pago(
        tramite_id=db_tramite.tramite_id,
        monto=1250.00, # Valor por defecto del sistema
        pagado=False
    )
    db.add(db_pago)
    db.commit()
    
    return db_tramite

def get_tramites_by_usuario(db: Session, usuario_id: int):
    return db.query(models.Tramite).filter(models.Tramite.usuario_creador_id == usuario_id).all()

# --- FILTROS PARA list_i (Operadores/Admin) ---
def get_todos_los_tramites(db: Session, estado: str = None, cuil: str = None, fecha: str = None):
    query = db.query(models.Tramite)
    
    if estado:
        query = query.filter(models.Tramite.estado == estado)
    if cuil:
        query = query.filter(models.Tramite.cuil == cuil)
    if fecha:
        # Convertimos el string de la URL a objeto fecha de Python
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        query = query.filter(models.Tramite.fecha_solicitud == fecha_dt)
        
    return query.all()

# --- ORQUESTACIÓN DE ESTADOS ---

def actualizar_estado_tramite(db: Session, tramite_id: int, nuevo_estado: models.EstadoTramite):
    db_tramite = db.query(models.Tramite).filter(models.Tramite.tramite_id == tramite_id).first()
    if db_tramite:
        db_tramite.estado = nuevo_estado
        db.commit()
        db.refresh(db_tramite)
    return db_tramite

# --- PROCESO DE PAGO (PlusPagos Webhook) ---

def registrar_pago_exitoso(db: Session, tramite_id: int, external_ref: str):
    # Buscamos el registro de pago que creamos al inicio
    db_pago = db.query(models.Pago).filter(models.Pago.tramite_id == tramite_id).first()
    
    if db_pago:
        db_pago.external_reference = external_ref
        db_pago.pagado = True
        db_pago.fecha_pago = datetime.now()
        
        # Actualizamos el trámite a 'PAGADA' (Fijate que sea PAGADA, no PAGADO por el Enum)
        actualizar_estado_tramite(db, tramite_id, models.EstadoTramite.PAGADA)
        
        db.commit()
        db.refresh(db_pago)
    return db_pago

# --- EMISIÓN DE CERTIFICADO ---

def emitir_certificado(db: Session, tramite_id: int, operador_id: int):
    # Simplemente registramos que se emitió
    nuevo_reg = models.Certificado(
        tramite_id=tramite_id,
        usuario_id=operador_id
    )
    db.add(nuevo_reg)
    
    # Actualizamos el trámite
    db_tramite = db.query(models.Tramite).filter(models.Tramite.tramite_id == tramite_id).first()
    db_tramite.estado = "EMITIDA"
    
    db.commit()
    return nuevo_reg

def actualizar_usuario(db: Session, usuario_id: int, datos: schemas.UsuarioUpdate):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.usuario_id == usuario_id).first()
    
    if db_usuario:
        db_usuario.nombre_completo = datos.nombre_completo
        db_usuario.login = datos.login
        db_usuario.rol = datos.rol
        
        # Solo actualizamos la contraseña si se envió una (o si no es ciudadano)
        if datos.password:
            db_usuario.password_hash = datos.password # Aquí pondrías el hash en el futuro
            
        db.commit()
        db.refresh(db_usuario)
    return db_usuario