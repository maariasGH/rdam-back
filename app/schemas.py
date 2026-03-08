from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from .models import EstadoTramite, RolUsuario

# --- ESQUEMAS DE USUARIO ---

class UsuarioBase(BaseModel):
    nombre_completo: str
    login: str
    rol: RolUsuario
    registrador_id: int

class UsuarioCreate(UsuarioBase):
    password: Optional[str] = None  # <-- Solo para Admins y Op

class UsuarioLogin(BaseModel):
    login: str
    password: str

class UsuarioRespuesta(UsuarioBase):
    usuario_id: int

    class Config:
        from_attributes = True # O orm_mode = True porque usamos Pydantic v1
        
class UsuarioUpdate(BaseModel):
    nombre_completo: str
    login: str
    rol: RolUsuario
    password: Optional[str] = None

    class Config:
        from_attributes = True

# --- ESQUEMAS DE TRÁMITE ---

class TramiteBase(BaseModel):
    cuil: str = Field(..., min_length=11, max_length=15, description="CUIL sin guiones")
    nombre_solicitante: str
    email_contacto: EmailStr
    ciudad_solicitante: str
    fecha_solicitud: date

class TramiteCreate(TramiteBase):
    pass

class Tramite(TramiteBase):
    tramite_id: int
    estado: EstadoTramite
    fecha_solicitud: date
    fecha_ultima_modificacion: datetime

    class Config:
        from_attributes = True

# --- ESQUEMAS DE PAGO ---

class PagoBase(BaseModel):
    external_reference: Optional[str] = None
    monto: float = 1250.00

class PagoCreate(PagoBase):
    tramite_id: int

class Pago(PagoBase):
    pago_id: int
    fecha_pago: Optional[datetime]
    pagado: bool

    class Config:
        from_attributes = True

# --- ESQUEMAS DE CERTIFICADO ---

class CertificadoBase(BaseModel):
    url_archivo_s3: str

class CertificadoCreate(CertificadoBase):
    tramite_id: int
    usuario_id: int # ID del Operador que emite

class Certificado(CertificadoBase):
    certificado_id: int
    fecha_emision: datetime

    class Config:
        from_attributes = True