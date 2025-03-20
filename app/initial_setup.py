import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal
from app.models.models import User, BackupSettings
from app.core.security import get_password_hash, generate_password

async def create_admin_user(db: AsyncSession, username: str, password: str = None):
    """管理者ユーザーを作成する"""
    # ユーザーが既に存在するか確認
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if user:
        print(f"ユーザー '{username}' は既に存在します。")
        return user
    
    # パスワードが指定されていない場合は生成
    if not password:
        password = generate_password(64)
        print(f"生成されたパスフレーズ: {password}")
    
    # 新しい管理者ユーザーを作成
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        is_admin=True,
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    print(f"管理者ユーザー '{username}' を作成しました。")
    return user

async def create_backup_settings(db: AsyncSession):
    """バックアップ設定を作成する"""
    from sqlalchemy import select
    result = await db.execute(select(BackupSettings))
    settings = result.scalars().first()
    
    if settings:
        print("バックアップ設定は既に存在します。")
        return settings
    
    settings = BackupSettings(
        enabled=True,
        frequency="daily",
        retention_days=30
    )
    
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    
    print("バックアップ設定を作成しました。")
    return settings

async def main():
    """初期セットアップを実行する"""
    db = SessionLocal()
    try:
        # 管理者ユーザーの作成
        admin_username = "admin"
        admin_user = await create_admin_user(db, admin_username)
        
        # バックアップ設定の作成
        backup_settings = await create_backup_settings(db)
        
        print("初期セットアップが完了しました。")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())

