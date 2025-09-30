# tests/utils.py

from jose import jwt

from app.core.config import settings
from tests.conftest import TEST_USER_UUID # 上記で定義したUUID

def create_mock_jwt(user_uuid: str = TEST_USER_UUID, secret: str = settings.SUPABASE_JWT_SECRET) -> str:
    """
    テスト用のJWTを生成する
    Supabaseのクレーム構造を模倣 (subにUUIDを格納)
    """
    # 期限切れでない適当なpayload
    to_encode = {"sub": user_uuid, "exp": 9999999999} 
    encoded_jwt = jwt.encode(
        to_encode, 
        secret, 
        algorithm="HS256"
    )
    return encoded_jwt