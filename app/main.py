from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
import os
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.core.auth import get_current_user, get_current_admin
from app.core.template_utils import get_template_context
from app.middleware.auth_middleware import AuthMiddleware
from app.models.models import User, Session, LoginHistory, ResetRequest

# アプリケーションの初期化
app = FastAPI(
    title=settings.APP_NAME,
    description="パスフレーズベースの認証サーバー",
    version="0.1.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セッションミドルウェアの設定
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_EXPIRE_HOURS * 3600,  # 秒単位
    same_site="lax",
    https_only=not settings.DEBUG  # 本番環境ではHTTPSのみ
)

# 認証ミドルウェアの追加
app.add_middleware(AuthMiddleware)

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# テンプレートの設定
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["get_template_context"] = get_template_context

# データベースの初期化
@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    return {"status": "ok", "app_name": settings.APP_NAME}

# APIルーターのインポートと登録
from app.api import auth, users, admin
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)

# ページルーティング

# ログインページ
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    # 既にログインしている場合はダッシュボードにリダイレクト
    if getattr(request.state, "is_authenticated", False):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("auth/login.html", {"request": request})

# 登録ページ
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    # 既にログインしている場合はダッシュボードにリダイレクト
    if getattr(request.state, "is_authenticated", False):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("auth/register.html", {"request": request})

# パスフレーズリセット依頼ページ
@app.get("/reset-request", response_class=HTMLResponse)
async def reset_request_page(request: Request):
    return templates.TemplateResponse("auth/reset_request.html", {"request": request})

# ダッシュボードページ（認証必須）
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, current_user: User = Depends(get_current_user)):
    # セッションの取得
    db = request.state.db
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .where(Session.is_active == True)
        .order_by(Session.created_at.desc())
    )
    sessions = result.scalars().all()
    
    # ログイン履歴の取得
    result = await db.execute(
        select(LoginHistory)
        .where(LoginHistory.user_id == current_user.id)
        .order_by(LoginHistory.timestamp.desc())
        .limit(5)
    )
    login_history = result.scalars().all()
    
    # 現在のセッションIDを取得
    current_session_id = None
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if session_token:
        result = await db.execute(
            select(Session.id)
            .where(Session.token_hash == session_token)
        )
        current_session_id = result.scalar()
    
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": current_user,
        "sessions": sessions,
        "login_history": login_history,
        "current_session_id": current_session_id
    })

# セキュリティ設定ページ（認証必須）
@app.get("/dashboard/security", response_class=HTMLResponse)
async def security_page(request: Request, current_user: User = Depends(get_current_user)):
    # セッションの取得
    db = request.state.db
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .where(Session.is_active == True)
        .order_by(Session.created_at.desc())
    )
    sessions = result.scalars().all()
    
    return templates.TemplateResponse("dashboard/security.html", {
        "request": request,
        "user": current_user,
        "sessions": sessions,
        "now": datetime.now()
    })

# ログイン履歴ページ（認証必須）
@app.get("/dashboard/history", response_class=HTMLResponse)
async def history_page(request: Request, current_user: User = Depends(get_current_user)):
    # ログイン履歴の取得
    db = request.state.db
    page = int(request.query_params.get("page", 1))
    page_size = 10
    offset = (page - 1) * page_size
    
    # 総件数の取得
    result = await db.execute(
        select(func.count())
        .select_from(LoginHistory)
        .where(LoginHistory.user_id == current_user.id)
    )
    total_count = result.scalar()
    
    # ログイン履歴の取得
    result = await db.execute(
        select(LoginHistory)
        .where(LoginHistory.user_id == current_user.id)
        .order_by(LoginHistory.timestamp.desc())
        .offset(offset)
        .limit(page_size)
    )
    login_history = result.scalars().all()
    
    # ページネーションの計算
    total_pages = (total_count + page_size - 1) // page_size
    pages = range(max(1, page - 2), min(total_pages + 1, page + 3))
    
    pagination = {
        "current_page": page,
        "total_pages": total_pages,
        "pages": list(pages)
    }
    
    return templates.TemplateResponse("dashboard/history.html", {
        "request": request,
        "login_history": login_history,
        "pagination": pagination
    })

