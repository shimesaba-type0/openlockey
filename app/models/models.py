from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    permanent_lock = Column(Boolean, default=False)
    
    # リレーションシップ
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    reset_requests = relationship("ResetRequest", 
                                 foreign_keys="ResetRequest.user_id", 
                                 back_populates="user", 
                                 cascade="all, delete-orphan")
    resolved_requests = relationship("ResetRequest", 
                                    foreign_keys="ResetRequest.resolved_by", 
                                    back_populates="resolver")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token_hash = Column(String, index=True)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # リレーションシップ
    user = relationship("User", back_populates="sessions")

class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=func.now())
    success = Column(Boolean)
    failure_reason = Column(String, nullable=True)
    
    # リレーションシップ
    user = relationship("User", back_populates="login_history")

class ResetRequest(Base):
    __tablename__ = "reset_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    request_reason = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    status = Column(String, default="pending")  # pending, approved, rejected
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # リレーションシップ
    user = relationship("User", foreign_keys=[user_id], back_populates="reset_requests")
    resolver = relationship("User", foreign_keys=[resolved_by], back_populates="resolved_requests")

class BackupSettings(Base):
    __tablename__ = "backup_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=True)
    frequency = Column(String, default="daily")  # daily, weekly, monthly
    retention_days = Column(Integer, default=30)
    last_backup = Column(DateTime, nullable=True)
    next_backup = Column(DateTime, nullable=True)

