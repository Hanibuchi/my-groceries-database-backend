# app/main.py

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# 自身のプロジェクトからインポート
from app.api.v1.api import api_router # v1/api.py でルーターを統合することを想定
from app.core.config import settings

# --- FastAPI アプリケーションのインスタンス化 ---
# タイトルやバージョン情報は settings.py から取得
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version=settings.VERSION,
)

# --- 1. CORS (Cross-Origin Resource Sharing) の設定 ---
# Next.js のフロントエンドからのアクセスを許可するために必須
if settings.BACKEND_CORS_ORIGINS:
    # カンマ区切りの文字列をリストに変換
    origins = [str(origin).strip() for origin in settings.BACKEND_CORS_ORIGINS.split(',')]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins, # 許可するオリジン (例: ["http://localhost:3000"])
        allow_credentials=True,
        allow_methods=["*"],    # 全てのHTTPメソッドを許可
        allow_headers=["*"],    # 全てのヘッダーを許可
    )

# --- 2. ルーターのインクルード ---
# v1 バージョンのAPIルーターを /v1 のパスにマウント
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- 3. ヘルスチェックルート (任意) ---
@app.get("/")
async def root():
    """アプリケーションが正常に動作しているかを確認するためのルート"""
    return {"message": "Welcome to My Groceries Database API", "version": settings.VERSION}


# --- 4. 開発環境での実行設定 (オプション) ---
# この部分は通常、DockerやGunicornで実行するため必須ではないが、単体実行用に含める
if __name__ == "__main__":
    # 環境変数から設定を読み込み
    port = settings.UVICORN_PORT
    host = settings.UVICORN_HOST

    print(f"Starting uvicorn server on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True) # reload=True は開発時のみ推奨