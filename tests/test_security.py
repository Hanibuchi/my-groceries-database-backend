# tests/test_security.py

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from starlette import status

from app.api.v1.schemas.user import User
from tests.conftest import MOCK_USER, TEST_USER_UUID
from tests.utils import create_mock_jwt # 作成したJWTヘルパー関数

# 💡 MOCK_DB_MANAGERを定義: db_manager.get_user_by_uuid をモック化するために使用
MOCK_DB_MANAGER = 'app.core.security.db_manager' 

def test_read_users_me_success(client: TestClient):
    """有効なJWTで /users/me にアクセスし、ユーザー情報が取得できるか"""
    
    # 1. 有効なJWTを生成
    valid_token = create_mock_jwt(user_uuid=TEST_USER_UUID)
    headers = {"Authorization": f"Bearer {valid_token}"}

    # 2. get_user_by_uuid をモック化し、MOCK_USERを返すように設定
    with patch(f'{MOCK_DB_MANAGER}.get_user_by_uuid', return_value=MOCK_USER) as mock_db_call:
        response = client.get("/api/v1/users/me", headers=headers)

    # 3. 検証
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == MOCK_USER.username
    # DBコールがJWTから抽出されたUUIDで正しく呼ばれたかを確認
    mock_db_call.assert_called_once_with(TEST_USER_UUID)

def test_read_users_me_no_token(client: TestClient):
    """トークンなしでアクセスし、401 Unauthorizedになるか"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]

def test_read_users_me_invalid_token_signature(client: TestClient):
    """署名が不正なトークンでアクセスし、401 Unauthorizedになるか"""
    # 秘密鍵を間違えて生成したトークンをシミュレート
    invalid_token = create_mock_jwt(secret="WRONG_SECRET_KEY") 
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    # DBコールはJWT検証エラーより先に実行されないため、モックは不要
    response = client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]


def test_read_users_me_user_not_found_in_db(client: TestClient):
    """JWTは有効だが、内部DBにユーザー情報が存在しない場合に404になるか"""
    valid_token = create_mock_jwt(user_uuid="00000000-0000-0000-0000-000000000002") # 別ユーザーUUID

    with patch(f'{MOCK_DB_MANAGER}.get_user_by_uuid', return_value=None):
        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {valid_token}"})
        
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User record not found in internal database." in response.json()["detail"]