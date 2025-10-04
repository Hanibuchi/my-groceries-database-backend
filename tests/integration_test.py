# import requests
# import json
# from datetime import date

# # 🚨 環境設定 🚨
# BASE_URL = "http://127.0.0.1:8000/v1"  # FastAPIのベースURL
# TEST_EMAIL = "test_user@example.com"  # 既存のテストユーザー
# TEST_PASSWORD = "testpassword"  # テストユーザーのパスワード

# # 実際には適当な画像ファイルを用意してください
# # 動作確認のため、ここではプレースホルダーとして使用します。
# RECEIPT_FILE_PATH = "sample_receipt.jpg"


# def create_sample_receipt_image():
#     """テスト用のダミー画像ファイルを生成（実際にはレシート画像を用意）"""
#     print(f"[{RECEIPT_FILE_PATH}]という名前のダミーファイルを作成します。")
#     try:
#         with open(RECEIPT_FILE_PATH, "wb") as f:
#             # 非常に小さなダミーのJPEGヘッダー
#             f.write(
#                 b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
#             )
#         print(f"ファイル [{RECEIPT_FILE_PATH}] が作成されました。")
#     except Exception as e:
#         print(f"ダミーファイルの作成に失敗しました: {e}")
#         return False
#     return True


# # ----------------------------------------------------


# def run_test_flow():
#     """主要なAPIエンドポイントを順に叩いて動作を確認する"""
#     print("--- 1. ユーザーログイン ---")

#     # ログイン
#     login_url = f"{BASE_URL}/users/login"
#     login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}

#     try:
#         response = requests.post(login_url, json=login_data)
#         response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
#         auth_data = response.json()
#         access_token = auth_data["access_token"]
#         print(f"✅ ログイン成功。トークン取得。 (UUID: {auth_data['user']['id']})")

#     except requests.exceptions.HTTPError as e:
#         print(
#             f"❌ ログイン失敗: {e.response.status_code} - {e.response.json().get('detail', '詳細不明')}"
#         )
#         print("💡 ユーザー登録（/users/）がまだ未実装の場合、このエラーは正常です。")
#         print(
#             "💡 Supabaseでテストユーザーを事前に作成するか、'/users/'エンドポイントを先に実装してください。"
#         )
#         return
#     except requests.exceptions.RequestException as e:
#         print(f"❌ リクエストエラー: {e}")
#         print("💡 FastAPIサーバーが起動しているか確認してください。")
#         return

#     # ヘッダー設定
#     headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

#     print("\n--- 2. レシート画像アップロードとOCR/正規化の提案 ---")

#     # ダミーファイルの作成
#     if not create_sample_receipt_image():
#         return

#     # レシートアップロード (OCRシミュレーション)
#     upload_url = f"{BASE_URL}/receipts/upload"
#     try:
#         # filesとして画像を送信
#         with open(RECEIPT_FILE_PATH, "rb") as f:
#             files = {"file": (RECEIPT_FILE_PATH, f, "image/jpeg")}
#             response = requests.post(upload_url, headers=headers, files=files)
#             response.raise_for_status()
#             ocr_results = response.json()

#         print(
#             f"✅ OCR/正規化提案取得成功。{len(ocr_results)}件の商品データを抽出しました。"
#         )

#         if not ocr_results:
#             print("⚠️ 抽出された商品データが0件でした。テストを終了します。")
#             return

#         # 最初の商品の提案情報を取得（ここではデータ構造の確認のみ）
#         first_item_ocr_result = ocr_results[0]
#         print(
#             f"   - 1件目の商品: RAW: {first_item_ocr_result['raw_item_name']} | 提案ID: {first_item_ocr_result['suggested_item_id']} | 価格: {first_item_ocr_result['price']}"
#         )

#     except requests.exceptions.HTTPError as e:
#         print(
#             f"❌ OCR/アップロード失敗: {e.response.status_code} - {e.response.json().get('detail', '詳細不明')}"
#         )
#         print(
#             "💡 `process_image` (ocr/ocr_engine.py) と `normalize_ocr_data` (services/data_processor.py) のモック実装が必要です。"
#         )
#         return
#     except requests.exceptions.RequestException as e:
#         print(f"❌ リクエストエラー: {e}")
#         return

#     print("\n--- 3. OCR結果の確定と購入履歴の登録 ---")

#     # 提案されたデータ構造から、確定データ (RecordCreate) を作成
#     # 実際のフロントエンドでは、ユーザーがここで修正や確定を行う
#     item_to_register = first_item_ocr_result

#     # item_idとstore_idがNoneの場合、新規登録処理が内部で走る想定だが、
#     # ここではテストのため、成功したと仮定して適当なID（例: 1, 1）を設定
#     # 💡 実際には、`data_processor.normalize_ocr_data`が
#     #    新規登録が必要な場合は新規IDを返し、不要なら既存IDを返すロジックが必要です。
#     record_create_data = {
#         "raw_item_name": item_to_register["raw_item_name"],
#         "raw_store_name": item_to_register["raw_store_name"],
#         "raw_price": item_to_register["raw_price"],
#         "raw_purchase_date": str(date.today()),
#         "item_id": item_to_register.get("suggested_item_id", 1),  # 仮のID
#         "store_id": item_to_register.get("suggested_store_id", 1),  # 仮のID
#         "price": item_to_register["price"],
#         "purchase_date": str(date.today()),
#     }

#     confirm_url = f"{BASE_URL}/receipts/confirm"
#     try:
#         # RecordCreateスキーマを送信
#         response = requests.post(confirm_url, headers=headers, json=record_create_data)
#         response.raise_for_status()
#         registered_record = response.json()

#         registered_item_id = registered_record["item_id"]
#         print(
#             f"✅ 購入履歴登録成功。 (Record ID: {registered_record['id']}, Item ID: {registered_item_id})"
#         )

#     except requests.exceptions.HTTPError as e:
#         print(
#             f"❌ 履歴登録失敗: {e.response.status_code} - {e.response.json().get('detail', '詳細不明')}"
#         )
#         print("💡 `db_manager.create_purchase_record` の実装を確認してください。")
#         return
#     except requests.requests.RequestException as e:
#         print(f"❌ リクエストエラー: {e}")
#         return

#     print("\n--- 4. 価格比較機能の確認 (特定の商品の平均価格) ---")

#     # 3で登録した商品のIDを使用して価格比較を取得
#     compare_url = f"{BASE_URL}/items/{registered_item_id}/compare"

#     try:
#         response = requests.get(compare_url, headers=headers)
#         response.raise_for_status()
#         comparison_data = response.json()

#         print(
#             f"✅ 価格比較データ取得成功。{len(comparison_data)}件の店舗データを確認。"
#         )
#         if comparison_data:
#             first_comparison = comparison_data[0]
#             print(
#                 f"   - 店舗名: {first_comparison['store_name']} | 平均価格: {first_comparison['average_price']} | 全体平均: {first_comparison['overall_average_price']}"
#             )

#     except requests.exceptions.HTTPError as e:
#         print(
#             f"❌ 価格比較失敗: {e.response.status_code} - {e.response.json().get('detail', '詳細不明')}"
#         )
#         print(
#             "💡 `db_manager.get_item_price_comparisons` の実装を確認してください。特に集計ロジック。"
#         )
#         return
#     except requests.requests.RequestException as e:
#         print(f"❌ リクエストエラー: {e}")
#         return

#     print("\n--- テストフロー完了 ---")


# if __name__ == "__main__":
#     run_test_flow()
