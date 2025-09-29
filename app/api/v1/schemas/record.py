# record.py
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional

# 共通ベーススキーマ
class RecordBase(BaseModel):
    """購入履歴の基本的な情報"""
    # OCRから読み取った店舗名（正規化前）
    raw_store_name: str = Field(..., max_length=100) 
    # OCRから読み取った商品名（正規化前）
    raw_item_name: str = Field(..., max_length=255) 
    price: float = Field(..., gt=0)
    purchase_date: date = Field(default_factory=date.today)
    
    # 以下のIDは正規化処理後に紐づけられる（DB保存時）
    item_id: Optional[int] = None 
    store_id: Optional[int] = None
    
# OCR処理後のデータ確認・修正用（リクエスト/レスポンス）
class OCRResult(BaseModel):
    """OCR処理および正規化後のデータと、ユーザーによる修正可能性を持たせた構造"""
    # 履歴本体
    record: RecordBase
    # 名寄せ候補や確認情報
    is_new_item: bool = True # 商品名が新規登録の必要があるか
    suggested_item_id: Optional[int] = None # 名寄せされた既存のitem_id
    suggested_item_name: Optional[str] = None # 名寄せされた既存のitem_name (表示用)
    
    is_new_store: bool = True # 店舗名が新規登録の必要があるか
    suggested_store_id: Optional[int] = None
    suggested_store_name: Optional[str] = None

# 購入履歴登録（リクエスト）：クライアント側からは画像のみ、またはOCR確認後のデータが送られる
# 画像アップロードは直接ファイルを受け取るため、このスキーマは主にOCR確認後のデータ登録に使用
class RecordCreate(OCRResult):
    """ユーザーがOCR結果を確認・修正した後の最終的な登録データ"""
    pass

# 購入履歴（レスポンス）
class Record(RecordBase):
    """データベースから取得した購入履歴"""
    id: int
    user_id: int
    
    # 正規化後の名称を紐付けて返す
    normalized_item_name: Optional[str] = None
    normalized_store_name: Optional[str] = None

    class Config:
        from_attributes = True

# 価格比較機能（レスポンス）
class PriceComparison(BaseModel):
    """特定の商品に関する店舗ごとの価格情報"""
    normalized_item_name: str
    store_name: str
    latest_price: float
    average_price: float
    # その店舗での過去の購入回数
    purchase_count: int
    # 比較用: 全店舗での平均価格
    overall_average_price: float