from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import os

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
# from app.api import auth, users, admin
# app.include_router(auth.router)
# app.include_router(users.router)
# app.include_router(admin.router)

# メインページ
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}

# アプリケーションの実行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.LISTEN_IP,
        port=settings.LISTEN_PORT,
        reload=settings.DEBUG
    )

