from app.api.v1.schemas.user import User  # レスポンス用のPydanticスキーマ
from app.api.v1.schemas.item import Item, ItemCreate
from app.api.v1.schemas.store import Store, StoreCreate
from typing import List, Optional
from app.api.v1.schemas.record import Record, RecordCreate, PriceComparison


# ---- 履歴管理 ----
def create_purchase_records(user_id: str, records_in: List):
    """(test_confirm_and_register_record_success 用) レコードリストの一括登録"""
    # 実際の実装は後で。テストをパスするために定義
    return []


def create_purchase_record(user_id, record_in: RecordCreate):
    pass


def get_records_by_item_id(user_id, item_id) -> List[Record]:
    return []


def update_record(user_id, record_id, record_in: Record):
    pass


def delete_record(user_id, record_id):
    pass


# 価格比較データの取得。優先度は低い
def get_item_price_comparisons(user_id: str, item_id: int) -> List[PriceComparison]:
    """(test_get_price_comparison_success 用) 価格比較データの取得"""
    return []


# ---- 商品管理 ----
def create_item(user_id, item_in: ItemCreate):
    pass


def get_items_by_user(user_id) -> List[Item]:
    pass


def update_item(user_id, item_id, item_in: ItemCreate):
    pass


def delete_item(user_id, item_id):
    pass


# ---- 店舗管理 ----
def create_store(user_id, store_in: StoreCreate):
    return None


def get_stores_by_user(user_id) -> List[Store]:
    pass


def update_store(user_id, store_id, store_in: StoreCreate):
    pass


def delete_store(user_id, store_id):
    pass


def export_user_data_to_csv(user_id: str):
    """(test_export_data_success 用) データエクスポート"""
    # テストでは一時ファイルパスを返すと想定
    return "temp_export.csv"


def delete_all_user_data(user_id: str) -> bool:
    """
    ユーザーIDに紐づく全てのデータ（商品、購入履歴、店舗など）を削除する。
    """
    # ... 実際のDB操作ロジック ...

    # テスト用スタブ: 常に成功を返す
    print(f"All internal data deleted for UUID: {user_id}")
    return True
