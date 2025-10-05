from typing import List, Tuple, Optional, Union
from datetime import date, datetime
import re
from rapidfuzz import fuzz  # 類似度計算ライブラリ

from app.api.v1.schemas.item import Item
from app.api.v1.schemas.store import Store
from app.api.v1.schemas.record import OCRResult
from app.services import db_manager

# 類似度の閾値 (SIMILARITY_THRESHOLD点以上で既存と判定)
SIMILARITY_THRESHOLD = 70.0
# サジェストの上限数
SUGGESTION_LIMIT = 10

# --- ヘルパー関数 ---


def _normalize_date(date_input) -> date:
    """
    様々な形式の日付文字列（例: '2025/10/1', '2025年 10月1日'）を YYYY-MM-DD 形式の date オブジェクトに変換する。
    変換できない場合は、本日の日付を返す。
    """

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


def _normalize_price(s: str) -> float:
    s = str(s)
    # 前後の空白除去
    s = s.strip()

    # 先頭が '\' の場合は削除
    if s.startswith("\\"):
        s = s[1:]

    # 末尾が '円' または 'yen' の場合は削除
    if s.endswith("円"):
        s = s[:-1]
    elif s.lower().endswith("yen"):
        s = s[:-3]

    # 余計な空白削除
    s = s.strip()

    # 数字以外の文字は '0' に置換
    cleaned = []
    for ch in s:
        if ch.isdigit() or ch == "." or ch in "+-":
            cleaned.append(ch)
        else:
            cleaned.append("0")

    cleaned_str = "".join(cleaned)

    try:
        return float(cleaned_str)
    except ValueError:
        return 0.0


def _normalize_name(
    user_id: str, raw_name: Optional[str], existing_data_getter
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    商品名または店舗名の名寄せ処理を実行し、結果を返す。

    :param raw_name: OCRから読み取られた元の名称
    :param existing_data_getter: 既存のデータを取得する関数 (e.g., db_manager.get_items_by_user)
    :return: (is_new, suggested_id, suggested_name) のタプル
    """
    # raw_name が None の場合、.lower() を呼び出すとエラーになるため、ここで処理を止める
    if raw_name is None or not str(raw_name).strip():
        # 新規と判定し、IDはNone、名称は空文字列として返す（または、元のraw_nameがNoneであればNoneを返す）
        return (True, None, raw_name) 

    # raw_name を文字列として扱い、前後の空白を除去
    raw_name = str(raw_name).strip()
    
    # データベースから既存のデータを取得
    existing_list = existing_data_getter(user_id)

    if not existing_list:
        return (True, None, raw_name)

    # 名寄せ処理
    best_match: Optional[Union[Item, Store]] = None
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


def _suggest_by_similarity(
    user_id: str, query: str, existing_data_getter, entity_type
) -> List:
    """
    商品・店舗サジェスト機能の共通ロジック。
    類似度計算(WRatio)に基づき、スコアの高い順に上位 SUGGESTION_LIMIT 件を返す。
    """
    # DBから既存データを取得
    all_entities = existing_data_getter(user_id)
    query_lower = query.lower()

    if not all_entities:
        return []

    scored_entities = []
    for entity in all_entities:
        # Item/Storeスキーマの name 属性を使用
        existing_name = entity.name

        # RapidFuzzによる類似度計算 (WRatioは単語の順序や長さの違いに強い)
        score = fuzz.WRatio(query_lower, existing_name.lower())

        # スコアとエンティティをタプルで保持
        scored_entities.append((score, entity))

    # スコアで降順ソート
    scored_entities.sort(key=lambda x: x[0], reverse=True)

    # 上位 SUGGESTION_LIMIT 件を抽出し、エンティティ本体のみを返す
    # (SUGGESTION_LIMIT はコード冒頭で定義された定数)
    suggestions = [entity for score, entity in scored_entities[:SUGGESTION_LIMIT]]

    return suggestions


# --- メインロジック ---


def normalize_ocr_data(
    user_id: str,
    raw_store_name: str,
    raw_item_name: str,
    raw_price: str,
    raw_purchase_date: Optional[str],
) -> OCRResult:
    """
    OCR抽出データを正規化し、名寄せ結果（提案）を含むOCRResultスキーマを返す。
    """
    if raw_store_name is None:
        raw_store_name = ""
        
    if raw_item_name is None:
        raw_item_name = ""
    
    # raw_purchase_date は既に None のチェックがあるが、
    # _normalize_name の呼び出し側で str() されることを考えると、
    # 他の raw データもここで安全を確保しておくと良い。
    if raw_purchase_date is None:
        raw_purchase_date = ""
    
    # 日付の正規化
    normalized_date = _normalize_date(raw_purchase_date)

    raw_price = str(raw_price)
    # 価格の正規化
    normalized_price = _normalize_price(raw_price)

    # 店舗名の名寄せ
    (is_new_store, suggested_store_id, suggested_store_name) = _normalize_name(
        user_id, raw_store_name, db_manager.get_stores_by_user  # 既存店舗取得関数
    )

    # 商品名の名寄せ
    (is_new_item, suggested_item_id, suggested_item_name) = _normalize_name(
        user_id, raw_item_name, db_manager.get_items_by_user  # 既存商品取得関数
    )

    # OCRResult スキーマの構築
    # raw_priceはfloatで、raw_purchase_dateはdateオブジェクト
    return OCRResult(
        raw_item_name=raw_item_name,
        raw_store_name=raw_store_name,
        raw_price=raw_price,
        raw_purchase_date=raw_purchase_date,  # YYYY-MM-DD形式のdateオブジェクト
        is_new_item=is_new_item,
        suggested_item_id=suggested_item_id,
        suggested_item_name=suggested_item_name,
        is_new_store=is_new_store,
        suggested_store_id=suggested_store_id,
        suggested_store_name=suggested_store_name,
        price=normalized_price,
        purchase_date=normalized_date,
    )


def suggest_items(user_id: str, query: str) -> List[Item]:
    """
    ユーザーIDと入力クエリに基づいて、既存の商品名からサジェストリストを返す。
    類似度計算(WRatio)に基づき、スコアの高い順に上位10件を返す。
    """
    # 共通ロジック関数を呼び出し、既存商品取得関数と商品型を渡す
    return _suggest_by_similarity(user_id, query, db_manager.get_items_by_user, Item)


def suggest_stores(user_id: str, query: str) -> List[Store]:
    """
    ユーザーIDと入力クエリに基づいて、既存の店舗名からサジェストリストを返す。
    類似度計算(WRatio)に基づき、スコアの高い順に上位10件を返す。
    """
    # 共通ロジック関数を呼び出し、既存店舗取得関数と店舗型を渡す
    return _suggest_by_similarity(user_id, query, db_manager.get_stores_by_user, Store)
