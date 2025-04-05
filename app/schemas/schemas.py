from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# ユーザー関連スキーマ
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=32, max_length=128)
    is_admin: bool = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=32, max_length=128)

class UserPasswordReset(BaseModel):
    user_id: int
    new_password: Optional[str] = Field(None, min_length=32, max_length=128)
    generate_password: bool = True
    password_length: int = Field(64, ge=32, le=128)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    permanent_lock: bool

    class Config:
        orm_mode = True

# セッション関連スキーマ
class SessionBase(BaseModel):
    user_agent: str
    ip_address: str

class SessionCreate(SessionBase):
    user_id: int
    expires_at: datetime

class SessionOut(SessionBase):
    id: int
    created_at: datetime
    expires_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

# ログイン履歴関連スキーマ
class LoginHistoryOut(BaseModel):
    id: int
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None

    class Config:
        orm_mode = True

# リセットリクエスト関連スキーマ
class ResetRequestCreate(BaseModel):
    user_id: int
    request_reason: str

class ResetRequestUpdate(BaseModel):
    status: str
    resolved_by: int

class ResetRequestOut(BaseModel):
    id: int
    user_id: int
    request_reason: str
    timestamp: datetime
    status: str
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# バックアップ設定関連スキーマ
class BackupSettingsUpdate(BaseModel):
    enabled: bool
    frequency: str
    retention_days: int

class BackupSettingsOut(BaseModel):
    id: int
    enabled: bool
    frequency: str
    retention_days: int
    last_backup: Optional[datetime] = None
    next_backup: Optional[datetime] = None

    class Config:
        orm_mode = True

# パスフレーズ生成スキーマ
class PasswordGenerateRequest(BaseModel):
    length: int = Field(64, ge=32, le=128)

class PasswordGenerateResponse(BaseModel):
    password: str

