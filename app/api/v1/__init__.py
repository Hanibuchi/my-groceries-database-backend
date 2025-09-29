from fastapi import APIRouter
from .endpoints import auth, users, receipts, items # 各エンドポイントファイルからルーターをインポート

# v1のメインルーターを定義
api_router = APIRouter()

# 各ルーターをインクルード
# prefixやtagsは各ファイル内で設定済みでも良いが、ここで統合することも可能
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(receipts.router, tags=["receipts"])
api_router.include_router(items.router, tags=["items"])