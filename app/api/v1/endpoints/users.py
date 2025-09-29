# users.py
from fastapi import APIRouter, Depends
from typing import List

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User, PasswordChange
from app.core.security import get_current_active_user # 依存性注入で認証済みユーザーを取得

router = APIRouter(prefix="/users", tags=["Users"])

# 認証済みユーザーの情報を取得
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """現在ログインしているユーザーの情報を取得する"""
    return current_user

# ユーザー名変更（ここでは省略。必要に応じてdb_managerを介して実装）

# パスワード変更
@router.post("/me/password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """現在のユーザーのパスワードを変更する"""
    # パスワード変更ロジック (securityとdb_managerを使用)
    success = security.change_user_password(
        current_user.id, 
        password_data.current_password, 
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )
        
    return {"message": "Password updated successfully"}

# データ初期化機能
@router.delete("/me/data", response_model=dict)
async def initialize_user_data(current_user: User = Depends(get_current_active_user)):
    """ユーザーのすべての購入履歴、店舗、商品を削除する"""
    # db_manager.initialize_data(current_user.id)
    # 実際は確認ダイアログなどをフロントで入れるべき
    return {"message": "All purchase history, items, and stores have been deleted."}