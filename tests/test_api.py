import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io
import os
from datetime import date
from typing import List
import tempfile

# -----------------------------------------------------------
# 1. テスト環境設定と依存性モック
# -----------------------------------------------------------

# FastAPIアプリケーションのエントリポイントを仮定してインポートします。
# 実際には 'from app.main import app' に置き換えてください。
# ここでは、ルーターと依存関係を統合した仮想的なアプリを構築します。

# 仮想的なFastAPIアプリケーションの構築 (テスト専用)
from fastapi import FastAPI
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.stores import router as stores_router
from app.api.v1.endpoints.items import router as items_router
from app.api.v1.endpoints.receipts import router as receipts_router
from app.core.security import get_current_active_user
from app.api.v1.schemas.user import User

app = FastAPI()
app.include_router(users_router, prefix="/api/v1")
app.include_router(stores_router, prefix="/api/v1")
app.include_router(items_router, prefix="/api/v1")
app.include_router(receipts_router, prefix="/api/v1")

# モックユーザーと認証依存性のオーバーライド
MOCK_USER = User(id="test_user_1", username="test_user", email="test@example.com")


def override_get_current_active_user():
    """認証済みユーザーを常に返すモック関数"""
    return MOCK_USER


# 依存性をテスト用のモック関数で上書き
app.dependency_overrides[get_current_active_user] = override_get_current_active_user

# テストクライアント
client = TestClient(app)

# -----------------------------------------------------------
# 2. ユーティリティ/共通データ
# -----------------------------------------------------------

# ダミーの画像データ (bytes)
DUMMY_IMAGE_BYTES = b"fake_jpeg_data"

# -----------------------------------------------------------
# 3. ユーザー認証・情報取得のテスト (users.py)
# -----------------------------------------------------------


