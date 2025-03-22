from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import secrets

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, generate_session_token
from app.models.models import User, Session, LoginHistory
from app.schemas.schemas import UserCreate, UserLogin, UserOut, SessionOut
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """新規ユーザーを登録する"""
    # ユーザー名が既に存在するか確認
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に使用されています。"
        )
    
    # 新規ユーザーの作成
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        is_admin=user_data.is_admin
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.post("/login")
async def login(
    user_data: UserLogin, 
    response: Response, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """ユーザーログイン処理"""
    # ユーザーの検索
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalars().first()
    
    # ログイン履歴の作成準備
    login_history = LoginHistory(
        user_id=user.id if user else None,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        success=False
    )
    
    # ユーザーが存在しない場合
    if not user:
        login_history.failure_reason = "ユーザーが存在しません。"
        db.add(login_history)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました。"
        )
    
    # アカウントがロックされている場合
    if user.permanent_lock:
        login_history.failure_reason = "アカウントが永続的にロックされています。"
        db.add(login_history)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="このアカウントはロックされています。管理者に連絡してください。"
        )
    
    if user.locked_until and user.locked_until > datetime.utcnow():
        login_history.failure_reason = "アカウントが一時的にロックされています。"
        db.add(login_history)
        await db.commit()
        
        lock_remaining = (user.locked_until - datetime.utcnow()).total_seconds() / 60
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"このアカウントは一時的にロックされています。約{int(lock_remaining)}分後に再試行してください。"
        )
    
    # パスワード検証
    if not verify_password(user_data.password, user.password_hash):
        # 失敗したログイン試行回数を増やす
        user.failed_login_attempts += 1
        
        # ロック条件を確認
        if user.failed_login_attempts >= settings.FAIL_LOCK_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(hours=settings.FAIL_LOCK_DURATION_HOURS)
            login_history.failure_reason = "パスフレーズが正しくありません。アカウントがロックされました。"
        else:
            login_history.failure_reason = "パスフレーズが正しくありません。"
        
        db.add(login_history)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました。"
        )
    
    # 認証成功
    # 失敗したログイン試行回数をリセット
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    
    # セッションの作成
    session_token = generate_session_token()
    session_expires = datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)
    
    new_session = Session(
        user_id=user.id,
        token_hash=session_token,  # 実際の実装ではハッシュ化すべき
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        expires_at=session_expires,
        is_active=True
    )
    
    db.add(new_session)
    
    # ログイン履歴を更新
    login_history.success = True
    login_history.failure_reason = None
    db.add(login_history)
    
    await db.commit()
    await db.refresh(new_session)
    
    # セッションクッキーの設定
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        secure=not settings.DEBUG,  # 本番環境ではセキュアクッキーを使用
        samesite="lax"
    )

    # セッションにユーザー情報を保存
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
    }
    
    return {
        "status": "success",
        "message": "ログインに成功しました。",
        "user": {
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    }

@router.post("/logout")
async def logout(
    request: Request, 
    response: Response, 
    db: AsyncSession = Depends(get_db)
):
    """ユーザーログアウト処理"""
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    
    if session_token:
        # セッションを検索して無効化
        result = await db.execute(select(Session).where(Session.token_hash == session_token))
        session = result.scalars().first()
        
        if session:
            session.is_active = False
            await db.commit()
    
    # クッキーを削除
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )

    # セッションからユーザー情報を削除
    if "user" in request.session:
        del request.session["user"]
    
    return {"status": "success", "message": "ログアウトしました。"}

@router.post("/reset-request")
async def request_password_reset(
    request: Request, 
    username: str, 
    reason: str, 
    db: AsyncSession = Depends(get_db)
):
    """パスワードリセットをリクエストする"""
    # ユーザーの検索
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if not user:
        # ユーザーが存在しない場合でも成功を返す（セキュリティ上の理由）
        return {
            "status": "success",
            "message": "リセットリクエストが送信されました。管理者による確認をお待ちください。"
        }
    
    # リセットリクエストの作成
    new_request = ResetRequest(
        user_id=user.id,
        request_reason=reason,
        status="pending"
    )
    
    db.add(new_request)
    await db.commit()
    
    return {
        "status": "success",
        "message": "リセットリクエストが送信されました。管理者による確認をお待ちください。"
    }

