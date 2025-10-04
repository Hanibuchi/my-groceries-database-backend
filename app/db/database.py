from typing import List, Optional, Any, Dict
from supabase import create_client, Client
from postgrest import APIResponse
import json
from datetime import date

from app.core.config import settings

# Pydanticスキーマのインポート
from app.api.v1.schemas.user import User
from app.api.v1.schemas.item import Item, ItemCreate
from app.api.v1.schemas.store import Store, StoreCreate
from app.api.v1.schemas.record import Record, RecordCreate, PriceComparison

from app.db import database # 専門職人(database.py)をインポート

# Supabaseクライアントを初期化
# settingsオブジェクトから安全にURLとキーを読み込みます
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# --- 1. ユーザー (User) 関連 ---


def create_user_internal(user_uuid: str, email: str, username: str) -> Optional[User]:
    """
    Supabaseで認証された後のユーザーの内部DBレコード(public.users)を初期登録する。
    """
    try:
        response: APIResponse = supabase.table('users').insert({
            "id": user_uuid,  # Supabase AuthのUUIDを主キーとして使用
            "email": email,
            "username": username
        }).execute()

        # 登録が成功したら、作成されたユーザー情報を返す
        if response.data:
            # response.dataはリストで返ってくるので、最初の要素を取り出す
            return User(**response.data[0])
        return None
    except Exception as e:
        print(f"Error creating internal user record: {e}")
        return None

def create_internal_user_record(user_uuid: str, email: str, username: str) -> Optional[User]:
    """新しいユーザーの内部DBレコードを作成する。"""
    # 専門職人(database)に、ユーザー作成の仕事を依頼する
    return database.create_user_internal(
        user_uuid=user_uuid, 
        email=email, 
        username=username
    )



def get_user_by_uuid(user_uuid: str) -> Optional[User]:
    """
    UUIDに基づき、管理者権限でauth.usersテーブルから直接ユーザーレコードを取得する。
    """
    try:
        # admin を呼び出して、auth のユーザー情報を取得
        response = supabase.auth.admin.get_user_by_id(user_uuid)
        user_data = response.user

        if user_data:
            # user_metadataからusernameを取得。なければemailをフォールバックとして使用。
            username = user_data.user_metadata.get("username", user_data.email)

            # 取得した情報を、アプリ内で使うUserモデルの形に変換して返す
            return User(id=str(user_data.id), is_active=True)  # 必須項目is_activeを追加
        return None
    except Exception as e:
        # ユーザーが見つからない場合などにエラーが発生
        print(f"Error fetching user from Supabase auth: {e}")
        return None


def delete_all_user_data(user_uuid: str) -> bool:
    """
    ユーザーに紐づく全てのデータと、auth.usersのユーザー本体を削除する。
    """
    try:
        # 関連するpublicスキーマのデータを全て削除する
        supabase.table("purchases").delete().eq("user_id", user_uuid).execute()
        supabase.table("items").delete().eq("user_id", user_uuid).execute()
        supabase.table("stores").delete().eq("user_id", user_uuid).execute()

        # 2. admin を呼び出して auth からユーザー本体を削除する
        supabase.auth.admin.delete_user(user_uuid)

        return True
    except Exception as e:
        print(f"Error deleting all user data: {e}")
        return False


# --- 2. 商品 (Item) 関連 ---


def create_item(user_id: str, item_in: ItemCreate) -> Item:
    """
    商品を新規登録する。
    """
    response: APIResponse = (
        supabase.table("items")
        .insert({"user_id": user_id, "name": item_in.name})
        .execute()
    )

    if response.data:
        return Item(**response.data[0])
    raise Exception("Could not create item")


def get_item_by_name_and_user(user_id: str, name: str) -> Optional[Item]:
    """
    特定ユーザーのデータベースから商品名をキーに商品を取得する（名寄せに使用）。
    """
    response: Optional[APIResponse] = (
        supabase.table("items")
        .select("*")
        .eq("user_id", user_id)
        .eq("name", name)
        .maybe_single()
        .execute()
    )

    # 修正: response が None の場合（レコードが見つからなかった場合）は None を返す。
    if response is None:
        return None

    # 修正: response が APIResponse の場合、data があれば Item オブジェクトに変換して返す。
    if response.data:
        return Item.model_validate(response.data)

    return None


