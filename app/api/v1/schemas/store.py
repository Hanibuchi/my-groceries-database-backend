# store.py
from pydantic import BaseModel, Field
from typing import Optional

# 共通ベーススキーマ
class StoreBase(BaseModel):
    """店舗の基本的な情報"""
    name: str = Field(..., max_length=100)

# 店舗登録（リクエスト）
class StoreCreate(StoreBase):
    """新規店舗登録時のリクエストボディ"""
    pass

# 店舗情報（レスポンス）
class Store(StoreBase):
    """データベースから取得した店舗情報"""
    id: int
    user_id: int  # どのユーザーが登録した店舗か

    class Config:
        from_attributes = True