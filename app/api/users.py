from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, generate_password
from app.models.models import User, Session
from app.schemas.schemas import UserUpdate, UserPasswordChange, PasswordGenerateRequest, PasswordGenerateResponse
from app.core.config import settings

router = APIRouter(prefix="/api/user", tags=["users"])

@router.post("/password/generate", response_model=PasswordGenerateResponse)
async def generate_secure_password(request: PasswordGenerateRequest):
    """安全なパスフレーズを生成する"""
    password = generate_password(length=request.length)
    return {"password": password}

@router.put("/password")
async def change_password(
    password_data: UserPasswordChange,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """ユーザーのパスワードを変更する"""
    # セッションからユーザーを取得
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証されていません。"
        )
    
    # セッションの検索
    result = await db.execute(select(Session).where(
        Session.token_hash == session_token,
        Session.is_active == True,
        Session.expires_at > datetime.utcnow()
    ))
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが無効または期限切れです。"
        )
    
    # ユーザーの検索
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。"
        )
    
    # 現在のパスワードを検証
    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスフレーズが正しくありません。"
        )
    
    # 新しいパスワードをハッシュ化して保存
    user.password_hash = get_password_hash(password_data.new_password)
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"status": "success", "message": "パスフレーズが正常に変更されました。"}

@router.get("/profile")
async def get_user_profile(request: Request, db: AsyncSession = Depends(get_db)):
    """ユーザープロファイルを取得する"""
    # セッションからユーザーを取得
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証されていません。"
        )
    
    # セッションの検索
    result = await db.execute(select(Session).where(
        Session.token_hash == session_token,
        Session.is_active == True,
        Session.expires_at > datetime.utcnow()
    ))
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが無効または期限切れです。"
        )
    
    # ユーザーの検索
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。"
        )
    
    # アクティブなセッションの数を取得
    result = await db.execute(select(Session).where(
        Session.user_id == user.id,
        Session.is_active == True,
        Session.expires_at > datetime.utcnow()
    ))
    active_sessions = result.scalars().all()
    
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "active_sessions": len(active_sessions)
    }

@router.put("/profile")
async def update_user_profile(
    user_data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """ユーザープロファイルを更新する"""
    # セッションからユーザーを取得
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証されていません。"
        )
    
    # セッションの検索
    result = await db.execute(select(Session).where(
        Session.token_hash == session_token,
        Session.is_active == True,
        Session.expires_at > datetime.utcnow()
    ))
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが無効または期限切れです。"
        )
    
    # ユーザーの検索
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。"
        )
    
    # 管理者でない場合、is_adminとis_activeフィールドは更新できない
    if not user.is_admin:
        user_data.is_admin = None
        user_data.is_active = None
    
    # ユーザー名の更新（指定された場合）
    if user_data.username is not None:
        # 既存のユーザー名と異なる場合のみチェック
        if user_data.username != user.username:
            # ユーザー名が既に存在するか確認
            result = await db.execute(select(User).where(User.username == user_data.username))
            existing_user = result.scalars().first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="このユーザー名は既に使用されています。"
                )
            
            user.username = user_data.username
    
    # 管理者権限の更新（指定された場合、かつ管理者の場合）
    if user_data.is_admin is not None and user.is_admin:
        user.is_admin = user_data.is_admin
    
    # アクティブ状態の更新（指定された場合、かつ管理者の場合）
    if user_data.is_active is not None and user.is_admin:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "success", "message": "プロファイルが正常に更新されました。"}

