# record.py
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
    
# OCR処理後のデータ確認・修正用（リクエスト/レスポンス）
class OCRResult(BaseModel):
    """
    OCR処理で抽出された生データと、それを基にした正規化の提案を保持するスキーマ。
    ユーザーに確認・修正させるフェーズで使用する。
    """
    # 1. OCRで読み取った生データ (必須)
    raw_item_name: str = Field(..., max_length=255)  # OCRから読み取った商品名（正規化前）
    raw_store_name: str = Field(..., max_length=100)  # OCRから読み取った店舗名（正規化前）
    raw_price: float = Field(..., gt=0)              # OCRから読み取った価格
    raw_purchase_date: date = Field(default_factory=date.today) # OCRから読み取った日付

    # 2. 名寄せ候補や確認情報 (正規化の提案)
    is_new_item: bool = True # 商品名が新規登録の必要があるか
    suggested_item_id: Optional[int] = None # 名寄せされた既存のitem_id（あれば）
    suggested_item_name: Optional[str] = Field(..., max_length=255) # item_name (表示用)
    
    is_new_store: bool = True # 店舗名が新規登録の必要があるか
    suggested_store_id: Optional[int] = None # 名寄せされた既存のstore_id（あれば）
    suggested_store_name: Optional[str] = Field(..., max_length=255)


# 購入履歴登録（リクエスト）：クライアント側からの最終登録データ
class RecordCreate(BaseModel):
    """
    ユーザーがOCR結果を確認・修正した後の最終的な登録データ。
    DB保存のために必要な情報を全て持つ。
    """
    raw_item_name: str = Field(..., max_length=255)  # OCRから読み取った商品名（正規化前）
    raw_store_name: str = Field(..., max_length=255)  # OCRから読み取った店舗名（正規化前）
    raw_price: float = Field(..., gt=0)              # OCRから読み取った価格
    raw_purchase_date: date = Field(default_factory=date.today) # OCRから読み取った日付
    
    # 確定した正規化ID
    item_id: int 
    store_id: int
    
    # 最終的な購入データ
    final_price: float = Field(..., gt=0)
    final_purchase_date: date = Field(default_factory=date.today)
    
# 購入履歴（レスポンス）
class Record(BaseModel):
    """データベースから取得した購入履歴"""
    
    price: float = Field(..., gt=0)
    purchase_date: date = Field(default_factory=date.today)
    
    # 以下のIDは正規化処理後に紐づけられる（DB保存時）
    item_id: Optional[int] = None # 正規化された商品ID
    store_id: Optional[int] = None # 正規化された店舗ID
    
    # 正規化後の名称を紐付けて返す
    item_name: Optional[str] = Field(..., max_length=255)
    store_name: Optional[str] = Field(..., max_length=255)

    id: int
    user_id: str

    class Config:
        from_attributes = True

# 価格比較機能（レスポンス）
class PriceComparison(BaseModel):
    """特定の商品に関する店舗ごとの価格情報"""
    item_name: str = Field(..., max_length=255)
    store_name: str = Field(..., max_length=255)
    
    item_id: Optional[int] = None # 正規化された商品ID
    store_id: Optional[int] = None # 正規化された店舗ID
    
    average_price: float
    # 比較用: 全店舗での平均価格
    overall_average_price: float