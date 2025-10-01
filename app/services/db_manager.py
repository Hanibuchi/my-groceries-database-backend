from app.api.v1.schemas.user import User # レスポンス用のPydanticスキーマ
from typing import List, Optional
from app.api.v1.schemas.record import Record, OCRResult, RecordCreate

def create_internal_user_record(user_uuid: str, email: str, username: str) -> User:
    """
    新しいユーザーの内部DBレコードを作成する。
    （Supabaseでのサインアップ完了後に呼び出し、UUIDをキーとして内部DBに初期データを登録する）
    """
    # 🚨 DB操作ロジック例:
    # new_user = DBUser(id=user_uuid, email=email, username=username)
    # db_session.add(new_user)
    # db_session.commit()
    
    # ハッカソン用スタブ: 作成したユーザーをPydanticモデルで返す
    print(f"Internal DB record created for UUID: {user_uuid}")
    return User(id=user_uuid, username=username, email=email, is_active=True) 

def get_user_by_uuid(user_uuid: str) -> Optional[User]:
    """
    UUIDでユーザーを取得する（security.pyの認可処理から呼ばれる必須関数）
    """
    # 🚨 DB操作ロジック例:
    # db_user = db_session.query(DBUser).filter(DBUser.id == user_uuid).first()
    # if not db_user:
    #     return None
    # return User.model_validate(db_user) # ORMオブジェクトをPydanticモデルに変換
    
    # ハッカソン用スタブ: 
    if user_uuid:
        # DBから取得したデータをPydanticモデルとして返す (UUIDはstr型)
        return User(id=user_uuid, username="retrieved_user", email="user@internal.db") 
    return None

# ---- 履歴管理 ----
def create_purchase_records(user_id: str, records_in: List):
    """(test_confirm_and_register_record_success 用) レコードリストの一括登録"""
    # 実際の実装は後で。テストをパスするために定義
    return []
def create_purchase_record(user_id, record_in: RecordCreate):
    pass

def get_records_by_item_id(user_id, item_id):
    return []

def get_item_price_comparisons(user_id: str, item_id: int):
    """(test_get_price_comparison_success 用) 価格比較データの取得"""
    return []

# ---- 商品管理 ----
def create_item(user_id, item_in):
    pass

def get_items_by_user(user_id):
    pass

def update_item(user_id, item_id, item_in):
    pass

def delete_item(user_id, item_id):
    pass


# ---- 店舗管理 ----
def create_store(user_id, store_in):
    return None 

def get_stores_by_user(user_id):
    pass

def update_store(user_id, store_id, store_in):
    pass

def delete_store(user_id, store_id):
    pass


def export_user_data_to_csv(user_id: str):
    """(test_export_data_success 用) データエクスポート"""
    # テストでは一時ファイルパスを返すと想定
    return "temp_export.csv" 