
import sys
import os

# テスト実行時にプロジェクトのルートディレクトリをパスに追加
# これにより、`app` パッケージのインポートが可能になる
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# tests/conftest.py (pytestのフィクスチャファイル)

from typing import Generator
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app # アプリケーションのエントリポイント
from app.api.v1.schemas.user import User

# テストで使うモックユーザー情報
TEST_USER_UUID = "00000000-0000-0000-0000-000000000001"
MOCK_USER = User(
    id=TEST_USER_UUID,
    username="testuser",
    email="test@example.com",
    is_active=True
)

@pytest.fixture(scope="module")
def client() -> Generator:
    """FastAPIテストクライアント"""
    with TestClient(app) as c:
        yield c