def test_read_users_me_success():
    """ユーザー情報取得エンドポイントのテスト"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == MOCK_USER.id
    assert data["email"] == MOCK_USER.email


# -----------------------------------------------------------
# 4. レシート処理フローの統合テスト (receipts.py)
# -----------------------------------------------------------


@patch("app.services.db_manager.create_purchase_record")
@patch("app.services.data_processor.normalize_ocr_data")
@patch("app.api.v1.endpoints.receipts.process_image")
def test_upload_receipt_and_process_success(
    mock_process_image, mock_normalize, mock_create_record
):
    """レシートアップロード、OCR、正規化提案のフローテスト"""
    # 1. OCR結果のモック
    mock_raw_data = {
        "store_name": "ファミマ",
        "item_name": "牛乳パック",
        "price": "240.0",
        "purchase_date": str(date.today().isoformat()),
    }
    mock_process_image.return_value = [mock_raw_data]

    # 2. 正規化結果のモック (既存アイテムへの名寄せを提案)
    mock_normalize.return_value = {
        "raw_item_name": "牛乳パック",
        "raw_store_name": "ファミマ",
        "raw_price": "240.0",
        "raw_purchase_date": str(
            date.today().isoformat()
        ),  # dateをisoformat文字列に変更
        "is_new_item": False,
        "suggested_item_id": 101,
        "suggested_item_name": "牛乳",
        "is_new_store": False,
        "suggested_store_id": 201,
        "suggested_store_name": "ファミリーマート",
        "price": 240.0,
        "purchase_date": date.today().isoformat(),
    }

    files = {"file": ("receipt.jpg", DUMMY_IMAGE_BYTES, "image/jpeg")}
    response = client.post("/api/v1/receipts/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["suggested_item_id"] == 101
    mock_process_image.assert_called_once()
    mock_normalize.assert_called_once()


@patch("app.services.db_manager.create_purchase_record")
def test_confirm_and_register_record_success(mock_create_record):
    """OCR結果確定後の購入履歴登録テスト"""
    from app.api.v1.schemas.record import RecordCreate, Record

    # DB登録成功時の返り値モック
    mock_record_in = RecordCreate(
        raw_item_name="牛乳パック",
        raw_store_name="ファミマ",
        raw_price="240.0",
        raw_purchase_date=str(date.today()),
        item_id=101,
        store_id=201,
        final_price=240.0,
        final_purchase_date=date.today(),
    )
    mock_record_out = Record(
        id=500,
        user_id=MOCK_USER.id,
        price=240.0,
        purchase_date=date.today(),
        item_id=101,
        store_id=201,
        item_name="牛乳",
        store_name="ファミリーマート",
    )
    mock_create_record.return_value = mock_record_out

    response = client.post(
        "/api/v1/receipts/confirm",
        json=mock_record_in.model_dump(mode="json", by_alias=True),
    )

    assert response.status_code == 201
    assert response.json()["id"] == 500
    mock_create_record.assert_called_once()
    assert mock_create_record.call_args[0][0] == MOCK_USER.id  # user_idが渡されているか


# -----------------------------------------------------------
# 5. 商品管理 (Item) のテスト (items.py)
# -----------------------------------------------------------


@patch("app.services.db_manager.update_item")
def test_update_item_owner_check_failure(mock_update_item):
    """商品更新時の所有権チェック失敗テスト (DBマネージャがNoneを返す)"""
    from app.api.v1.schemas.item import ItemCreate

    mock_update_item.return_value = None  # 存在しない/所有権のないアイテム

    item_in = ItemCreate(name="コーラ 500ml")
    response = client.put("/api/v1/items/999", json=item_in.model_dump())

    assert response.status_code == 404
    assert "not found or you don't have permission" in response.json()["detail"]


@patch("app.services.data_processor.suggest_items")
def test_suggest_items_feature(mock_suggest_items):
    """商品名サジェスト機能のテスト (表記ゆれ対策の連携)"""
    from app.api.v1.schemas.item import Item

    mock_suggest_items.return_value = [
        Item(id=10, user_id=MOCK_USER.id, name="サッポロ一番"),
        Item(id=11, user_id=MOCK_USER.id, name="サッポロポテト"),
    ]

    response = client.get("/api/v1/items/suggest?query=サッポ")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "サッポロ一番" in data[0]["name"]
    mock_suggest_items.assert_called_once_with(MOCK_USER.id, "サッポ")


@patch("app.services.db_manager.get_item_price_comparisons")
def test_get_price_comparison_success(mock_comparison):
    """価格比較機能のテスト (集計ロジックの連携)"""
    # db_managerが返すモックデータ
    mock_comparison.return_value = [
        {
            "item_name": "納豆",
            "store_name": "Aスーパー",
            "average_price": 98.0,
            "overall_average_price": 102.0,
        },
        {
            "item_name": "納豆",
            "store_name": "Bコンビニ",
            "average_price": 110.0,
            "overall_average_price": 102.0,
        },
    ]

    response = client.get("/api/v1/items/101/compare")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["average_price"] == 98.0
    mock_comparison.assert_called_once_with(MOCK_USER.id, 101)


# @patch("os.remove")  # 実際の一時ファイル削除をスキップ
# @patch("app.services.db_manager.export_user_data_to_csv")
# def test_export_data_csv_export(mock_export_csv, mock_remove):
#     """データエクスポート機能のテスト"""

#     # 仮想的なCSVファイルを作成し、db_managerがそのパスを返すようにモック
#     TEST_CSV_CONTENT = (
#         "date,store_name,item_name,price\n2023-10-01,Aスーパー,牛乳,200\n"
#     )

#     # 🚨 修正: tempfileを使用して、OSに関係なく安全な一時ファイルを作成 🚨
#     with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
#         tmp.write(TEST_CSV_CONTENT.encode("utf-8"))  # <-- .encode('utf-8') を追加
#         TEMP_FILE_PATH = tmp.name  # 作成された一時ファイルのパスを取得

#     # db_managerのモックが一時ファイルのパスを返すように設定
#     mock_export_csv.return_value = TEMP_FILE_PATH

#     # 1. API呼び出し
#     response = client.get("/api/v1/items/export/csv")

#     # 2. テスト後、一時ファイルを削除
#     try:
#         os.remove(TEMP_FILE_PATH)
#     except Exception:
#         pass  # 削除失敗は無視 (テスト結果に影響しないため)

#     assert response.status_code == 200
#     assert response.headers["content-type"] == "text/csv; charset=utf-8"
#     assert (
#         f"filename=purchase_history_{MOCK_USER.id}.csv"
#         in response.headers["content-disposition"]
#     )
#     assert response.content.decode("utf-8") == TEST_CSV_CONTENT  # 内容の検証
#     mock_export_csv.assert_called_once_with(MOCK_USER.id)


# -----------------------------------------------------------
# 6. 店舗管理 (Store) のテスト (stores.py)
# -----------------------------------------------------------


@patch("app.services.db_manager.create_store")
def test_create_store_success(mock_create_store):
    """店舗の新規登録テスト"""
    from app.api.v1.schemas.store import StoreCreate, Store

    store_in = StoreCreate(name="新規スーパー")
    mock_create_store.return_value = Store(
        id=301, user_id=MOCK_USER.id, name="新規スーパー"
    )

    response = client.post("/api/v1/stores/", json=store_in.model_dump())

    assert response.status_code == 201
    assert response.json()["name"] == "新規スーパー"
    mock_create_store.assert_called_once()


@patch("app.services.db_manager.delete_store")
def test_delete_store_success(mock_delete_store):
    """店舗の削除テスト (成功)"""
    mock_delete_store.return_value = True  # 削除成功

    response = client.delete("/api/v1/stores/301")

    assert response.status_code == 204
    mock_delete_store.assert_called_once_with(MOCK_USER.id, 301)


@patch("app.services.db_manager.delete_store")
def test_delete_store_not_found(mock_delete_store):
    """店舗の削除テスト (失敗: 存在しない/権限なし)"""
    mock_delete_store.return_value = False  # 削除失敗

    response = client.delete("/api/v1/stores/999")

    assert response.status_code == 404
    assert "not found or you don't have permission" in response.json()["detail"]
