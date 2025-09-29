# app/api/v1/api.py

from fastapi import APIRouter

# 各エンドポイントファイルからルーターをインポート
# endpoints ディレクトリの構造に応じてインポートパスを調整
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import users
from app.api.v1.endpoints import receipts
from app.api.v1.endpoints import stores
from app.api.v1.endpoints import items

# APIバージョン1のメインルーターを定義
api_router = APIRouter()

# 各機能のルーターをメインルーターに含める
# ここで設定した prefix は、endpoints/ の各ファイルで設定した prefix に先行して適用される
api_router.include_router(auth.router)      # 例: /v1/auth/token
api_router.include_router(users.router)     # 例: /v1/users/me
api_router.include_router(receipts.router)  # 例: /v1/receipts/upload
api_router.include_router(stores.router)    # 例: /v1/stores/
api_router.include_router(items.router)     # 例: /v1/items/