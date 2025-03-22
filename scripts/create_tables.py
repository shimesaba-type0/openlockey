#!/usr/bin/env python3
import asyncio
import os
import sys

# プロジェクトのルートディレクトリをPYTHONPATHに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine, Base
from app.models.models import User, Session, LoginHistory, ResetRequest, BackupSettings

async def create_tables():
    """データベーステーブルを作成する"""
    print("データベーステーブルを作成しています...")
    async with engine.begin() as conn:
        # テーブルが存在する場合は削除（開発環境のみ）
        # await conn.run_sync(Base.metadata.drop_all)
        # テーブルを作成
        await conn.run_sync(Base.metadata.create_all)
    print("データベーステーブルの作成が完了しました。")

if __name__ == "__main__":
    asyncio.run(create_tables())

