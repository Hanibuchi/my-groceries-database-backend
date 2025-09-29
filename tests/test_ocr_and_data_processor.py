# test_ocr_and_data_processor.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.ocr import ocr_engine # 開発中のOCRエンジン
from app.services.data_processor import normalize_ocr_data
from app.api.v1.schemas.record import RecordBase

# --- OCR Engine のモックテスト ---

# OCRエンジンの出力が期待通りかテスト
def test_ocr_engine_extracts_data_correctly():
    """モック画像データからレシート項目が正しく抽出されるか"""
    # 実際にはテスト用のレシート画像を準備するか、モックで代替
    mock_image_bytes = b"fake image content"
    
    # 実際のOCR処理をスキップし、固定の抽出結果を返すようにモック化
    with patch('app.ocr.ocr_engine.TextExtractor.process_image') as mock_process:
        # OCR処理の結果をシミュレート
        mock_process.return_value = {
            "store_name": "スーパーA店",
            "items": [
                {"name": "牛乳(低脂肪)", "price": 198.0, "quantity": 1.0},
                {"name": "バナナ", "price": 120.0, "quantity": 1.0}
            ],
            "purchase_date": "2024-05-10"
        }
        
        # ocr_service.process_image の呼び出し (ここでは簡略化のため直接 ocr_engine をテスト)
        # 実際には ocr_service のラッパー経由でテストすることが望ましい
        result = ocr_engine.TextExtractor.process_image(mock_image_bytes)
        
        assert result["store_name"] == "スーパーA店"
        assert len(result["items"]) == 2

# --- Data Processor の名寄せテスト ---

# DB操作をモック化
@patch('app.services.db_manager.get_item_by_name_fuzzy')
@patch('app.services.db_manager.get_store_by_name_fuzzy')
def test_normalize_new_item_and_store(mock_get_store, mock_get_item):
    """新規の商品・店舗が正しく判定されるか"""
    # 既存の商品・店舗が見つからないケースをシミュレート
    mock_get_item.return_value = None
    mock_get_store.return_value = None
    
    result = normalize_ocr_data(
        user_id=1, 
        raw_store_name="ライフ 練馬店", 
        raw_item_name="牛乳", 
        price=220, 
        quantity=1.0, 
        purchase_date="2024-05-10"
    )
    
    assert result.is_new_item is True
    assert result.is_new_store is True
    assert result.suggested_item_id is None
    assert result.record.raw_item_name == "牛乳"


@patch('app.services.db_manager.get_item_by_name_fuzzy')
@patch('app.services.db_manager.get_store_by_name_fuzzy')
def test_normalize_existing_item(mock_get_store, mock_get_item):
    """既存の商品が正しく名寄せされるか（表記ゆれ）"""
    # 既存の商品が見つかったケースをシミュレート
    mock_get_item.return_value = MagicMock(id=101, normalized_name="明治 おいしい牛乳")
    mock_get_store.return_value = MagicMock(id=201, name="イオン")

    result = normalize_ocr_data(
        user_id=1, 
        raw_store_name="イオンスーパー", 
        raw_item_name="オイシイ牛乳", # 表記ゆれ
        price=250, 
        quantity=1.0, 
        purchase_date="2024-05-11"
    )
    
    # 既存の商品に紐づけられたことを確認
    assert result.is_new_item is False
    assert result.suggested_item_id == 101
    assert result.suggested_item_name == "明治 おいしい牛乳"
    
    # 既存の店舗に紐づけられたことを確認
    assert result.is_new_store is False
    assert result.suggested_store_id == 201
    assert result.suggested_store_name == "イオン"