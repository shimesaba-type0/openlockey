from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from datetime import datetime
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_password_hash, generate_password
from app.models.models import User, Session, LoginHistory, ResetRequest
from app.schemas.schemas import UserOut, UserPasswordReset, ResetRequestUpdate
from app.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

# 管理者権限チェック用の依存関係
async def get_admin_user(request: Request, db: AsyncSession = Depends(get_db)):
    """管理者権限を持つユーザーを取得する"""
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
    
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です。"
        )
    
    return user

@router.get("/users", response_model=List[UserOut])
async def list_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status_filter: Optional[str] = None
):
    """ユーザー一覧を取得する"""
    query = select(User)
    
    # 検索条件の適用
    if search:
        query = query.where(User.username.ilike(f"%{search}%"))
    
    # ステータスフィルターの適用
    if status_filter:
        if status_filter == "active":
            query = query.where(User.is_active == True)
        elif status_filter == "inactive":
            query = query.where(User.is_active == False)
        elif status_filter == "locked":
            query = query.where(or_(
                User.permanent_lock == True,
                and_(User.locked_until != None, User.locked_until > datetime.utcnow())
            ))
        elif status_filter == "admin":
            query = query.where(User.is_admin == True)
    
    # ページネーション
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users

@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """特定のユーザー情報を取得する"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。"
        )
    
    return user

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: dict,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー情報を更新する"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。"
        )
    
    # ユーザー名の更新（指定された場合）
    if "username" in user_data:
        # 既存のユーザー名と異なる場合のみチェック
        if user_data["username"] != user.username:
            # ユーザー名が既に存在するか確認
            result = await db.execute(select(User).where(User.username == user_data["username"]))
            existing_user = result.scalars().first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="このユーザー名は既に使用されています。"
                )
            
            user.username = user_data["username"]
    
    # 管理者権限の更新（指定された場合）
    if "is_admin" in user_data:
        user.is_admin = user_data["is_admin"]
    
    # アクティブ状態の更新（指定された場合）
    if "is_active" in user_data:
        user.is_active = user_data["is_active"]
    
    # ロック状態の更新（指定された場合）
    if "permanent_lock" in user_data:
        user.permanent_lock = user_data["permanent_lock"]
    
    # 一時ロックの更新（指定された場合）
    if "locked_until" in user_data:
        user.locked_until = user_data["locked_until"]
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "success", "message": "ユーザー情報が正常に更新されました。"}

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    reset_data: UserPasswordReset,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザーのパスワードをリセットする"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません。"
        )
    
    # パスワードの生成または設定
    new_password = reset_data.new_password
    if reset_data.generate_password:
        new_password = generate_password(length=reset_data.password_length)
    
    # パスワードのハッシュ化と保存
    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    user.failed_login_attempts = 0
    user.locked_until = None
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "パスワードがリセットされました。",
        "new_password": new_password if reset_data.generate_password else None
    }

@router.get("/reset-requests")
async def list_reset_requests(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None
):
    """パスワードリセットリクエスト一覧を取得する"""
    query = select(ResetRequest)
    
    # ステータスフィルターの適用
    if status:
        query = query.where(ResetRequest.status == status)
    
    # 日付の降順でソート
    query = query.order_by(ResetRequest.timestamp.desc())
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    # ユーザー情報を含める
    request_list = []
    for req in requests:
        user_result = await db.execute(select(User).where(User.id == req.user_id))
        user = user_result.scalars().first()
        
        request_data = {
            "id": req.id,
            "user_id": req.user_id,
            "username": user.username if user else "不明なユーザー",
            "request_reason": req.request_reason,
            "timestamp": req.timestamp,
            "status": req.status,
            "resolved_by": req.resolved_by,
            "resolved_at": req.resolved_at
        }
        
        if req.resolved_by:
            resolver_result = await db.execute(select(User).where(User.id == req.resolved_by))
            resolver = resolver_result.scalars().first()
            request_data["resolver_username"] = resolver.username if resolver else "不明な管理者"
        else:
            request_data["resolver_username"] = None
        
        request_list.append(request_data)
    
    return request_list

@router.put("/reset-requests/{request_id}")
async def update_reset_request(
    request_id: int,
    update_data: ResetRequestUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """パスワードリセットリクエストのステータスを更新する"""
    result = await db.execute(select(ResetRequest).where(ResetRequest.id == request_id))
    reset_request = result.scalars().first()
    
    if not reset_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="リセットリクエストが見つかりません。"
        )
    
    # すでに解決済みの場合はエラー
    if reset_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このリクエストはすでに処理されています。"
        )
    
    # ステータスの更新
    reset_request.status = update_data.status
    reset_request.resolved_by = admin.id
    reset_request.resolved_at = datetime.utcnow()
    
    await db.commit()
    
    # 承認された場合、ユーザーのロックを解除
    if update_data.status == "approved":
        result = await db.execute(select(User).where(User.id == reset_request.user_id))
        user = result.scalars().first()
        
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            # 永続的なロックは解除しない（管理者が明示的に解除する必要がある）
            
            await db.commit()
    
    return {"status": "success", "message": "リセットリクエストが更新されました。"}

@router.get("/stats")
async def get_admin_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理者ダッシュボード用の統計情報を取得する"""
    # 総ユーザー数
    result = await db.execute(select(User))
    total_users = len(result.scalars().all())
    
    # アクティブなセッション数
    result = await db.execute(select(Session).where(
        Session.is_active == True,
        Session.expires_at > datetime.utcnow()
    ))
    active_sessions = len(result.scalars().all())
    
    # ロックされたアカウント数
    result = await db.execute(select(User).where(or_(
        User.permanent_lock == True,
        and_(User.locked_until != None, User.locked_until > datetime.utcnow())
    )))
    locked_accounts = len(result.scalars().all())
    
    # 保留中のリセットリクエスト数
    result = await db.execute(select(ResetRequest).where(ResetRequest.status == "pending"))
    pending_reset_requests = len(result.scalars().all())
    
    # 最近のログイン試行
    result = await db.execute(
        select(LoginHistory)
        .order_by(LoginHistory.timestamp.desc())
        .limit(10)
    )
    recent_login_attempts = []
    
    for login in result.scalars().all():
        user_result = await db.execute(select(User).where(User.id == login.user_id))
        user = user_result.scalars().first()
        
        recent_login_attempts.append({
            "timestamp": login.timestamp,
            "user_id": login.user_id,
            "username": user.username if user else "不明なユーザー",
            "ip_address": login.ip_address,
            "user_agent": login.user_agent,
            "success": login.success,
            "failure_reason": login.failure_reason
        })
    
    return {
        "total_users": total_users,
        "active_sessions": active_sessions,
        "locked_accounts": locked_accounts,
        "pending_reset_requests": pending_reset_requests,
        "recent_login_attempts": recent_login_attempts
    }

