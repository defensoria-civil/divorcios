from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from .db import Base

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    phone = Column(String(32), index=True, nullable=False)
    status = Column(String(32), default="new")
    type = Column(String(16), nullable=True)  # unilateral | conjunta
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # simple progress tracking
    phase = Column(String(32), default="inicio")

    # collected data (denormalized for speed; also stored in Persons)
    nombre = Column(String(120), nullable=True)  # Nombre completo (deprecado, usar apellido + nombres)
    apellido = Column(String(80), nullable=True)
    nombres = Column(String(80), nullable=True)
    dni = Column(String(16), nullable=True)
    cuit = Column(String(16), nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)
    domicilio = Column(Text, nullable=True)
    email = Column(String(120), nullable=True)
    ocupacion = Column(String(80), nullable=True)
    nacionalidad = Column(String(32), default="argentino/a")
    
    # document references (media IDs from WhatsApp)
    dni_image_url = Column(String(255), nullable=True)
    marriage_cert_url = Column(String(255), nullable=True)
    
    # marriage data
    fecha_matrimonio = Column(Date, nullable=True)
    lugar_matrimonio = Column(String(255), nullable=True)
    fecha_separacion = Column(Date, nullable=True)
    
    # datos del acta de matrimonio (extraídos por OCR)
    acta_numero = Column(String(16), nullable=True)
    acta_libro = Column(String(32), nullable=True)
    acta_anio = Column(String(8), nullable=True)
    acta_foja = Column(String(16), nullable=True)
    acta_oficina = Column(String(120), nullable=True)
    
    # spouse data
    nombre_conyuge = Column(String(120), nullable=True)  # Nombre completo (deprecado)
    apellido_conyuge = Column(String(80), nullable=True)
    nombres_conyuge = Column(String(80), nullable=True)
    dni_conyuge = Column(String(16), nullable=True)
    cuit_conyuge = Column(String(16), nullable=True)
    domicilio_conyuge = Column(Text, nullable=True)
    fecha_nacimiento_conyuge = Column(Date, nullable=True)
    ocupacion_conyuge = Column(String(80), nullable=True)
    nacionalidad_conyuge = Column(String(32), default="argentino/a")
    phone_conyuge = Column(String(32), nullable=True)
    email_conyuge = Column(String(120), nullable=True)
    
    # children info
    tiene_hijos = Column(Boolean, nullable=True)
    info_hijos = Column(Text, nullable=True)
    
    # assets info
    tiene_bienes = Column(Boolean, nullable=True)
    info_bienes = Column(Text, nullable=True)

    messages = relationship("Message", back_populates="case", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    role = Column(String(16))  # user|assistant|system
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="messages")

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    kind = Column(String(16))  # immediate|session|episodic|semantic
    content = Column(Text)
    embedding = Column(Vector(768))
    created_at = Column(DateTime, default=datetime.utcnow)

class SemanticKnowledge(Base):
    __tablename__ = "semantic_knowledge"
    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    content = Column(Text)
    embedding = Column(Vector(768))
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    """Modelo de usuario para autenticación y autorización"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120))
    role = Column(String(32), default="operator")  # operator | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
