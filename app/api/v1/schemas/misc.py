# misc.py
from pydantic import BaseModel
from typing import Any

# 一般的なメッセージ応答（エラー、成功通知など）
class Message(BaseModel):
    """一般的なメッセージ応答用"""
    message: str

# データエクスポート機能（レスポンス）
class DataExport(BaseModel):
    """エクスポートされたCSVデータの情報"""
    filename: str
    # ダウンロードURLなど
    download_url: str