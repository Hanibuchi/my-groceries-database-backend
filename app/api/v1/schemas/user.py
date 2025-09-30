# user.py
from pydantic import BaseModel, Field

# 共通ベーススキーマ
class UserBase(BaseModel):
    """ユーザーの基本的な情報"""
    username: str = Field(..., max_length=50)
    email: str = Field(..., max_length=100)

# ユーザー登録（リクエスト）
class UserCreate(UserBase):
    """新規ユーザー登録時のリクエストボディ"""
    password: str = Field(..., min_length=8)

# ユーザー情報（レスポンス）
class User(UserBase):
    """データベースから取得したユーザー情報 (パスワードなどは含まない)"""
    id: str 
    is_active: bool = True

    class Config:
        from_attributes = True

# 認証トークン（レスポンス）
class Token(BaseModel):
    """JWTトークン情報"""
    access_token: str
    token_type: str = "bearer"

# パスワード変更（リクエスト）
class PasswordChange(BaseModel):
    """パスワード変更時のリクエストボディ"""
    current_password: str
    new_password: str = Field(..., min_length=8)