def get_items_by_user(user_id: str) -> List[Item]:
    """
    特定ユーザーの全商品リストを取得する。
    """
    response: APIResponse = (
        supabase.table("items").select("*").eq("user_id", user_id).execute()
    )

    if response.data:
        return [Item(**item) for item in response.data]
    return []


def get_item_by_id(user_id: str, item_id: int) -> Optional[Item]:
    """
    商品IDに基づき商品を取得する。
    """
    response: APIResponse = (
        supabase.table("items")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", item_id)
        .single()
        .execute()
    )

    if response.data:
        return Item(**response.data)
    return None


def update_item(user_id: str, item_id: int, item_in: ItemCreate) -> Optional[Item]:
    """
    商品情報を更新する。
    """
    response: APIResponse = (
        supabase.table("items")
        .update({"name": item_in.name})
        .eq("user_id", user_id)
        .eq("id", item_id)
        .execute()
    )

    if response.data:
        return Item(**response.data[0])
    return None


def delete_item(user_id: str, item_id: int) -> bool:
    """
    商品を削除する。
    """
    response: APIResponse = (
        supabase.table("items")
        .delete()
        .eq("user_id", user_id)
        .eq("id", item_id)
        .execute()
    )
    return bool(response.data)


def search_items_by_partial_name(user_id: str, query: str) -> List[Item]:
    """
    商品名の一部が一致する商品を検索する（LIKE検索などを利用）。
    """
    response: APIResponse = (
        supabase.table("items")
        .select("*")
        .eq("user_id", user_id)
        .ilike("name", f"%{query}%")
        .execute()
    )

    if response.data:
        return [Item(**item) for item in response.data]
    return []


# --- 3. 店舗 (Store) 関連 ---


def create_store(user_id: str, store_in: StoreCreate) -> Store:
    """
    店舗を新規登録する。
    """
    response: APIResponse = (
        supabase.table("stores")
        .insert({"user_id": user_id, "name": store_in.name})
        .execute()
    )

    if response.data:
        return Store(**response.data[0])
    raise Exception("Could not create store")


def get_store_by_name_and_user(user_id: str, name: str) -> Optional[Store]:
    """
    特定ユーザーのデータベースから店舗名をキーに店舗を取得する（名寄せに使用）。
    """
    response: APIResponse = (
        supabase.table("stores")
        .select("*")
        .eq("user_id", user_id)
        .eq("name", name)
        .maybe_single()
        .execute()
    )

    if response.data:
        return Store(**response.data)
    return None


def get_stores_by_user(user_id: str) -> List[Store]:
    """
    特定ユーザーの全店舗リストを取得する。
    """
    response: APIResponse = (
        supabase.table("stores").select("*").eq("user_id", user_id).execute()
    )

    if response.data:
        return [Store(**store) for store in response.data]
    return []


def get_store_by_id(user_id: str, store_id: int) -> Optional[Store]:
    """
    店舗IDに基づき店舗を取得する。
    """
    response: APIResponse = (
        supabase.table("stores")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", store_id)
        .single()
        .execute()
    )

    if response.data:
        return Store(**response.data)
    return None


def update_store(user_id: str, store_id: int, store_in: StoreCreate) -> Optional[Store]:
    """
    店舗情報を更新する。
    """
    response: APIResponse = (
        supabase.table("stores")
        .update({"name": store_in.name})
        .eq("user_id", user_id)
        .eq("id", store_id)
        .execute()
    )

    if response.data:
        return Store(**response.data[0])
    return None


def delete_store(user_id: str, store_id: int) -> bool:
    """
    店舗を削除する。
    """
    response: APIResponse = (
        supabase.table("stores")
        .delete()
        .eq("user_id", user_id)
        .eq("id", store_id)
        .execute()
    )
    return bool(response.data)


# --- 4. 購入履歴 (Record) 関連 ---


