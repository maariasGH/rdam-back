from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from .models import EstadoTramite, RolUsuario

# --- ESQUEMAS DE USUARIO ---

class UsuarioBase(BaseModel):
    nombre_completo: str
    login: str
    rol: RolUsuario

class UsuarioCreate(UsuarioBase):
    password: str  # Se recibe como texto plano y se hashea en el CRUD

class Usuario(UsuarioBase):
    usuario_id: int
    estado: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# --- ESQUEMAS DE TRÁMITE ---

class TramiteBase(BaseModel):
    cuil: str = Field(..., min_length=11, max_length=15, description="CUIL sin guiones")
    nombre_solicitante: str
    email_contacto: EmailStr
    ciudad_solicitante: str

class TramiteCreate(TramiteBase):
    pass

class Tramite(TramiteBase):
    tramite_id: int
    estado: EstadoTramite
    fecha_solicitud: date
    usuario_creador_id: int
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