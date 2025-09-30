
# ユーザー管理
def create_new_user(user_in):
    """新しいユーザーを作成する"""

# ユーザー認証
def create_access_token(data: dict) -> str:
    """JWTトークンを生成する"""
    return "access_token"

def get_user_by_uuid(user_uuid: str):
    """UUIDでユーザーを取得する"""
    pass


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