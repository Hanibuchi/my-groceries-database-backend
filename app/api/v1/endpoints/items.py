# items.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from fastapi.responses import StreamingResponse
# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User
from app.api.v1.schemas.item import Item, ItemCreate
from app.api.v1.schemas.record import Record, PriceComparison
from app.core.security import get_current_active_user
from app.services import db_manager, data_processor # 商品名検索にdata_processorも使用

router = APIRouter(prefix="/items", tags=["Items & History"])

## 商品情報 (Item) 関連

# 商品の一覧取得
@router.get("/", response_model=List[Item])
async def read_items(
    current_user: User = Depends(get_current_active_user),
    query: Optional[str] = Query(None, description="商品名の一部検索クエリ")
):
    """ユーザーが登録した商品の一覧、または部分一致で検索した結果を取得する"""
    if query:
        # data_processorが表記ゆれを考慮した検索ロジックを持つことを想定
        return data_processor.suggest_items(current_user.id, query)
    return db_manager.get_items_by_user(current_user.id)

# 商品の新規登録 (手動登録またはOCR後の修正)
@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item_in: ItemCreate, current_user: User = Depends(get_current_active_user)):
    """新しい商品情報を登録する"""
    return db_manager.create_item(current_user.id, item_in)

# 商品の変更 (PUT)
@router.put("/{item_id}", response_model=Item)
async def update_item(
    item_id: int, 
    item_in: ItemCreate, 
    current_user: User = Depends(get_current_active_user)
):
    """特定の商品の正規化名を更新する"""
    # 存在チェックと所有者チェックをdb_managerで実施
    # 注意: ここで正規化名を変更すると、このIDに紐づく過去の全購入履歴に影響します。
    updated_item = db_manager.update_item(current_user.id, item_id, item_in)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found or you don't have permission."
        )
    return updated_item

# 商品の削除
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, current_user: User = Depends(get_current_active_user)):
    """特定の商品の正規化情報を削除する (関連する購入履歴がある場合は削除せず、エラーを出す)"""
    success = db_manager.delete_item(current_user.id, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found or you don't have permission."
        )
    return

# 商品名サジェスト機能 (表記ゆれ対策を兼ねる)
@router.get("/suggest", response_model=List[Item])
async def suggest_items(
    query: str = Query(..., description="入力中の商品名"),
    current_user: User = Depends(get_current_active_user)
):
    """入力文字列に基づいて、既存の商品名からサジェストリストを返す"""
    # 表記ゆれ対策 (部分一致、類似度計算など) は data_processor に任せる
    return data_processor.suggest_items(current_user.id, query)


## 購入履歴 (Record) 関連

# 特定商品の購入履歴を取得
@router.get("/{item_id}/history", response_model=List[Record])
async def get_item_history(
    item_id: int, 
    current_user: User = Depends(get_current_active_user)
):
    """特定の正規化された商品IDの購入履歴を全て取得する"""
    # 履歴の取得と、ユーザーの所有物であることの確認
    return db_manager.get_records_by_item_id(current_user.id, item_id)

# 購入履歴の更新 (PUT)
@router.put("/records/{record_id}", response_model=Record)
async def update_record(
    record_id: int, 
    record_in: Record, # 更新に必要なデータを含むスキーマを想定 (例: price, quantity, purchase_date, store_id)
    current_user: User = Depends(get_current_active_user)
):
    """特定の購入履歴を更新する"""
    # 存在チェックと所有者チェックをdb_managerで実施
    updated_record = db_manager.update_record(current_user.id, record_id, record_in)
    if not updated_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Record not found or you don't have permission."
        )
    return updated_record

# 購入履歴の削除 (DELETE)
@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(record_id: int, current_user: User = Depends(get_current_active_user)):
    """特定の購入履歴を削除する"""
    success = db_manager.delete_record(current_user.id, record_id)
    if not success:
        # 削除対象が存在しない、または権限がない場合は404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Record not found or you don't have permission."
        )
    return


## 価格比較機能

# 商品の各店舗の平均値を返す機能 (リアルタイムな価格比較)
@router.get("/{item_id}/compare", response_model=List[PriceComparison])
async def get_price_comparison(
    item_id: int, 
    current_user: User = Depends(get_current_active_user)
):
    """
    特定の正規化された商品について、店舗ごとの最新価格と平均価格を比較して返す
    """
    # db_managerに複雑な集計ロジックを実装
    comparison_data = db_manager.get_item_price_comparisons(current_user.id, item_id)
    
    if not comparison_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No history found for this item.")
        
    return comparison_data


## エクスポート機能

@router.get("/export/csv")
async def export_data(current_user: User = Depends(get_current_active_user)):
    # 1. CSVファイルを生成し、一時的なファイルパスを取得する
    #    （db_manager.export_user_data_to_csv()が一時ファイルを作成すると想定）
    file_path = db_manager.export_user_data_to_csv(current_user.id) 

    # 2. ファイルをバイナリ読み込みモードで開き、StreamingResponseで返す
    #    media_type="text/csv" でブラウザにCSVファイルであることを伝える
    return StreamingResponse(
        open(file_path, "rb"), 
        media_type="text/csv",
        # ダウンロード時のファイル名を指定するHTTPヘッダー
        headers={"Content-Disposition": f"attachment; filename=purchase_history_{current_user.id}.csv"}
    )
    
## 全データ削除機能
@router.delete("/data", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_user_data_endpoint(current_user: User = Depends(get_current_active_user)):
    """
    認証済みユーザーの内部DBに保存されている全てのデータ（商品、購入履歴、店舗など）を削除する。
    🚨 この操作は元に戻せません。
    """
    success = db_manager.delete_all_user_data(current_user.id)
    
    if not success:
        # DB操作で予期せぬエラーが発生した場合など
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete all user data."
        )
    
    # 成功した場合、レスポンスボディなしの 204 No Content を返す
    return