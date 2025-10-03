from typing import List, Tuple, Optional
from datetime import date, datetime
import re
from rapidfuzz import fuzz  # 類似度計算ライブラリ

from app.api.v1.schemas.item import Item
from app.api.v1.schemas.store import Store
from app.api.v1.schemas.record import OCRResult
from app.services import db_manager

# 類似度の閾値 (SIMILARITY_THRESHOLD点以上で既存と判定)
SIMILARITY_THRESHOLD = 70.0

# --- ヘルパー関数 ---


def _normalize_date(date_input) -> date:
    """
    様々な形式の日付文字列（例: '2025/10/1', '2025年 10月1日'）を YYYY-MM-DD 形式の date オブジェクトに変換する。
    変換できない場合は、本日の日付を返す。
    """
    if date_input is None:
        return date.today()

    date_str = str(date_input).strip()

    # 日本語形式 (例: 2025年 10月1日) を 'YYYY-MM-DD' 形式に変換
    # スラッシュ、ドット、ハイフン、日本語表現を統一
    normalized_str = (
        date_str.replace("年", "-")
        .replace("月", "-")
        .replace("日", "")
        .replace("/", "-")
        .replace(".", "-")
    )

    # 正規表現で YYYY-MM-DD (または類似) のパターンを抽出
    match = re.search(r"(\d{4})[^\d]*(\d{1,2})[^\d]*(\d{1,2})", normalized_str)

    if match:
        try:
            year, month, day = map(int, match.groups())
            # 存在しない日付（例: 2月30日）を防ぐためのチェック
            return date(year, month, day)
        except ValueError:
            # 日付として無効な場合 (例: 2025-2-30)
            pass

    # 既存のパースロジックで試す（例: '2025-10-01'）
    try:
        dt = datetime.strptime(normalized_str, "%Y-%m-%d")
        return dt.date()
    except ValueError:
        pass

    return date.today()  # どの形式にも一致しない場合は本日の日付


def _normalize_name(
    user_id: str, raw_name: str, existing_data_getter
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    商品名または店舗名の名寄せ処理を実行し、結果を返す。

    :param raw_name: OCRから読み取られた元の名称
    :param existing_data_getter: 既存のデータを取得する関数 (e.g., db_manager.get_items_by_user)
    :return: (is_new, suggested_id, suggested_name) のタプル
    """
    # データベースから既存のデータを取得
    existing_list = existing_data_getter(user_id)

    if not existing_list:
        return (True, None, raw_name)

    # 名寄せ処理
    best_match: Optional[Item | Store] = None
    best_score = 0.0

    for entity in existing_list:
        # Item/Storeスキーマの name 属性を使用
        existing_name = entity.name

        # RapidFuzzによる類似度計算 (WRatioは単語の順序や長さの違いに強い)
        score = fuzz.WRatio(raw_name.lower(), existing_name.lower())

        if score > best_score:
            best_score = score
            best_match = entity

    # print(
    #     f"Best match for '{raw_name}': '{best_match.name if best_match else None}' with score {best_score}"
    # )
    if best_score >= SIMILARITY_THRESHOLD and best_match is not None:
        # 既存のものと判定
        return (False, best_match.id, best_match.name)
    else:
        # 新規と判定（または類似度が低すぎる）
        # 提案名には生のOCRデータをセット
        return (True, None, raw_name)


# --- メインロジック ---


def normalize_ocr_data(
    user_id: str, raw_store_name: str, raw_item_name: str, price: float, purchase_date
) -> OCRResult:
    """
    OCR抽出データを正規化し、名寄せ結果（提案）を含むOCRResultスキーマを返す。
    """
    # 1. 日付の正規化
    normalized_date = _normalize_date(purchase_date)

    # 2. 店舗名の名寄せ
    (is_new_store, suggested_store_id, suggested_store_name) = _normalize_name(
        user_id, raw_store_name, db_manager.get_stores_by_user  # 既存店舗取得関数
    )

    # 3. 商品名の名寄せ
    (is_new_item, suggested_item_id, suggested_item_name) = _normalize_name(
        user_id, raw_item_name, db_manager.get_items_by_user  # 既存商品取得関数
    )

    # 4. OCRResult スキーマの構築
    # raw_priceはfloatで、raw_purchase_dateはdateオブジェクト
    return OCRResult(
        raw_item_name=raw_item_name,
        raw_store_name=raw_store_name,
        raw_price=price,
        raw_purchase_date=normalized_date,  # YYYY-MM-DD形式のdateオブジェクト
        is_new_item=is_new_item,
        suggested_item_id=suggested_item_id,
        suggested_item_name=suggested_item_name,
        is_new_store=is_new_store,
        suggested_store_id=suggested_store_id,
        suggested_store_name=suggested_store_name,
    )


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
    return []


def suggest_stores(user_id: str, query: str) -> List[Store]:
    """
    ユーザーIDと入力クエリに基づいて、既存の店舗名からサジェストリストを返す
    """
    return []
