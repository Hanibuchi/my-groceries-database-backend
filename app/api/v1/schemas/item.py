# item.py
from pydantic import BaseModel, Field
from typing import Optional

# 共通ベーススキーマ
class ItemBase(BaseModel):
    """商品の基本的な情報"""
    # 正規化後の商品名。OCRデータ正規化後の名寄せ処理の鍵となる
    normalized_name: str = Field(..., max_length=255)
    # 商品カテゴリなど、より詳細な情報も追加可能

# 商品登録（リクエスト）
class ItemCreate(ItemBase):
    """新規商品登録時のリクエストボディ"""
    pass

# 商品情報（レスポンス）
class Item(ItemBase):
    """データベースから取得した商品情報"""
    id: int
    user_id: int # どのユーザーのデータベースに属するか

    class Config:
        from_attributes = True