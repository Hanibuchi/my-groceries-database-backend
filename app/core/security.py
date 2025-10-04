from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.api.v1.schemas.user import User
# db_managerはもう不要になります
# from app.services import db_manager

# Supabaseクライアントをインポート
from supabase import create_client, Client

bearer_scheme = HTTPBearer()

# Supabaseクライアントを初期化
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# 🚨 Supabase JWT 検証と認可のメインロジック 🚨
def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    """
    リクエストヘッダーからJWTを取得し、Supabaseに問い合わせてユーザー情報を検証し、
    その情報から直接Userモデルを構築する。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (Token invalid or expired)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    try:
        # Supabaseに「このトークンは本物ですか？」と直接問い合わせる
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise credentials_exception

        auth_user = user_response.user
        
        # ▼▼▼【最重要修正】内部DBを見に行かず、Supabaseの応答から直接Userを構築▼▼▼
        # これで、public.usersテーブルが不要になります。
        user = User(
            id=str(auth_user.id),
            email=auth_user.email,
            username=auth_user.user_metadata.get("username", auth_user.email),
            is_active=True
        )
        return user
            
    except Exception as e:
        # Supabaseからの応答がエラーだった場合など
        print(f"Supabase Token Validation Error: {e}")
        raise credentials_exception