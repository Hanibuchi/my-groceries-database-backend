from fastapi import Depends, HTTPException, status
# 認証はSupabaseに委譲するが、トークン抽出のためにOAuth2PasswordBearerを使用
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
    
    try:
        # JWTを複合（SupabaseのシークレットキーとHS256アルゴリズムを使用）
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            # aud (Audience) の検証はSupabaseの動作に合わせて柔軟に設定
            options={"verify_signature": True, "verify_aud": False}
        )
        
        print(f"✅ Token DECODE SUCCESS! User UUID (sub): {payload.get('sub')}")
        
        # SupabaseのJWTペイロードからユーザーID（subクレーム）を抽出
        user_uuid = payload.get("sub") 
        if user_uuid is None:
            raise credentials_exception
            
    except (JWTError, ValidationError) as e:
        # トークンの期限切れ、署名エラー、Pydanticの検証エラーなど
        print(f"JWT Validation Error: {e}")
        raise credentials_exception
    
    # DBからユーザー情報を取得
    user = db_manager.get_user_by_uuid(user_uuid)
    
    if user is None:
        # DBに紐づくユーザーがいない（認証は通ったが、内部DBに未登録など）
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record not found in internal database."
        )
        
    return user