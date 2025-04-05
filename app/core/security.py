from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets
import string
from app.core.config import settings

# パスワードハッシュ化のためのコンテキスト
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """パスワードを検証する"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """パスワードをハッシュ化する"""
    return pwd_context.hash(password)

def generate_session_token():
    """セッショントークンを生成する"""
    return secrets.token_urlsafe(32)

def generate_password(length=64):
    """安全なパスフレーズを生成する"""
    # 使用する文字セット（仕様に従って視覚的に混同しやすい文字を除外）
    lowercase = "abcdefghijkmnopqrstuvwxyz"  # l を除外
    uppercase = "ABCDEFGHJKLMNPQRSTUVWXYZ"   # I, O を除外
    digits = "23456789"                      # 0, 1 を除外

    # 全ての文字セットを組み合わせる
    alphabet = lowercase + uppercase + digits
    
    # 少なくとも1つの大文字、小文字、数字を含むようにする
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c in lowercase for c in password) and
            any(c in uppercase for c in password) and
            any(c in digits for c in password)):
            break
    
    return password

def is_locked(user):
    """ユーザーがロックされているかどうかを確認する"""
    if user.permanent_lock:
        return True
    
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True
    
    return False

def should_lock_user(user):
    """ユーザーをロックすべきかどうかを確認する"""
    if user.failed_login_attempts >= settings.FAIL_LOCK_ATTEMPTS:
        return True
    return False

def get_lock_duration():
    """ロック期間を取得する"""
    return timedelta(hours=settings.FAIL_LOCK_DURATION_HOURS)

def reset_failed_attempts(user):
    """失敗したログイン試行回数をリセットする"""
    user.failed_login_attempts = 0
    user.locked_until = None

