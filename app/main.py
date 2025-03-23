from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import os
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.models import models

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

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# テンプレートの設定
templates = Jinja2Templates(directory="app/templates")

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
    return templates.TemplateResponse("auth/login.html", {"request": request})

# 登録ページ
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

# パスフレーズリセット依頼ページ
@app.get("/reset-request", response_class=HTMLResponse)
async def reset_request_page(request: Request):
    return templates.TemplateResponse("auth/reset_request.html", {"request": request})

# ダッシュボードページ（認証必須）
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    # TODO: 認証チェック
    # 仮のユーザーデータとセッションデータ
    user = {
        "username": "testuser",
        "created_at": datetime.now(),
        "last_login": datetime.now(),
        "is_active": True,
        "is_admin": False,
        "failed_login_attempts": 0
    }
    
    sessions = [
        {
            "id": 1,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "ip_address": "127.0.0.1",
            "created_at": datetime.now()
        }
    ]
    
    login_history = [
        {
            "timestamp": datetime.now(),
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "success": True,
            "failure_reason": None
        }
    ]
    
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": user,
        "sessions": sessions,
        "login_history": login_history,
        "current_session_id": 1
    })

# セキュリティ設定ページ（認証必須）
@app.get("/dashboard/security", response_class=HTMLResponse)
async def security_page(request: Request):
    # TODO: 認証チェック
    # 仮のユーザーデータとセッションデータ
    user = {
        "username": "testuser",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "last_login": datetime.now(),
        "is_active": True,
        "is_admin": False,
        "failed_login_attempts": 0,
        "locked_until": None,
        "permanent_lock": False
    }
    
    sessions = [
        {
            "id": 1,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "ip_address": "127.0.0.1",
            "created_at": datetime.now()
        }
    ]
    
    return templates.TemplateResponse("dashboard/security.html", {
        "request": request,
        "user": user,
        "sessions": sessions,
        "now": datetime.now()
    })

# ログイン履歴ページ（認証必須）
@app.get("/dashboard/history", response_class=HTMLResponse)
async def history_page(request: Request):
    # TODO: 認証チェック
    # 仮のログイン履歴データ
    login_history = [
        {
            "timestamp": datetime.now(),
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "success": True,
            "failure_reason": None
        },
        {
            "timestamp": datetime.now(),
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "success": False,
            "failure_reason": "パスフレーズが正しくありません。"
        }
    ]
    
    # 仮のページネーションデータ
    pagination = {
        "current_page": 1,
        "total_pages": 1,
        "pages": [1]
    }
    
    return templates.TemplateResponse("dashboard/history.html", {
        "request": request,
        "login_history": login_history,
        "pagination": pagination
    })

# 管理者ダッシュボード（管理者認証必須）
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    # TODO: 管理者認証チェック
    # 仮の統計データ
    stats = {
        "total_users": 10,
        "active_sessions": 5,
        "locked_accounts": 1,
        "pending_reset_requests": 2
    }
    
    # 仮のアクティビティデータ
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
    
    # 仮のログイン試行データ
    recent_login_attempts = [
        {
            "timestamp": datetime.now(),
            "user_id": 1,
            "username": "admin",
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "success": True,
            "failure_reason": None
        },
        {
            "timestamp": datetime.now(),
            "user_id": 2,
            "username": "user1",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "success": False,
            "failure_reason": "パスフレーズが正しくありません。"
        }
    ]
    
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "stats": stats,
        "recent_activities": recent_activities,
        "recent_login_attempts": recent_login_attempts
    })

# ユーザー管理ページ（管理者認証必須）
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    # TODO: 管理者認証チェック
    # 仮のユーザーデータ
    users = [
        {
            "id": 1,
            "username": "admin",
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "is_active": True,
            "is_admin": True,
            "locked_until": None,
            "permanent_lock": False
        },
        {
            "id": 2,
            "username": "user1",
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "is_active": True,
            "is_admin": False,
            "locked_until": None,
            "permanent_lock": False
        },
        {
            "id": 3,
            "username": "user2",
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "is_active": True,
            "is_admin": False,
            "locked_until": datetime.now(),
            "permanent_lock": False
        }
    ]
    
    # 仮のページネーションデータ
    pagination = {
        "current_page": 1,
        "total_pages": 1,
        "pages": [1]
    }
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "users": users,
        "pagination": pagination,
        "search_query": "",
        "status_filter": "all",
        "now": datetime.now()
    })

# システムログページ（管理者認証必須）
@app.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs_page(request: Request):
    # TODO: 管理者認証チェック
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
async def admin_settings_page(request: Request):
    # TODO: 管理者認証チェック
    # 仮の設定データ
    settings = {
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
        "settings": settings
    })

# リセット依頼管理ページ（管理者認証必須）
@app.get("/admin/reset-requests", response_class=HTMLResponse)
async def admin_reset_requests_page(request: Request):
    # TODO: 管理者認証チェック
    # 仮のリセット依頼データ
    reset_requests = [
        {
            "id": 1,
            "user_id": 2,
            "username": "user1",
            "request_reason": "パスフレーズを忘れました",
            "timestamp": datetime.now() - timedelta(days=1),
            "status": "pending",
            "resolved_by": None,
            "resolver_username": None,
            "resolved_at": None
        },
        {
            "id": 2,
            "user_id": 3,
            "username": "user2",
            "request_reason": "アカウントがロックされました",
            "timestamp": datetime.now() - timedelta(days=2),
            "status": "approved",
            "resolved_by": 1,
            "resolver_username": "admin",
            "resolved_at": datetime.now() - timedelta(days=1)
        },
        {
            "id": 3,
            "user_id": 4,
            "username": "user3",
            "request_reason": "セキュリティ上の理由でリセットしたい",
            "timestamp": datetime.now() - timedelta(days=3),
            "status": "rejected",
            "resolved_by": 1,
            "resolver_username": "admin",
            "resolved_at": datetime.now() - timedelta(days=2)
        }
    ]

    return templates.TemplateResponse("admin/reset_requests.html", {
        "request": request,
        "reset_requests": reset_requests
    })

# ログアウト処理
@app.get("/logout")
async def logout(request: Request, response: Response):
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

