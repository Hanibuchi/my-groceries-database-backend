import pytest
from datetime import date
from app.api.v1.schemas.item import ItemCreate
from app.api.v1.schemas.store import StoreCreate
from app.api.v1.schemas.record import RecordCreate
from app.db import database

# 🚨 実際には、テスト用の設定を読み込むための準備が必要です。
# 例: 環境変数を設定、またはテストフィクスチャでconfigをモックする。

# 🚨 環境依存の注意:
# 以下のテストを実行するには、database.pyが正しくSupabaseに接続できる状態である必要があります。
# また、テスト用に確保したユーザーID (UUID) が必要です。

TEST_USER_ID = "f405c50e-824a-4508-9218-571bba692713"  # 実際のUUIDに置き換えること
# 例: TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


# テスト実行前に、関連するテストデータをすべてクリーンアップする関数
def cleanup_test_data(user_id: str):
    """テスト用に作成されたデータを削除（冪等性の確保）"""
    # 履歴を削除
    database.supabase.table("purchases").delete().eq("user_id", user_id).execute()
    # 商品を削除
    database.supabase.table("items").delete().eq("user_id", user_id).execute()
    # 店舗を削除
    database.supabase.table("stores").delete().eq("user_id", user_id).execute()


# 各テストの開始前にクリーンアップを実行するフィクスチャ
@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """モジュール実行前後にデータをクリーンアップ"""
    cleanup_test_data(TEST_USER_ID)
    yield
    cleanup_test_data(TEST_USER_ID)


def test_item_crud_and_search():
    """商品の作成、取得、更新、検索、削除のフローをテスト"""

    # 1. 作成 (Create)
    item_in = ItemCreate(name="牛乳")
    created_item = database.create_item(TEST_USER_ID, item_in)
    assert created_item.name == "牛乳"
    assert created_item.user_id == TEST_USER_ID
    assert isinstance(created_item.id, int)

    item_id = created_item.id

    # 2. 取得 (Read by name) - 名寄せ用
    fetched_item = database.get_item_by_name_and_user(TEST_USER_ID, "牛乳")
    assert fetched_item.id == item_id

    # 3. 検索 (Search) - サジェスト用
    search_results = database.search_items_by_partial_name(TEST_USER_ID, "牛")
    assert len(search_results) == 1
    assert search_results[0].name == "牛乳"

    # 4. 更新 (Update)
    update_in = ItemCreate(name="特濃牛乳")
    updated_item = database.update_item(TEST_USER_ID, item_id, update_in)
    assert updated_item.name == "特濃牛乳"

    # 5. 削除 (Delete) - クリーンアップフィクスチャがあるため、ここでは成功確認のみ
    success = database.delete_item(TEST_USER_ID, item_id)
    assert success

    # 削除後の確認
    fetched_item_after_delete = database.get_item_by_name_and_user(
        TEST_USER_ID, "特濃牛乳"
    )
    assert fetched_item_after_delete is None


def test_store_create_and_read():
    """店舗の作成と取得をテスト"""

    store_in = StoreCreate(name="スーパーA")
    created_store = database.create_store(TEST_USER_ID, store_in)
    assert created_store.name == "スーパーA"

    fetched_store = database.get_store_by_name_and_user(TEST_USER_ID, "スーパーA")
    assert fetched_store.id == created_store.id


def test_record_create_and_price_comparison():
    """購入履歴の登録と価格比較機能の動作をテスト"""

    # 1. 依存データ（商品、店舗）の作成
    item_in = ItemCreate(name="パン")
    item = database.create_item(TEST_USER_ID, item_in)
    store_a_in = StoreCreate(name="スーパーA")
    store_b_in = StoreCreate(name="ディスカウントB")
    store_a = database.create_store(TEST_USER_ID, store_a_in)
    store_b = database.create_store(TEST_USER_ID, store_b_in)

    # 2. 履歴の作成
    # スーパーA: 100円
    record_a_in = RecordCreate(
        raw_item_name="食パン",
        raw_store_name="A",
        raw_price="100",
        raw_purchase_date="2024-01-01",
        item_id=item.id,
        store_id=store_a.id,
        final_price=100.0,
        final_purchase_date=date(2024, 1, 1).isoformat(),
    )
    record_a = database.create_purchase_record(TEST_USER_ID, record_a_in)
    assert record_a.price == 100.0

    # スーパーA: 120円 (平均: 110円)
    record_a_2_in = RecordCreate(
        raw_item_name="食パン",
        raw_store_name="A",
        raw_price="120",
        raw_purchase_date="2024-01-10",
        item_id=item.id,
        store_id=store_a.id,
        final_price=120.0,
        final_purchase_date=date(2024, 1, 10).isoformat(),
    )
    database.create_purchase_record(TEST_USER_ID, record_a_2_in)

    # ディスカウントB: 90円
    record_b_in = RecordCreate(
        raw_item_name="食パン",
        raw_store_name="B",
        raw_price="90",
        raw_purchase_date="2024-01-05",
        item_id=item.id,
        store_id=store_b.id,
        final_price=90.0,
        final_purchase_date=date(2024, 1, 5),
    )
    database.create_purchase_record(TEST_USER_ID, record_b_in)

    # 3. 履歴リスト取得のテスト
    all_records = database.get_records_by_item_id(TEST_USER_ID, item.id)
    assert len(all_records) == 3
    # JOINによる名称取得の確認
    assert all_records[0].item_name == "パン"
    assert all_records[0].store_name in ["スーパーA", "ディスカウントB"]