def create_purchase_record(user_id: str, record_in: RecordCreate) -> Record:
    """
    購入履歴を登録する。
    """
    # 修正ポイント: mode="json" と by_alias=True を使用する
    # by_alias=True により、final_price -> price, final_purchase_date -> purchase_date に変換される
    record_dict = record_in.model_dump(mode="json", by_alias=True)
    record_dict["user_id"] = user_id  # ユーザーIDを手動で追加

    response: APIResponse = supabase.table("purchases").insert(record_dict).execute()

    if response.data:
        # 登録後、関連情報を含めて取得し直すのが確実
        return get_record_by_id(user_id, response.data[0]["id"])
    raise Exception("Could not create purchase record")


def get_records_by_item_id(user_id: str, item_id: int) -> List[Record]:
    """
    特定商品IDに紐づく購入履歴を全て取得する（価格比較の計算に使用）。
    関連テーブルの情報も一緒に取得(JOIN)する。
    """
    response: APIResponse = (
        supabase.table("purchases")
        .select("*, items!inner(name), stores!inner(name)")
        .eq("user_id", user_id)
        .eq("item_id", item_id)
        .execute()
    )

    if response.data:
        # ネストされたデータをフラットな構造に整形
        records = []
        for r in response.data:
            r["item_name"] = r["items"]["name"]
            r["store_name"] = r["stores"]["name"]
            records.append(Record(**r))
        return records
    return []


def get_record_by_id(user_id: str, record_id: int) -> Optional[Record]:
    """
    履歴IDに基づき購入履歴を取得する。関連情報もJOINする。
    """
    response: APIResponse = (
        supabase.table("purchases")
        .select("*, items!inner(name), stores!inner(name)")
        .eq("user_id", user_id)
        .eq("id", record_id)
        .single()
        .execute()
    )

    if response.data:
        r = response.data
        r["item_name"] = r["items"]["name"]
        r["store_name"] = r["stores"]["name"]
        return Record(**r)
    return None


def update_record(
    user_id: str, record_id: int, record_in: RecordCreate
) -> Optional[Record]:
    """
    購入履歴を更新する。
    """
    record_dict = record_in.model_dump()
    response: APIResponse = (
        supabase.table("purchases")
        .update(record_dict)
        .eq("user_id", user_id)
        .eq("id", record_id)
        .execute()
    )

    if response.data:
        return get_record_by_id(user_id, response.data[0]["id"])
    return None


def delete_record(user_id: str, record_id: int) -> bool:
    """
    購入履歴を削除する。
    """
    response: APIResponse = (
        supabase.table("purchases")
        .delete()
        .eq("user_id", user_id)
        .eq("id", record_id)
        .execute()
    )
    return bool(response.data)


def get_all_records_for_export(user_id: str) -> List[Dict[str, Any]]:
    """
    特定ユーザーの全購入履歴、関連する商品・店舗名を取得する（エクスポート機能用）。
    """
    response: APIResponse = (
        supabase.table("purchases")
        .select(
            "purchase_date, price, raw_item_name, items:items(name), stores:stores(name)"
        )
        .eq("user_id", user_id)
        .execute()
    )

    if response.data:
        # CSV出力に適した形式に整形
        export_data = []
        for r in response.data:
            export_data.append(
                {
                    "購入日": r["purchase_date"],
                    "価格": r["price"],
                    "商品名（レシート表記）": r["raw_item_name"],
                    "商品名（標準）": r["items"]["name"] if r.get("items") else "",
                    "店舗名": r["stores"]["name"] if r.get("stores") else "",
                }
            )
        return export_data
    return []


def get_item_store_price_averages(user_id: str, item_id: int) -> List[PriceComparison]:
    """
    SupabaseのPostgreSQL Function (RPC) を呼び出して、集計済みの結果を直接受け取る。
    """
    # 'get_price_comparison'という名前の関数をSupabaseに依頼するだけ
    response: APIResponse = supabase.rpc(
        "get_price_comparison", {"p_user_id": user_id, "p_item_id": item_id}
    ).execute()

    if response.data:
        return [PriceComparison(**row) for row in response.data]
    return []
