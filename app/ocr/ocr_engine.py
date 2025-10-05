import requests
import time
import json
import re
from dotenv import dotenv_values
import os

from app.core.config import settings

endpoint = settings.OCR_ENDPOINT
key = settings.OCR_KEY

def azure_receipt_ocr(image_path):
    url = (
        endpoint
        + "formrecognizer/documentModels/prebuilt-receipt:analyze?api-version=2023-07-31"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/octet-stream",
    }
    with open(image_path, "rb") as f:
        img_data = f.read()
    response = requests.post(url, headers=headers, data=img_data)
    response.raise_for_status()
    result_url = response.headers.get("operation-location")
    if not result_url:
        print("operation-location ヘッダーがありません。")
        return {}

    for _ in range(20):
        result_response = requests.get(
            result_url, headers={"Ocp-Apim-Subscription-Key": key}
        )
        result_json = result_response.json()
        status = result_json.get("status")
        if status == "succeeded":
            return result_json
        elif status == "failed":
            print("解析失敗")
            return {}
        time.sleep(1)
    print("タイムアウト")
    return {}


def parse_receipt_result(result_json):
    # 生データ（全文テキスト）
    raw_text = ""
    for page in result_json.get("analyzeResult", {}).get("pages", []):
        for line in page.get("lines", []):
            raw_text += line.get("content", "") + "\n"

    receipts = result_json.get("analyzeResult", {}).get("documents", [])
    if not receipts:
        print("レシートデータが検出されませんでした。")
        return {}

    data = receipts[0].get("fields", {})
    store_name = data.get("MerchantName", {}).get("valueString")
    transaction_date = data.get("TransactionDate", {}).get("valueDate")

    # 合計金額
    total_data = data.get("Total", {})
    currency = total_data.get("valueCurrency")
    amount = total_data.get("valueAmount")
    if amount is not None:
        if currency:
            total = f"{currency} {amount}"
        else:
            total = str(amount)
    else:
        total = None

    # 商品リスト
    items_data = data.get("Items", {}).get("valueArray", [])
    items = []
    for item in items_data:
        fields = item.get("valueObject", {})
        name = fields.get("Description", {}).get("valueString")
        price = fields.get("TotalPrice", {}).get("valueAmount")
        if name and price is not None:
            items.append({"商品名": name, "価格": price})

    return {
        "生データ": raw_text,
        "店舗名": store_name,
        "購入日": transaction_date,
        "合計": total,
        "商品リスト": items,
    }


def clean_item_name(item_name):
    # 商品名の先頭に「数字＋スペース」があれば除去（例: "1100 大根" → "大根"）
    item_name = re.sub(r"^\d+\s*", "", item_name)
    # 「内*」「内」も除去
    item_name = re.sub(r"^内\*?", "", item_name)
    return item_name


def parse_receipt_text(text):
    # 購入日抽出
    purchase_date = None
    date_patterns = [
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})",
    ]
    for pattern in date_patterns:
        m = re.search(pattern, text)
        if m:
            y, mth, d = m.groups()
            purchase_date = f"{y}/{int(mth):02d}/{int(d):02d}"
            break

    items = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    skip_words = [
        "値引",
        "割引",
        "小計",
        "合計",
        "計",
        "お預り",
        "お釣り",
        "ポイント",
        "支払",
        "点",
        "クレジット",
        "春の大セール",
        "営業時間",
        "年",
        "月",
        "日",
        ":",
        "TEL",
        "消費税",
        "交通系",
        "QR",
        "ノ",
        "合-言十",
        "-",
        "%",
        "代金",
        "個",
        "内税",
        "¥",
        "税",
        "レシート",
        "領収書",
        "お買上げ",
        "ありがとうございました",
        "またのご来店をお待ちしております",
        "本日のお買上げ",
        "ありがとうございました",
        "またお越しくださいませ",
        "またのご来店をお待ちしております",
        "お買い上げありがとうございました",
        "またのご来店を心よりお待ちしております",
        "食品等の返品はお受け致しかねます",
        "ご理解をお願いいたします",
        "ご来店ありがとうございます",
    ]
    i = 0
    while i < len(lines):
        line = lines[i]
        # 商品名＋値段が同じ行
        m_inline = re.match(r"(.+?)\s*[¥\\]\s*([\d,]+)", line)
        if m_inline:
            item_name = m_inline.group(1).strip()
            item_name = item_name.split("(")[0].strip()
            item_name = clean_item_name(item_name)
            price = m_inline.group(2).replace(",", "")
            if (
                not any(x in item_name for x in skip_words)
                and re.search(r"\D", item_name)
                and not re.match(r"^[¥\\\d,]+$", item_name)
                and len(item_name) < 20
            ):
                items.append(
                    {
                        "store_name": None,
                        "item_name": item_name,
                        "price": price,
                        "purchase_date": purchase_date or "",
                    }
                )
            i += 1
            continue

        # 値段だけの行→直前の行を商品名として扱う
        m_price = re.match(r"^¥\s*([\d,]+)", line)
        if m_price and i > 0:
            item_name = lines[i - 1].strip()
            item_name = item_name.split("(")[0].strip()
            item_name = clean_item_name(item_name)
            price = m_price.group(1).replace(",", "")
            if (
                not any(x in item_name for x in skip_words)
                and re.search(r"\D", item_name)
                and not re.match(r"^[¥\\\d,]+$", item_name)
                and len(item_name) < 20
            ):
                items.append(
                    {
                        "store_name": None,
                        "item_name": item_name,
                        "price": price,
                        "purchase_date": purchase_date or "",
                    }
                )
        i += 1
    return items


def process_image(image_path):
    """
    入力画像パスを受け取り、商品リストを抽出して返す関数
    """
    result_json = azure_receipt_ocr(image_path)
    result = parse_receipt_result(result_json)
    raw_data_list = parse_receipt_text(result.get("生データ", ""))
    return raw_data_list


# 使い方例
if __name__ == "__main__":
    items = process_image("app/ocr/receipt_sample.jpg")
    for d in items:
        print(d)
