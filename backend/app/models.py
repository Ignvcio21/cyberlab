from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String, unique=True, index=True, nullable=False)
    contrasena = Column(String, nullable=False)


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    tipo_evento = Column(String, nullable=False)
    ip_origen = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    severidad = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())


class IpBloqueada(Base):
    __tablename__ = "ips_bloqueadas"

    id = Column(Integer, primary_key=True, index=True)
    direccion_ip = Column(String, unique=True, index=True, nullable=False)
    motivo = Column(String, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())


class AccionUsuario(Base):
    __tablename__ = "acciones_usuario"

    id = Column(Integer, primary_key=True, index=True)
    comando = Column(String, nullable=False)
    resultado = Column(String, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())