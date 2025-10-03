# process_image 関数は、以下のキーを持つ辞書を要素とするリストを返してください。
# - 'store_name': str (レシート全体から抽出された店舗名。一つでOK)
# - 'item_name': str (商品名)
# - 'price': float (商品の単価または行の価格)
# - 'purchase_date': datetime.date (購入日付。必須ではないが、取得できれば格納)
#
# [例]
# raw_data_list = process_image(image_bytes)
# raw_data_list = [
#     {'store_name': 'イオンモール', 'item_name': '牛乳', 'price': 258.0, 'purchase_date': '2025/10/1'},
#     {'store_name': 'イオンモール', 'item_name': 'たまご 10個入', 'price': 320.0, 'purchase_date': '2025年 10月1日'},
#     ...
# ]
#
# 抽出データがない場合 (OCR失敗時) は、空のリスト [] を返してください。


def process_image(image_bytes: bytes):
    # ... 実際のOCRロジック ...
    return []