# 管理者ダッシュボード（管理者認証必須）
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request, current_admin: User = Depends(get_current_admin)):
    db = request.state.db
    
    # 統計データの取得
    # ユーザー数
    result = await db.execute(select(func.count()).select_from(User))
    total_users = result.scalar()
    
    # アクティブセッション数
    result = await db.execute(
        select(func.count())
        .select_from(Session)
        .where(Session.is_active == True)
        .where(Session.expires_at > datetime.utcnow())
    )
    active_sessions = result.scalar()
    
    # ロックされたアカウント数
    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            (User.permanent_lock == True) | 
            ((User.locked_until != None) & (User.locked_until > datetime.utcnow()))
        )
    )
    locked_accounts = result.scalar()
    
    # 保留中のリセットリクエスト数
    result = await db.execute(
        select(func.count())
        .select_from(ResetRequest)
        .where(ResetRequest.status == "pending")
    )
    pending_reset_requests = result.scalar()
    
    stats = {
        "total_users": total_users,
        "active_sessions": active_sessions,
        "locked_accounts": locked_accounts,
        "pending_reset_requests": pending_reset_requests
    }
    
    # 最近のアクティビティ（仮のデータ）
    recent_activities = [
        {
            "type_color": "primary",
            "icon": "person-plus",
            "message": "新規ユーザー「user1」が登録されました",
            "timestamp": datetime.now(),
            "details": None
        },
        {
            "type_color": "danger",
            "icon": "shield-exclamation",
            "message": "ユーザー「user2」が5回連続でログインに失敗し、アカウントがロックされました",
            "timestamp": datetime.now(),
            "details": "IP: 192.168.1.100"
        }
    ]
    
    # 最近のログイン試行
    result = await db.execute(
        select(LoginHistory, User.username)
        .join(User, LoginHistory.user_id == User.id)
        .order_by(LoginHistory.timestamp.desc())
        .limit(10)
    )
    recent_login_attempts_data = result.all()
    
    recent_login_attempts = []
    for login_history, username in recent_login_attempts_data:
        recent_login_attempts.append({
            "timestamp": login_history.timestamp,
            "user_id": login_history.user_id,
            "username": username,
            "ip_address": login_history.ip_address,
            "user_agent": login_history.user_agent,
            "success": login_history.success,
            "failure_reason": login_history.failure_reason
        })
    
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "stats": stats,
        "recent_activities": recent_activities,
        "recent_login_attempts": recent_login_attempts
    })

# ユーザー管理ページ（管理者認証必須）
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, current_admin: User = Depends(get_current_admin)):
    db = request.state.db
    
    # クエリパラメータの取得
    page = int(request.query_params.get("page", 1))
    search_query = request.query_params.get("q", "")
    status_filter = request.query_params.get("status", "all")
    
    page_size = 10
    offset = (page - 1) * page_size
    
    # クエリの構築
    query = select(User)
    
    # 検索条件の適用
    if search_query:
        query = query.where(User.username.ilike(f"%{search_query}%"))
    
    # ステータスフィルターの適用
    if status_filter == "active":
        query = query.where(User.is_active == True)
    elif status_filter == "inactive":
        query = query.where(User.is_active == False)
    elif status_filter == "locked":
        query = query.where(
            (User.permanent_lock == True) | 
            ((User.locked_until != None) & (User.locked_until > datetime.utcnow()))
        )
    elif status_filter == "admin":
        query = query.where(User.is_admin == True)
    
    # 総件数の取得
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total_count = result.scalar()
    
    # ユーザーの取得
    query = query.order_by(User.username).offset(offset).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # ページネーションの計算
    total_pages = (total_count + page_size - 1) // page_size
    pages = range(max(1, page - 2), min(total_pages + 1, page + 3))
    
    pagination = {
        "current_page": page,
        "total_pages": total_pages,
        "pages": list(pages)
    }
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "users": users,
        "pagination": pagination,
        "search_query": search_query,
        "status_filter": status_filter,
        "now": datetime.now()
    })

