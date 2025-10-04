from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User
from app.core.security import (
    get_current_active_user,
)  # 依存性注入で認証済みユーザーを取得

router = APIRouter(prefix="/users", tags=["Users"])


# 認証済みユーザーの情報を取得
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """現在ログインしているユーザーの情報を取得する"""
    return current_user


# 🚨 パスワード変更エンドポイントの削除 🚨
# フロントエンド側からSupabaseの update_user または reset_password APIを直接叩いてください。
# @router.post("/me/password", response_model=dict)
# async def change_password(...): ... (削除)
