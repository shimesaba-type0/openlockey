from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
from datetime import datetime

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

# ログアウト処理
@app.get("/logout")
async def logout():
    # TODO: セッション削除処理
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

