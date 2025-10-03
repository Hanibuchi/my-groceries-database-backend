from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 各エンドポイントのルーターをインポート
from app.api.v1.endpoints import stores, receipts, users, items

app = FastAPI()

# CORS設定
origins = [
    "https://my-groceries-database.vercel.app",  # フロントエンドのURL
    "http://localhost:3000",                     # ローカルでのフロントエンド開発用
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 各エンドポイントのルーターをアプリに接続します
app.include_router(stores.router, prefix="/api/v1", tags=["stores"])
app.include_router(receipts.router, prefix="/api/v1", tags=["receipts"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(items.router, prefix="/api/v1", tags=["items"])


# 動作確認用のAPI
@app.get("/")
def read_root():
    return {"message": "Welcome to ReciLog API!"}