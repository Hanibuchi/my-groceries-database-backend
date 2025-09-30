from typing import Optional

from fastapi import Depends, HTTPException, status
# ユーザー認証がフロントエンドとSupabaseで完結するため、OAuth2PasswordBearerの代わりにOAuth2BearerTokenを使用
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.api.v1.schemas.user import User # 認証済みユーザーのレスポンスモデル
from app.services import db_manager # DB操作サービスをインポート

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scheme_name="JWT"
)

# 🚨 Supabase JWT 検証と認可のメインロジック 🚨
async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    リクエストヘッダーからJWTを取得し、検証、ユーザーUUIDを抽出し、DBからユーザー情報を取得する
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (Token invalid or expired)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # ⚠️ 既存のUserスキーマのIDはintですが、SupabaseのユーザーIDはUUID(str)です。
    # ここでは、DBマネージャがUUIDを受け取れる、またはDBにUUIDフィールドがあることを前提とします。
    
    try:
        # JWTを複合（SupabaseのシークレットキーとHS256アルゴリズムを使用）
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            # aud (Audience) の検証はSupabaseの動作に合わせて柔軟に設定
            options={"verify_signature": True, "verify_aud": False}
        )
        
        # SupabaseのJWTペイロードからユーザーID（subクレーム）を抽出
        user_uuid: str = payload.get("sub") 
        if user_uuid is None:
            raise credentials_exception
            
    except (JWTError, ValidationError) as e:
        # トークンの期限切れ、署名エラー、Pydanticの検証エラーなど
        print(f"JWT Validation Error: {e}")
        raise credentials_exception
    
    # DBからユーザー情報を取得
    # 🚨 db_managerにUUIDで検索する関数が必要です 🚨
    # ハッカソンでは、内部ユーザーテーブルの外部キーとしてUUIDを持つのがシンプルです
    user = db_manager.get_user_by_uuid(user_uuid)
    
    if user is None:
        # DBに紐づくユーザーがいない（認証は通ったが、内部DBに未登録など）
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record not found in internal database."
        )
        
    return user

# 🚨 以下のローカル認証ロジックは全て削除されます 🚨
# def verify_password(...): ... (削除)
# def get_password_hash(...): ... (削除)
# def create_access_token(...): ... (削除)
# def authenticate_user(...): ... (削除)
# def change_user_password(...): ... (削除)