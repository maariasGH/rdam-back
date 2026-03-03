from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Date, Numeric, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base 

# 1. Enums
class EstadoTramite(enum.Enum):
    PENDIENTE = "PENDIENTE"
    VENCIDA = "VENCIDA"
    PAGADA = "PAGADA"
    EMITIDA = "EMITIDA"
    RECHAZADA = "RECHAZADA"
    EMITIDA_VENCIDA = "EMITIDA_VENCIDA"

class RolUsuario(enum.Enum):
    CIUDADANO = "CIUDADANO"
    OPERADOR = "OPERADOR"
    ADMINISTRADOR = "ADMINISTRADOR"

# 2. Tabla de Usuarios con Relación Recursiva
class Usuario(Base):
    __tablename__ = "usuarios"

    usuario_id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(100), nullable=False)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=True)
    rol = Column(Enum(RolUsuario), nullable=False)
    estado = Column(String(20), server_default="Activo")
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Columna para la relación retrospectiva (¿Quién creó a este usuario?)
    registrador_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=True)

    # RELACIONES
    # 1. Un ciudadano crea trámites
    tramites_creados = relationship("Tramite", back_populates="creador")
    
    # 2. Un operador emite certificados
    certificados_emitidos = relationship("Certificado", back_populates="emisor")
    
    # 3. Relación Recursiva (Admin gestiona Usuarios)
    # El 'registrador' es el admin que creó la cuenta
    registrador = relationship("Usuario", remote_side=[usuario_id], backref="usuarios_registrados")

# 3. Tabla de Trámites
class Tramite(Base):
    __tablename__ = "tramites"

    tramite_id = Column(Integer, primary_key=True, index=True)
    cuil = Column(String(15), nullable=False, index=True)
    nombre_solicitante = Column(String(100), nullable=False)
    email_contacto = Column(String(100), nullable=False)
    estado = Column(Enum(EstadoTramite), server_default="PENDIENTE", index=True)
    fecha_solicitud = Column(Date, server_default=func.current_date())
    usuario_creador_id = Column(Integer, ForeignKey("usuarios.usuario_id"))
    fecha_ultima_modificacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ciudad_solicitante = Column(String(50), nullable=False)

    creador = relationship("Usuario", back_populates="tramites_creados")
    pago = relationship("Pago", back_populates="tramite", uselist=False)
    certificado = relationship("Certificado", back_populates="tramite", uselist=False)

# 4. Tabla de Pagos (Relacionada solo al trámite)
class Pago(Base):
    __tablename__ = "pagos"

    pago_id = Column(Integer, primary_key=True, index=True)
    tramite_id = Column(Integer, ForeignKey("tramites.tramite_id"))
    external_reference = Column(String(100))
    monto = Column(Numeric(10, 2), server_default="1250.00")
    fecha_pago = Column(DateTime(timezone=True))
    pagado = Column(Boolean, server_default="false")

    tramite = relationship("Tramite", back_populates="pago")

# 5. Tabla de Certificados
class Certificado(Base):
    __tablename__ = "certificados"

    certificado_id = Column(Integer, primary_key=True, index=True)
    tramite_id = Column(Integer, ForeignKey("tramites.tramite_id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id")) 
    
    fecha_emision = Column(DateTime(timezone=True), server_default=func.now())
    url_archivo_s3 = Column(Text)

    tramite = relationship("Tramite", back_populates="certificado")
    emisor = relationship("Usuario", back_populates="certificados_emitidos")