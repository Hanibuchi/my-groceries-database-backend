# stores.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from typing import List, Optional

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User
from app.api.v1.schemas.store import Store, StoreCreate
from app.core.security import get_current_active_user
from app.services import db_manager
from app.services import db_manager, data_processor # 商品名検索にdata_processorも使用

router = APIRouter(prefix="/stores", tags=["Stores"])

# 店舗の一覧取得
@router.get("/", response_model=List[Store])
async def read_stores(current_user: User = Depends(get_current_active_user),
    query: Optional[str] = Query(None, description="商品名の一部検索クエリ")
    ):
    """ユーザーが登録した店舗の一覧、または部分一致で検索した結果を取得する"""
    if query:
        # data_processorが表記ゆれを考慮した検索ロジックを持つことを想定
        return data_processor.suggest_stores(current_user.id, query)
    return db_manager.get_stores_by_user(current_user.id)

# 店舗の詳細取得
@router.get("/{store_id}", response_model=Store)
async def read_store(store_id: int, current_user: User = Depends(get_current_active_user)):
    """特定の店舗IDに基づいて詳細情報を取得する"""
    
    # db_managerに、IDとユーザーIDで店舗を取得する関数を呼び出す
    store = db_manager.get_store_by_id_and_user(current_user.id, store_id)
    
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Store not found or you don't have permission."
        )
    return store

# 店舗の新規登録（手動登録またはOCR後の修正）
@router.post("/", response_model=Store, status_code=status.HTTP_201_CREATED)
async def create_store(store_in: StoreCreate, current_user: User = Depends(get_current_active_user)):
    """新しい店舗情報を登録する"""
    return db_manager.create_store(current_user.id, store_in)

# 店舗の変更 (PUT / PATCH) - ここではPUTの例
@router.put("/{store_id}", response_model=Store)
async def update_store(
    store_id: int, 
    store_in: StoreCreate, 
    current_user: User = Depends(get_current_active_user)
):
    """特定の店舗情報を更新する"""
    # 存在チェックと所有者チェックをdb_managerで実施
    updated_store = db_manager.update_store(current_user.id, store_id, store_in)
    if not updated_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Store not found or you don't have permission."
        )
    return updated_store

# 店舗の削除
@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: int, current_user: User = Depends(get_current_active_user)):
    """特定の店舗情報を削除する (関連する購入履歴がある場合は削除せず、エラーを出す)"""
    success = db_manager.delete_store(current_user.id, store_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Store not found or you don't have permission."
        )
    return

# 店舗名サジェスト機能 (表記ゆれ対策を兼ねる)
@router.get("/suggest", response_model=List[Store])
async def suggest_stores(
    query: str = Query(..., description="入力中の店舗名"),
    current_user: User = Depends(get_current_active_user)
):
    """入力文字列に基づいて、既存の店舗名からサジェストリストを返す"""
    # 表記ゆれ対策 (部分一致、類似度計算など) は data_processor に任せる
    return data_processor.suggest_stores(current_user.id, query)