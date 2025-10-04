import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime

# テスト対象のモジュールと依存関係のインポート
# 🚨 プロジェクトのルートディレクトリをPYTHONPATHに追加する必要があります
from app.services.data_processor import (
    normalize_ocr_data,
    suggest_items,
    suggest_stores,
)  # suggest_items, suggest_stores を追加

# スキーマのインポート（Pydanticモデルはテスト内でダミーデータとして利用）
from app.api.v1.schemas.item import Item
from app.api.v1.schemas.store import Store
from app.api.v1.schemas.record import OCRResult

# ----------------------------------------------------------------------
# 名寄せ処理のためにdb_managerが返す「既存データ」のダミーリストを定義
# ----------------------------------------------------------------------

TEST_USER_ID = "test-user-uuid-123"

MOCK_EXISTING_ITEMS = [
    Item(id=1, name="牛乳 (1L)", user_id=TEST_USER_ID),
    Item(id=2, name="たまご 10個入", user_id=TEST_USER_ID),
    Item(id=3, name="ポテトチップスうすしお味", user_id=TEST_USER_ID),
]

MOCK_EXISTING_STORES = [
    Store(id=101, name="イオンモール", user_id=TEST_USER_ID),
    Store(id=102, name="ライフ", user_id=TEST_USER_ID),
    Store(id=103, name="セブン-イレブン", user_id=TEST_USER_ID),
]

# ----------------------------------------------------------------------
# テストクラス
# ----------------------------------------------------------------------