# システムログページ（管理者認証必須）
@app.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs_page(request: Request, current_admin: User = Depends(get_current_admin)):
    # 仮のログデータ
    logs = [
        {
            "timestamp": datetime.now(),
            "level": "INFO",
            "type": "auth",
            "user_id": 1,
            "username": "admin",
            "ip_address": "127.0.0.1",
            "message": "ログイン成功",
            "details": None
        },
        {
            "timestamp": datetime.now() - timedelta(minutes=5),
            "level": "WARNING",
            "type": "auth",
            "user_id": 2,
            "username": "user1",
            "ip_address": "192.168.1.1",
            "message": "ログイン失敗: パスフレーズが正しくありません",
            "details": {"attempt": 1, "browser": "Chrome", "os": "Windows"}
        },
        {
            "timestamp": datetime.now() - timedelta(minutes=10),
            "level": "ERROR",
            "type": "system",
            "user_id": None,
            "username": None,
            "ip_address": None,
            "message": "データベース接続エラー",
            "details": {"error": "Connection refused", "db": "postgres"}
        }
    ]
    
    return templates.TemplateResponse("admin/logs.html", {
        "request": request,
        "logs": logs
    })

# システム設定ページ（管理者認証必須）
@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request, current_admin: User = Depends(get_current_admin)):
    # 仮の設定データ
    settings_data = {
        # 認証設定
        "session_expire_hours": 24,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 30,
        "min_password_length": 12,
        "require_special_chars": True,
        "require_numbers": True,
        "require_mixed_case": True,
        
        # システム設定
        "app_name": "OpenLockey",
        "listen_ip": "0.0.0.0",
        "listen_port": 8000,
        "debug": True,
        "log_level": "INFO",
        
        # バックアップ設定
        "enable_auto_backup": True,
        "backup_interval_hours": 24,
        "backup_retention_days": 30,
        "backup_path": "/app/backups",
        
        # メール設定
        "enable_email": False,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user@example.com",
        "smtp_password": "password",
        "email_sender": "noreply@example.com",
        "smtp_use_tls": True
    }
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "settings": settings_data
    })

# リセット依頼管理ページ（管理者認証必須）
@app.get("/admin/reset-requests", response_class=HTMLResponse)
async def admin_reset_requests_page(request: Request, current_admin: User = Depends(get_current_admin)):
    db = request.state.db
    
    # リセットリクエストの取得
    result = await db.execute(
        select(ResetRequest, User.username.label("username"), 
               User.username.label("resolver_username"))
        .join(User, ResetRequest.user_id == User.id)
        .outerjoin(User, ResetRequest.resolved_by == User.id, isouter=True)
        .order_by(ResetRequest.timestamp.desc())
    )
    reset_requests_data = result.all()
    
    reset_requests = []
    for request_data in reset_requests_data:
        reset_requests.append({
            "id": request_data.ResetRequest.id,
            "user_id": request_data.ResetRequest.user_id,
            "username": request_data.username,
            "request_reason": request_data.ResetRequest.request_reason,
            "timestamp": request_data.ResetRequest.timestamp,
            "status": request_data.ResetRequest.status,
            "resolved_by": request_data.ResetRequest.resolved_by,
            "resolver_username": request_data.resolver_username,
            "resolved_at": request_data.ResetRequest.resolved_at
        })
    
    return templates.TemplateResponse("admin/reset_requests.html", {
        "request": request,
        "reset_requests": reset_requests
    })

# ログアウト処理
@app.get("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # セッションクッキーからトークンを取得
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    
    if session_token:
        # セッションを検索して無効化
        result = await db.execute(select(Session).where(Session.token_hash == session_token))
        session = result.scalars().first()
        
        if session:
            session.is_active = False
            await db.commit()
    
    # セッションからユーザー情報を削除
    if "user" in request.session:
        del request.session["user"]
    
    # セッションクッキーを削除
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    return RedirectResponse(url="/", status_code=303)

# アプリケーションの実行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.LISTEN_IP,
        port=settings.LISTEN_PORT,
        reload=settings.DEBUG
    )

