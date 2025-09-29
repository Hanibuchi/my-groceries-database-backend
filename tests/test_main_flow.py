# test_main_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

# 認証済みユーザーのトークンを取得するフィクスチャ (前述のテストで成功する前提)
@pytest.fixture(scope="session")
def auth_token():
    # 便宜上、テスト開始前にユーザーを作成し、トークンを取得する
    client.post("/v1/auth/register", json={"username": "flowuser", "email": "flow@example.com", "password": "flowpassword"})
    response = client.post(
        "/v1/auth/token",
        data={"username": "flowuser", "password": "flowpassword"}
    )
    return response.json()["access_token"]

# --- OCR結果の取得と確認フロー ---

@patch('app.services.ocr.process_image')
@patch('app.services.data_processor.normalize_ocr_data')
def test_upload_receipt_and_get_ocr_result(mock_normalize, mock_ocr, auth_token):
    """レシートアップロードがOCR結果の確認スキーマを返すか"""
    
    # OCR結果のモック
    mock_ocr.return_value = [{"store_name": "ダイエー", "item_name": "米 5kg", "price": 2500, "quantity": 1.0, "purchase_date": "2024-05-20"}]
    
    # 正規化後の提案結果のモック (新規商品として提案)
    mock_normalize.return_value = MagicMock(
        record=MagicMock(raw_store_name="ダイエー", raw_item_name="米 5kg", price=2500, quantity=1.0),
        is_new_item=True,
        is_new_store=False, # 店舗は既存と仮定
        suggested_store_id=99
    )
    
    # テスト用のダミー画像を作成 (ファイルアップロードのため)
    image_data = b"fake image content"
    
    response = client.post(
        "/v1/receipts/upload",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("receipt.jpg", image_data, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["record"]["raw_item_name"] == "米 5kg"
    assert data["is_new_item"] is True
    assert data["suggested_store_id"] == 99


# --- 購入履歴の確定登録フロー ---

@patch('app.services.db_manager.create_purchase_record')
def test_confirm_and_register_record(mock_create_record, auth_token):
    """確認済みOCRデータがDBに正しく登録されるか"""
    
    # DB登録後のモデルのモック
    mock_create_record.return_value = MagicMock(
        id=10, 
        user_id=1, 
        raw_item_name="米 5kg", 
        normalized_item_name="コシヒカリ 5kg",
        price=2500
    )
    
    # ユーザーがフロントで確認・修正したと仮定したリクエストデータ
    confirmed_data = {
        "record": {
            "raw_store_name": "ダイエー",
            "raw_item_name": "米 5kg",
            "price": 2500.0,
            "quantity": 1.0,
            "purchase_date": "2024-05-20",
            "item_id": 101, # 既存の商品IDに紐づけ
            "store_id": 99   # 既存の店舗IDに紐づけ
        },
        "is_new_item": False,
        "is_new_store": False
    }
    
    response = client.post(
        "/v1/receipts/confirm",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=confirmed_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 10
    assert data["normalized_item_name"] == "コシヒカリ 5kg"


# --- 価格比較機能のテスト (統合テスト) ---

@patch('app.services.db_manager.get_item_price_comparisons')
def test_get_price_comparison(mock_comparison, auth_token):
    """価格比較エンドポイントが期待されるデータを返すか"""
    
    # 価格比較結果のモック
    mock_comparison.return_value = [
        {
            "normalized_item_name": "明治 おいしい牛乳",
            "store_name": "スーパーA",
            "latest_price": 240.0,
            "average_price": 250.0,
            "purchase_count": 5,
            "overall_average_price": 245.0
        },
        {
            "normalized_item_name": "明治 おいしい牛乳",
            "store_name": "コンビニB",
            "latest_price": 280.0,
            "average_price": 280.0,
            "purchase_count": 1,
            "overall_average_price": 245.0
        },
    ]

    item_id = 101
    response = client.get(
        f"/v1/items/{item_id}/compare",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["store_name"] == "スーパーA"
    assert data[1]["latest_price"] == 280.0