import json
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import crud, models, schemas
from .database import SessionLocal, engine
from .crypto_pay import encrypt_string
from fastapi import Body, Header
from typing import List, Optional
from fastapi.responses import RedirectResponse
from fastapi.responses import StreamingResponse
from .services.pdf_gen import generar_pdf_certificado
from datetime import datetime, timedelta
import random
import string
from email.message import EmailMessage
import mailtrap as mt
import os
from dotenv import load_dotenv
from .security import verify_password, crear_token_jwt, verificar_token
import requests

# Cargar las variables del archivo .env
load_dotenv()

# Acceso a ellas
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 2525))
API_TOKEN= os.getenv("API_TOKEN")
MERCHANT_GUID = os.getenv("MERCHANT_GUID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLUSPAGOS_URL = os.getenv("PLUSPAGOS_URL")
RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET_KEY")


def enviar_email(destinatario, codigo):
    # Cargar el token justo antes de usarlo para asegurar que lo lee
    token_actual = API_TOKEN
    
    if not token_actual:
        print("❌ ERROR: No se encontró el API_TOKEN en las variables de entorno")
        return

    # IMPORTANTE: En Mailtrap Sandbox, el remitente DEBE ser este para que no rebote
    sender_email = "hello@demomailtrap.com" 
    
    mail = mt.Mail(
        sender=mt.Address(email=sender_email, name="Sistema RDAM"),
        to=[mt.Address(email=destinatario)],
        subject="Tu Código de Acceso - RDAM",
        text=f"Tu código es: {codigo}. Válido por 15 minutos.",
        category="Auth"
    )

    try:
        client = mt.MailtrapClient(token=token_actual)
        client.send(mail)
        print(f"✅ Email enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar con Mailtrap: {e}")
        print(f"[SIMULACION] Codigo enviado a {destinatario}: {codigo}. Válido por 15 minutos. Tambien puede ser consultado en la BD")

def generar_codigo():
    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return codigo


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
def login_staff(params: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    """
    Endpoint para que Operadores y Administradores inicien sesión 
    con usuario y contraseña.
    """
    # 1. Buscar al usuario en la base de datos
    user = db.query(models.Usuario).filter(models.Usuario.login == params.login).first()

    # 2. Validar si existe y si la password es correcta
    # NOTA: En producción deberías usar hash (ej. passlib) en lugar de texto plano
    if not user or not verify_password(params.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Responder con los datos del perfil y un token de sesión
    return {
        "msg": {
          "exito": "Inicio de Sesión Exitoso"  
        },
        "user": {
            "login": user.login,
            "rol": user.rol,
            "nombre": user.nombre_completo
        }
    }
    
# --- NUEVOS ENDPOINTS CIUDADANO-TRAMITE ---

@app.post("/api/auth/ciudadano/solicitar-codigo")
def solicitar_codigo(email: str, recaptcha_token: str, db: Session = Depends(get_db)):
    
    # 1. Validar el token de reCAPTCHA con Google
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": RECAPTCHA_SECRET,
        "response": recaptcha_token
    }
    response = requests.post(url, data=payload).json()

    # Si la validación falla o el score es bajo (ej: < 0.5), bloqueamos el intento
    if recaptcha_token == "token_prueba_123":
        print("⚠️ Bypass de Captcha activado (Solo desarrollo, hasta que se desarrolle el front-end y se pueda integrar la api del Captcha)")
    else:
        if not response.get("success") or response.get("score", 0) < 0.5:
            raise HTTPException(status_code=400, detail="Error de seguridad: Solicitud sospechosa detectada.")

    # 2. Tu lógica actual (Generación de OTP y envío de email)
    db.query(models.CodigoTemporal).filter(models.CodigoTemporal.email == email).delete()
    
    codigo_otp = generar_codigo()
    expiracion = datetime.now() + timedelta(minutes=15)
    
    nuevo_registro = models.CodigoTemporal(email=email, codigo=codigo_otp, expiracion=expiracion)
    db.add(nuevo_registro)
    db.commit()
    
    try:
        enviar_email(destinatario=email, codigo=codigo_otp)
    except Exception as e:
        db.delete(nuevo_registro)
        db.commit()
        raise HTTPException(status_code=500, detail="Error al enviar el correo")
        
    return {"message": "Código enviado correctamente."}

@app.post("/api/auth/ciudadano/verificar")
def verificar_codigo(email: str, codigo: str, db: Session = Depends(get_db)):
    # 1. Obtener registro de la BD
    otp_record = db.query(models.CodigoTemporal).filter(
        models.CodigoTemporal.email == email,
        models.CodigoTemporal.codigo == codigo
    ).first()

    # 2. Verificar existencia
    if not otp_record:
        raise HTTPException(status_code=401, detail="Código incorrecto")

    # 3. Verificar expiración (si la hora actual es mayor a la de expiración, venció)
    if datetime.now() > otp_record.expiracion:
        # Opcional: borrar el código vencido de la BD
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=401, detail="El código ha expirado. Solicite uno nuevo.")

    # 4. Éxito
    token_jwt = crear_token_jwt({"sub": email})
    
    return {
        "access_token": token_jwt,
        "token_type": "bearer"
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

@app.post("/api/tramites/crear")
def crear_tramite(
    tramite_data: schemas.TramiteCreate,
    authorization: str = Header(...), # El cliente envía "Bearer <JWT>"
    db: Session = Depends(get_db)
):
    # 1. Extraer el token del header
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    
    token = authorization.replace("Bearer ", "")
    
    # 2. Validar el token JWT
    payload = verificar_token(token) # Función que definimos en el paso anterior
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    # 3. Obtener el email desde el payload (el 'sub' que pusimos al crear el token)
    email_ciudadano = payload.get("sub")
    
    # 4. Usar tu método CRUD existente
    # Aquí puedes pasar el email si necesitas registrar quién creó el trámite
    nuevo_tramite = crud.crear_tramite(db=db, tramite=tramite_data)
    
    return {
        "message": "Trámite creado exitosamente",
        "tramite_id": nuevo_tramite.tramite_id,
        "usuario": email_ciudadano
    }
    
# --- MODIFICACIÓN DEL ENDPOINT DE CONSULTA ---

@app.get("/api/tramites/mis-solicitudes")
def listar_solicitudes_ciudadano(email: str, db: Session = Depends(get_db)):
    """ Devuelve trámites asociados al email original """
    tramites = db.query(models.Tramite).filter(models.Tramite.email_solicitante == email).all()
    return tramites

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
    Genera y descarga el PDF del certificado usando ReportLab.
    """
    # 1. Buscar el trámite y los datos del ciudadano
    db_tramite = db.query(models.Tramite).filter(models.Tramite.tramite_id == tramite_id).first()
    
    if not db_tramite:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
        
    # 2. Verificar que el trámite esté en un estado que permita ver el certificado
    if db_tramite.estado.value != "EMITIDA":
    # El .value extrae el string "EMITIDA" del objeto EstadoTramite.EMITIDA
        raise HTTPException(
            status_code=400, 
            detail=f"El certificado no ha sido emitido. Estado actual: {db_tramite.estado.value}"
        )
    # 3. Obtener datos para el PDF (pueden venir del ciudadano asociado al trámite)
    # 1. Obtenemos nombre y cuil directamente del trámite (según lo que pusiste)
    nombre_pdf = db_tramite.nombre_solicitante 
    cuil_pdf = db_tramite.cuil

    # 2. Accedemos a la fecha desde la relación con la tabla Certificado
    # Usamos un if para evitar que el programa explote si por alguna razón 
    # el registro del certificado aún no se creó en esa tabla.
    if db_tramite.certificado:
        fecha_pdf = db_tramite.certificado.fecha_emision.strftime("%d/%m/%Y")
    else:
    # Opción de respaldo si no encuentra el registro en la tabla certificados
        fecha_pdf = datetime.now().strftime("%d/%m/%Y")

    # 4. Generar el PDF usando tu función
    pdf_buffer = generar_pdf_certificado(nombre_pdf, cuil_pdf, fecha_pdf)

    # 5. Retornar el archivo para descarga o visualización
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=certificado_{tramite_id}.pdf"}
    )

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
    """ Renderiza list-u, La lista de Usuarios (Gestión de Usuarios) """
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
    Endpoint para registrar un nuevo usuario (ADMIN/OPERADOR).
    Si el rol no es CIUDADANO, requiere contraseña.
    """
    # 1. Verificar si el login ya existe para evitar duplicados
    db_user = crud.get_usuario_by_login(db, login=usuario.login)
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="El nombre de usuario (login) ya está en uso."
        )


    if not usuario.password or len(usuario.password) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Los administradores y operadores requieren una contraseña de al menos 3 caracteres."
        )

    # 3. Llamar al CRUD para insertar en la DB
    nuevo_usuario = crud.crear_usuario(db=db, usuario=usuario)
    return nuevo_usuario