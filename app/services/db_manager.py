from app.api.v1.schemas.user import User # レスポンス用のPydanticスキーマ
from typing import Optional

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
def get_records_by_item_id(user_id, item_id):
    pass


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
    pass

def get_stores_by_user(user_id):
    pass

def update_store(user_id, store_id, store_in):
    pass

def delete_store(user_id, store_id):
    pass