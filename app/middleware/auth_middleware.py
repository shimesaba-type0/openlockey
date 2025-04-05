from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal
from app.core.auth import get_current_user_from_session

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # リクエストごとに新しいDBセッションを作成
        db = SessionLocal()
        try:
            # DBセッションをリクエストのstateに保存
            request.state.db = db
            
            # ユーザー認証情報を取得
            user = await get_current_user_from_session(request, db)
            
            # リクエストのstateにユーザー情報を保存
            request.state.user = user
            request.state.is_authenticated = user is not None
            
            # 次のミドルウェアまたはエンドポイントを呼び出す
            response = await call_next(request)
            return response
        finally:
            await db.close()

