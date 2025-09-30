from fastapi import APIRouter
from .endpoints import auth, users, receipts, stores, items # 各エンドポイントファイルからルーターをインポート

# v1のメインルーターを定義
api_router = APIRouter()

# 各ルーターをインクルード
# prefixやtagsは各ファイル内で設定済みでも良いが、ここで統合することも可能
# api_router.include_router(auth.router)      # 例: /v1/auth/token
api_router.include_router(users.router)     # 例: /v1/users/me
api_router.include_router(receipts.router)  # 例: /v1/receipts/upload
api_router.include_router(stores.router)    # 例: /v1/stores/
api_router.include_router(items.router)     # 例: /v1/items/