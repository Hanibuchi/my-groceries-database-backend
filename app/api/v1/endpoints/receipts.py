# receipts.py (修正案)
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User
# レスポンスモデルの型ヒントを変更するためにList[OCRResult]を使用
from app.api.v1.schemas.record import Record, OCRResult, RecordCreate
from app.core.security import get_current_active_user
from app.ocr.ocr_engine import process_image
from app.services import data_processor
from app.services import db_manager

router = APIRouter(prefix="/receipts", tags=["Receipts"])

# レシート画像アップロードとOCR実行
# response_modelをList[OCRResult]に変更
@router.post("/upload", response_model=List[OCRResult])
async def upload_receipt_and_process(
    file: UploadFile = File(..., description="レシートの画像ファイル"),
    current_user: User = Depends(get_current_active_user)
):
    """
    レシート画像をアップロードし、OCRにかけてデータを抽出し、正規化の提案を行う。
    結果をユーザーに確認・修正させるために、抽出されたすべての項目をList[OCRResult]として返す。
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only JPEG and PNG are supported."
        )

    # 1. 画像データを読み込み
    image_bytes = await file.read()
    
    # 2. OCRサービスを実行
    # raw_data_listは、レシート上の各商品に対応する辞書のリストと想定
    raw_data_list = process_image(image_bytes)
    
    if not raw_data_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract data from receipt.")
        
    # 3. データ正規化サービスを実行し、提案を構築
    # すべてのOCR結果を格納するリスト
    normalized_results: List[OCRResult] = []
    
    # raw_data_listの要素すべてに対してループ処理を実行
    for raw_data in raw_data_list:
        # data_processor.normalize_ocr_dataを各要素に適用
        ocr_result = data_processor.normalize_ocr_data(
            user_id=current_user.id,
            raw_store_name=raw_data.get("store_name", "不明な店舗"),
            raw_item_name=raw_data.get("item_name", "不明な商品"),
            price=raw_data.get("price", 0.0),
            purchase_date=raw_data.get("purchase_date", None)
        )
        
        normalized_results.append(ocr_result)
    
    # すべての正規化された結果のリストを返す
    return normalized_results

# OCR結果の確定と購入履歴の登録
@router.post("/confirm", response_model=Record, status_code=status.HTTP_201_CREATED)
async def confirm_and_register_record(
    record_in: RecordCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    ユーザーが確認・修正したOCR結果 (RecordCreate) を最終的な購入履歴としてDBに登録する。
    （このエンドポイントの変更は不要と判断）
    """
    # サービスの呼び出しとDBへの保存
    db_record = db_manager.create_purchase_record(current_user.id, record_in)
    
    return db_record