from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    source_ip = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BlockedIP(Base):
    __tablename__ = "blocked_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, index=True, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, index=True)
    command = Column(String, nullable=False)
    result = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())