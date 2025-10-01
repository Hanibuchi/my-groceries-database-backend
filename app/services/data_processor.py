from typing import List
from app.api.v1.schemas.item import Item
from app.api.v1.schemas.store import Store
from app.services import db_manager
from app.api.v1.schemas.record import OCRResult

def normalize_ocr_data(user_id: str, raw_store_name: str, raw_item_name: str, price: float, purchase_date) -> OCRResult:
    pass

def suggest_items(user_id: str, query: str) -> List[Item]:
    """
    ユーザーIDと入力クエリに基づいて、既存の商品名からサジェストリストを返す
    """
    # ここで部分一致や類似度計算などのロジックを実装
    # 例えば、Levenshtein距離やTrigramマッチングなど
    # 簡易的には、部分一致でフィルタリングするだけでも良いでしょう
    # all_items = db_manager.get_items_by_user_id(user_id)
    # suggestions = [item for item in all_items if query.lower() in item.normalized_name.lower()]
    
    # 必要に応じて、類似度スコアでソートしたり、上位N件に絞ることも可能
    # return suggestions[:10]  # 上位10件を返す例
    
def suggest_stores(user_id: str, query: str) -> List[Store]:
    """
    ユーザーIDと入力クエリに基づいて、既存の店舗名からサジェストリストを返す
    """
    pass