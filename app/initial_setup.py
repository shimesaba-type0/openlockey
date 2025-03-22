#!/usr/bin/env python3
import asyncio
import os
import sys
import getpass
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal
from app.models.models import User, BackupSettings
from app.core.security import get_password_hash, generate_password

# 禁止ユーザー名リストの読み込み
def load_restricted_usernames():
    """禁止ユーザー名リストを読み込む"""
    restricted_file = os.path.join("config", "restricted_usernames.txt")
    if not os.path.exists(restricted_file):
        print(f"警告: 禁止ユーザー名リストファイル '{restricted_file}' が見つかりません。")
        return ["admin", "administrator", "root", "superuser"]
    
    with open(restricted_file, "r") as f:
        return [line.strip().lower() for line in f if line.strip()]

async def create_admin_user(db: AsyncSession, username: str = None, password: str = None):
    """管理者ユーザーを作成する"""
    restricted_usernames = load_restricted_usernames()
    
    # ユーザー名の入力を促す
    while not username:
        username = input("管理者ユーザー名を入力してください: ").strip()
        
        # 禁止ユーザー名チェック
        if username.lower() in restricted_usernames:
            print(f"セキュリティ上の理由から、'{username}' は管理者ユーザー名として使用できません。")
            username = None
            continue
    
    # ユーザーが既に存在するか確認
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if user:
        print(f"ユーザー '{username}' は既に存在します。")
        return user
    
    # パスワードの入力または生成
    if not password:
        use_generated = input("自動生成されたパスフレーズを使用しますか？ (y/n): ").strip().lower()
        if use_generated == 'y':
            password = generate_password(64)
            print(f"生成されたパスフレーズ: {password}")
            print("このパスフレーズを安全な場所に保存してください。")
        else:
            while True:
                password = getpass.getpass("パスフレーズを入力してください (32文字以上): ")
                if len(password) < 32:
                    print("パスフレーズは32文字以上である必要があります。")
                    continue
                
                confirm = getpass.getpass("パスフレーズを再入力してください: ")
                if password != confirm:
                    print("パスフレーズが一致しません。もう一度お試しください。")
                    continue
                
                break
    
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

async def reset_database():
    """データベースをリセットする（開発環境のみ）"""
    from app.core.database import engine, Base
    
    confirm = input("警告: これによりすべてのデータが削除されます。続行しますか？ (yes/no): ")
    if confirm.lower() != "yes":
        print("データベースのリセットをキャンセルしました。")
        return False
    
    print("データベースをリセットしています...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print("データベースのリセットが完了しました。")
    return True

async def main():
    """初期セットアップを実行する"""
    # コマンドライン引数の処理
    reset = False
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset = True
    
    if reset:
        reset_success = await reset_database()
        if not reset_success:
            return
    
    db = SessionLocal()
    try:
        # 管理者ユーザーの作成
        admin_user = await create_admin_user(db)
        
        # バックアップ設定の作成
        backup_settings = await create_backup_settings(db)
        
        print("初期セットアップが完了しました。")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())