# @patchデコレーターのパスは、テスト対象のモジュール（data_processor.py）内でのインポート元を指定します
@patch(
    "app.services.data_processor.db_manager.get_items_by_user",
    return_value=MOCK_EXISTING_ITEMS,
)
@patch(
    "app.services.data_processor.db_manager.get_stores_by_user",
    return_value=MOCK_EXISTING_STORES,
)
class TestNormalizeOCRData(unittest.TestCase):

    def setUp(self):
        # 毎テスト実行前に実行される初期設定
        self.user_id = TEST_USER_ID

    def test_successful_name_matching(self, mock_get_stores, mock_get_items):
        """
        類似度が高い場合に、既存のIDと名称が提案されることを確認
        """
        # --- テストデータ ---
        raw_item_name = (
            "ポテトチップ うす塩"  # 既存の 'ポテトチップスうすしお味' に高類似
        )
        raw_store_name = "イオンモール（仮）"  # 既存の 'イオンモール' に高類似
        raw_price = "150.0"
        raw_date = "2024/05/15"

        # --- 実行 ---
        result: OCRResult = normalize_ocr_data(
            user_id=self.user_id,
            raw_store_name=raw_store_name,
            raw_item_name=raw_item_name,
            raw_price=str(raw_price),
            raw_purchase_date=raw_date,
        )

        # --- 検証 ---
        self.assertIsInstance(result, OCRResult)

        # 1. 商品名 (高類似度 -> 既存)
        self.assertFalse(result.is_new_item, "商品名は新規ではないと提案されるべき")
        self.assertEqual(
            result.suggested_item_id,
            3,
            "ID 3 (ポテトチップスうすしお味) が提案されるべき",
        )
        self.assertEqual(
            result.suggested_item_name,
            "ポテトチップスうすしお味",
            "正確な名称が提案されるべき",
        )

        # 2. 店舗名 (高類似度 -> 既存)
        self.assertFalse(result.is_new_store, "店舗名は新規ではないと提案されるべき")
        self.assertEqual(
            result.suggested_store_id, 101, "ID 101 (イオンモール) が提案されるべき"
        )
        self.assertEqual(
            result.suggested_store_name, "イオンモール", "正確な名称が提案されるべき"
        )

        # 3. 日付の正規化
        self.assertEqual(
            result.purchase_date, date(2024, 5, 15), "日付が正しく正規化されるべき"
        )
        self.assertEqual(result.price, 150.0)

    def test_new_entity_detection(self, mock_get_stores, mock_get_items):
        """
        類似度が低い場合に、新規として登録が提案されることを確認
        """
        # --- テストデータ ---
        raw_item_name = "超高級キャビア"  # 既存商品と低類似度
        raw_store_name = "個人商店田中"  # 既存店舗と低類似度
        raw_price = "10000円"
        raw_date = "2024年12月25日"

        # --- 実行 ---
        result: OCRResult = normalize_ocr_data(
            user_id=self.user_id,
            raw_store_name=raw_store_name,
            raw_item_name=raw_item_name,
            raw_price=raw_price,
            raw_purchase_date=raw_date,
        )

        # --- 検証 ---
        # 1. 商品名 (低類似度 -> 新規)
        self.assertTrue(result.is_new_item, "商品名は新規として提案されるべき")
        self.assertIsNone(result.suggested_item_id, "新規なのでIDはNoneであるべき")
        self.assertEqual(
            result.suggested_item_name,
            raw_item_name,
            "提案名には生のOCRデータが使われるべき",
        )

        # 2. 店舗名 (低類似度 -> 新規)
        self.assertTrue(result.is_new_store, "店舗名は新規として提案されるべき")
        self.assertIsNone(result.suggested_store_id, "新規なのでIDはNoneであるべき")
        self.assertEqual(
            result.suggested_store_name,
            raw_store_name,
            "提案名には生のOCRデータが使われるべき",
        )

        # 3. 日付の正規化 (日本語形式)
        self.assertEqual(
            result.purchase_date,
            date(2024, 12, 25),
            "日本語の日付が正しく正規化されるべき",
        )

    def test_date_format_handling(self, mock_get_stores, mock_get_items):
        """
        様々な日付形式と、パース失敗時の処理を確認
        """

        # 1. 様々な正常な日付形式
        test_cases = [
            ("2023/1/1", date(2023, 1, 1)),
            ("2025年10月01日", date(2025, 10, 1)),
            ("2022-12-31", date(2022, 12, 31)),
            ("2024.07.04", date(2024, 7, 4)),
            ("2015年04月28日（火）", date(2015, 4, 28)),
            (None, date.today()),  # Noneは今日の日付になる
        ]

        for raw_date, expected_date in test_cases:
            with self.subTest(raw_date=raw_date):
                result: OCRResult = normalize_ocr_data(
                    user_id=self.user_id,
                    raw_store_name="ダミー",
                    raw_item_name="ダミー",
                    raw_price="1.0",
                    raw_purchase_date=raw_date,
                )
                self.assertEqual(
                    result.purchase_date,
                    expected_date,
                    f"日付 '{raw_date}' の正規化に失敗",
                )

        # 2. パース失敗時（不正な文字列）
        raw_date_fail = "購入日不明"
        result_fail: OCRResult = normalize_ocr_data(
            user_id=self.user_id,
            raw_store_name="ダミー",
            raw_item_name="ダミー",
            raw_price="1.0",
            raw_purchase_date=raw_date_fail,
        )
        self.assertEqual(
            result_fail.purchase_date,
            date.today(),
            "不正な日付は今日の日付になるべき",
        )

    # ----------------------------------------------------------------------
    # 新規追加：サジェスト機能のテスト
    # ----------------------------------------------------------------------

    def test_suggest_items_less_than_limit(self, mock_get_stores, mock_get_items):
        """
        既存商品が10件未満の場合、全てが類似度順に返されることを確認（件数チェック）
        """
        # クエリ '牛乳' に対して、既存リストの '牛乳 (1L)' が最も高スコアになることを期待
        query = "牛乳"

        suggestions: List[Item] = suggest_items(self.user_id, query)

        # 既存は3件なので、全てが返される
        self.assertEqual(len(suggestions), 3)

        # 類似度によるソートチェック: '牛乳 (1L)' が最も類似度が高いはず
        self.assertEqual(suggestions[0].name, "牛乳 (1L)")

    def test_suggest_items_more_than_limit(self, mock_get_stores, mock_get_items):
        """
        既存商品が10件より多い場合、類似度順の上位10件のみが返されることを確認（件数チェック）
        """
        # テスト用に15件のモックリストを作成
        MOCK_LARGE_ITEMS = [
            Item(id=i, name=f"Query Match Item {i:02d}", user_id=self.user_id)
            for i in range(1, 11)  # 10件（高類似度を意図）
        ] + [
            Item(id=i, name=f"Non Match Item {i:02d}", user_id=self.user_id)
            for i in range(11, 16)  # 5件（低類似度を意図）
        ]

        # このテストケースでのみモックを上書き
        with patch(
            "app.services.data_processor.db_manager.get_items_by_user",
            return_value=MOCK_LARGE_ITEMS,
        ):
            query = "Query Match"
            suggestions: List[Item] = suggest_items(self.user_id, query)

            # 上限の10件のみが返されるべき
            self.assertEqual(len(suggestions), 10)

            # 類似度チェック（オプション）：上位10件が意図したものであるか
            returned_names = [item.name for item in suggestions]

            # 高類似度の10件が全て含まれていることを確認
            expected_names = [f"Query Match Item {i:02d}" for i in range(1, 11)]
            self.assertTrue(all(name in returned_names for name in expected_names))

    def test_suggest_stores_less_than_limit(self, mock_get_stores, mock_get_items):
        """
        既存店舗が10件未満の場合、全てが類似度順に返されることを確認（件数チェック）
        """
        # クエリ 'イオン' に対して、既存リストの 'イオンモール' が最も高スコアになることを期待
        query = "イオン"

        suggestions: List[Store] = suggest_stores(self.user_id, query)

        # 既存は3件なので、全てが返される
        self.assertEqual(len(suggestions), 3)

        # 類似度によるソートチェック: 'イオンモール' が最も類似度が高いはず
        self.assertEqual(suggestions[0].name, "イオンモール")

    def test_suggest_stores_more_than_limit(self, mock_get_stores, mock_get_items):
        """
        既存店舗が10件より多い場合、類似度順の上位10件のみが返されることを確認（件数チェック）
        """
        # テスト用に15件のモックリストを作成
        MOCK_LARGE_STORES = [
            Store(id=i + 200, name=f"Query Match Store {i:02d}", user_id=self.user_id)
            for i in range(1, 11)  # 10件（高類似度を意図）
        ] + [
            Store(id=i + 200, name=f"Non Match Store {i:02d}", user_id=self.user_id)
            for i in range(11, 16)  # 5件（低類似度を意図）
        ]

        # このテストケースでのみモックを上書き
        with patch(
            "app.services.data_processor.db_manager.get_stores_by_user",
            return_value=MOCK_LARGE_STORES,
        ):
            query = "Query Match"
            suggestions: List[Store] = suggest_stores(self.user_id, query)

            # 上限の10件のみが返されるべき
            self.assertEqual(len(suggestions), 10)

            # 類似度チェック（オプション）：上位10件が意図したものであるか
            returned_names = [store.name for store in suggestions]

            # 高類似度の10件が全て含まれていることを確認
            expected_names = [f"Query Match Store {i:02d}" for i in range(1, 11)]
            self.assertTrue(all(name in returned_names for name in expected_names))
