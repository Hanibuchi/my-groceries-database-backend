from typing import List, Optional
from app.api.v1.schemas.user import User
from app.api.v1.schemas.item import Item, ItemCreate
from app.api.v1.schemas.store import Store, StoreCreate
from app.api.v1.schemas.record import Record, RecordCreate, PriceComparison

# データベース操作の専門家であるdatabaseモジュールをインポート
from app.db import database


# --- 1. ユーザー (User) 関連 ---

# create_user_internalは現在の設計では不要なため、実装しない
# def create_user_internal(...):
#     pass

def get_user_by_uuid(user_uuid: str) -> Optional[User]:
    """UUIDでユーザーを取得する"""
    # 専門家(database)に、ユーザー取得の仕事を依頼する
    return database.get_user_by_uuid(user_uuid=user_uuid)


def delete_all_user_data(user_uuid: str) -> bool:
    """ユーザーの全データを削除する"""
    return database.delete_all_user_data(user_uuid=user_uuid)


# --- 2. 商品 (Item) 関連 ---

def create_item(user_id: str, item_in: ItemCreate) -> Item:
    """商品を新規登録する"""
    return database.create_item(user_id=user_id, item_in=item_in)


def get_items_by_user(user_id: str) -> List[Item]:
    """特定ユーザーの全商品リストを取得する"""
    return database.get_items_by_user(user_id=user_id)


def update_item(user_id: str, item_id: int, item_in: ItemCreate) -> Optional[Item]:
    """商品情報を更新する"""
    return database.update_item(user_id=user_id, item_id=item_id, item_in=item_in)


def delete_item(user_id: str, item_id: int) -> bool:
    """商品を削除する"""
    return database.delete_item(user_id=user_id, item_id=item_id)


# --- 3. 店舗 (Store) 関連 ---

def create_store(user_id: str, store_in: StoreCreate) -> Store:
    """店舗を新規登録する"""
    return database.create_store(user_id=user_id, store_in=store_in)


def get_stores_by_user(user_id: str) -> List[Store]:
    """特定ユーザーの全店舗リストを取得する"""
    return database.get_stores_by_user(user_id=user_id)


def update_store(user_id: str, store_id: int, store_in: StoreCreate) -> Optional[Store]:
    """店舗情報を更新する"""
    return database.update_store(user_id=user_id, store_id=store_id, store_in=store_in)


def delete_store(user_id: str, store_id: int) -> bool:
    """店舗を削除する"""
    return database.delete_store(user_id=user_id, store_id=store_id)


# --- 4. 購入履歴 (Record) 関連 ---

def create_purchase_record(user_id: str, record_in: RecordCreate) -> Record:
    """購入履歴を登録する"""
    return database.create_purchase_record(user_id=user_id, record_in=record_in)


def get_records_by_item_id(user_id: str, item_id: int) -> List[Record]:
    """特定商品IDに紐づく購入履歴を全て取得する"""
    return database.get_records_by_item_id(user_id=user_id, item_id=item_id)


def update_record(user_id: str, record_id: int, record_in: RecordCreate) -> Optional[Record]:
    """購入履歴を更新する"""
    return database.update_record(user_id=user_id, record_id=record_id, record_in=record_in)


def delete_record(user_id: str, record_id: int) -> bool:
    """購入履歴を削除する"""
    return database.delete_record(user_id=user_id, record_id=record_id)


# --- 5. 特別集計・その他 ---

def get_item_price_comparisons(user_id: str, item_id: int) -> List[PriceComparison]:
    """特定商品の店舗ごとの価格比較データを取得する"""
    # 専門家(database)に、RPCを使った特別な調査を依頼する
    return database.get_item_store_price_averages(user_id=user_id, item_id=item_id)
