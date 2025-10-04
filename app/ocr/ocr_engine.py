# process_image 関数は、以下のキーを持つ辞書を要素とするリストを返してください。
# - 'store_name': str (レシート全体から抽出された店舗名。一つでOK)
# - 'item_name': str (商品名)
# - 'price': str (商品の単価または行の価格)
# - 'purchase_date': str (購入日付。必須ではないが、取得できれば格納)
#
# [例]
# raw_data_list = process_image(image_bytes)
# raw_data_list = [
#     {'store_name': 'イオンモール', 'item_name': '牛乳', 'price': '258.0', 'purchase_date': '2025/10/1'},
#     {'store_name': 'イオンモール', 'item_name': 'たまご 10個入', 'price': 320.0, 'purchase_date': '2025年 10月1日'},
#     ...
# ]
#
# 抽出データがない場合 (OCR失敗時) は、空のリスト [] を返してください。

import cv2
import os
import pytesseract
import re
import numpy as np
from PIL import Image
import datetime
import jaconv
from supabase import create_client, Client

pytesseract.pytesseract.tesseract_cmd = r"app\ocr\Tesseract-OCR\tesseract.exe"
os.environ['TESSDATA_PREFIX'] = r'app\ocr\Tesseract-OCR\tessdata'

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
    # img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # img = cv2.convertScaleAbs(img, alpha=1.2, beta=10)  # コントラスト・明るさ調整
    # img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    #                         cv2.THRESH_BINARY, 11, 2)
    # kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    # img = cv2.filter2D(img, -1, kernel)
    # img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return img

def extract_receipt_data(image_path):
    custom_config = r'--psm 6' ##この値変更すると読み取りデータかなり変わる レシートに対しては3か4か6がいいらしい
    img = preprocess_image(image_path)
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
    text = pytesseract.image_to_string(img_pil, lang="jpn", config=custom_config)

    # OCR結果のテキストを全角カナに変換
    # text = jaconv.h2z(text, kana=True, ascii=False, digit=False)

    # 店舗名抽出
    store_name = None
    for line in text.split("\n"):
        if "店" in line or "株式会社" in line:
            store_name = line.strip()
            break

        # 購入日抽出（スペース対応）
    purchase_date = None
    # 例: 2019 年 3 月 22 日, 2019/03/22, 2019-03-22 など
    date_patterns = [
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})"
    ]
    for pattern in date_patterns:
        m = re.search(pattern, text)
        if m:
            y, mth, d = m.groups()
            try:
                purchase_date = f"{y}/{int(mth):02d}/{int(d):02d}"
            except:
                purchase_date = None
            break

    # 商品リスト抽出
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    skip_words = ["割引", "値引", "小計", "合計", "お預り", "お釣り", "ポイント", "支払", "点", "クレジット", "春の大セール", "営業時間", "年", "月", "日", ":", "TEL", "消費税", "交通系", "QR", "ノ", "合-言十"]
    i = 0
    # ...existing code...

    while i < len(lines):
        line = lines[i]
        # 全角→半角変換＋スペース除去
        item_line_clean = jaconv.z2h(line.replace(" ", ""), kana=False, ascii=True, digit=True)
        # 除外ワードが含まれる行はスキップ
        if any(word in item_line_clean for word in skip_words):
            i += 1
            continue

        # パターン1: 商品名＋値段が同じ行（カンマ・スペース対応）
        m = re.match(r"(.+?)[¥\\]\s*([\d,]+)", line)
        if m:
            item_name_raw = m.group(1)
            # 全角→半角変換＋スペース除去＋商品コード除去
            item_name = re.sub(r"^\d+\s*", "", jaconv.z2h(item_name_raw.replace(" ", ""), kana=False, ascii=True, digit=True))
            price_str = m.group(2).replace(",", "")
            price_str = jaconv.z2h(price_str, kana=False, ascii=True, digit=True)
            if not any(word in item_name for word in skip_words):
                items.append({"商品": item_name, "値段": price_str})
            i += 1
            continue

        # パターン2: 商品名行の直後に値段だけの行
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            next_line_clean = jaconv.z2h(next_line.replace(" ", ""), kana=False, ascii=True, digit=True)
            m2 = re.match(r"[¥\\]\s*([\d,]+)", next_line)
            if m2 and not any(word in next_line_clean for word in skip_words):
                item_name_raw = item_line_clean
                item_name = re.sub(r"^\d+\s*", "", item_name_raw)
                price_str = m2.group(1).replace(",", "")
                price_str = jaconv.z2h(price_str, kana=False, ascii=True, digit=True)
                if not any(word in item_name for word in skip_words):
                    items.append({"商品": item_name, "値段": price_str})
                i += 2
                continue

        i += 1

# ...existing code...
    return {
        # "店舗名": store_name,
        "商品リスト": items,
        "購入日": purchase_date,
        "生テキスト": text
    }

if __name__ == "__main__":
    result = extract_receipt_data("app/ocr/receipt_sample.jpg")
    print("--- 抽出結果 ---")
    # print("店舗名:", result["店舗名"])
    print("購入日:", result["購入日"])
    print("商品リスト:")
    for item in result["商品リスト"]:
        print(f"  商品名: {item['商品']}, 値段: {item['値段']}円")
    print("\n--- OCR生テキスト ---")
    print(result["生テキスト"])

def process_image(image_bytes):
    # 一時ファイルに保存
    temp_path = "temp_receipt.jpg"
    with open(temp_path, "wb") as f:
        f.write(image_bytes)

    result = extract_receipt_data(temp_path)
    store_name = result.get("店舗名", None)
    purchase_date = result.get("購入日", None)
    items = result.get("商品リスト", [])

    raw_data_list = []
    for item in items:
        raw_data_list.append({
            "store_name": store_name,
            "item_name": item["商品"],
            "price": item["値段"],
            "purchase_date": purchase_date
        })

    # ファイル削除
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return raw_data_list



# --- 使用例 ---
with open("app/ocr/receipt_sample.jpg", "rb") as f:
    image_bytes = f.read()
raw_data_list = process_image(image_bytes)
print(raw_data_list)

# # SupabaseのURLとAPIキー
# url = "https://xxxx.supabase.co"
# key = "your_anon_public_api_key"
# supabase: Client = create_client(url, key)

# def save_items_to_supabase(items):
#     for item in items:
#         data = {
#             "item_name": item["商品"],
#             "price": item["値段"]
#         }
#         supabase.table("receipts").insert(data).execute()

# # 例: OCR結果のitemsリストを保存
# result = extract_receipt_data("receipt_sample.jpg")
# save_items_to_supabase(result["商品リスト"])


