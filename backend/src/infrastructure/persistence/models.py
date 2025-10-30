from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
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
    nombre = Column(String(120), nullable=True)
    dni = Column(String(16), nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)
    domicilio = Column(Text, nullable=True)

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
