from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.models import User, Session
from app.core.config import settings

async def get_current_user_from_session(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """
    セッションからユーザーを取得する
    """
    # セッションクッキーからトークンを取得
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    
    if not session_token:
        return None
    
    # セッションをデータベースから検索
    result = await db.execute(
        select(Session)
        .where(Session.token_hash == session_token)
        .where(Session.is_active == True)
        .where(Session.expires_at > datetime.utcnow())
    )
    session = result.scalars().first()
    
    if not session:
        return None
    
    # ユーザーを取得
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    
    if not user or not user.is_active:
        return None
    
    return user

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    現在のユーザーを取得する依存関係
    認証が必要なエンドポイントで使用する
    """
    user = await get_current_user_from_session(request, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です。",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    現在の管理者ユーザーを取得する依存関係
    管理者権限が必要なエンドポイントで使用する
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です。"
        )
    
    return current_user

async def authenticate_user(
    request: Request, 
    response: Request, 
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザー認証ミドルウェア
    """
    user = await get_current_user_from_session(request, db)
    
    # リクエストのセッションにユーザー情報を保存
    if user:
        request.state.user = user
        request.state.is_authenticated = True
    else:
        request.state.user = None
        request.state.is_authenticated = False

