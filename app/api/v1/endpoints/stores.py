# stores.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User
from app.api.v1.schemas.store import Store, StoreCreate
from app.core.security import get_current_active_user
from app.services import db_manager

router = APIRouter(prefix="/stores", tags=["Stores"])

# 店舗の一覧取得
@router.get("/", response_model=List[Store])
async def read_stores(current_user: User = Depends(get_current_active_user)):
    """ユーザーが登録した店舗の一覧を取得する"""
    return db_manager.get_stores_by_user(current_user.id)

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
    """特定の店舗情報を削除する"""
    success = db_manager.delete_store(current_user.id, store_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Store not found or you don't have permission."
        )
    return