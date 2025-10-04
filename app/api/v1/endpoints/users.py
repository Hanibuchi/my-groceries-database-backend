from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
# AuthApiErrorの正しいインポート先
from gotrue.errors import AuthApiError

# Supabaseの同期クライアントをインポート
from supabase import create_client, Client

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User, UserLogin, AuthResponse
from app.core.config import settings
from app.core.security import get_current_active_user
from app.services import db_manager

router = APIRouter(prefix="/users", tags=["Users"])

# Supabaseの同期クライアントを初期化
SUPABASE_URL: str = settings.SUPABASE_URL
SUPABASE_KEY: str = settings.SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. 新規ユーザー登録


@router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="新規ユーザー登録",
)
def register_user(
    # ▼▼▼【最重要修正】UserCreateではなく、UserLoginを受け取るように変更 ▼▼▼
    # これで、emailとpasswordだけで登録できるようになります。
    user_in: UserLogin,
) -> Any:
    """
    ユーザーをSupabase Authに登録し、その情報を直接返す。
    """
    try:
        # 1. Supabase Authにユーザーを登録
        auth_response = supabase.auth.sign_up(
            {"email": user_in.email, "password": user_in.password}
        )

        auth_user = auth_response.user
        if not auth_user or not auth_user.id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user info from Supabase after sign up.",
            )

        # public.usersテーブルは使わず、Supabaseからの応答を直接返す
        # usernameは一旦emailと同じものを設定します
        return User(
            id=str(auth_user.id),
            email=auth_user.email,
            username=auth_user.email, # usernameは必須なので、emailを仮で設定
            is_active=True,
        )

    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {e.message}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


# 2. ログイン (Token Issuance)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="ユーザーログインとアクセストークン取得",
)
def user_login(user_in: UserLogin) -> Any:
    """
    Supabaseで認証を行い、成功した場合にアクセストークンとユーザー情報を返す。
    """
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {"email": user_in.email, "password": user_in.password}
        )

        if not auth_response.session or not auth_response.session.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login failed, no session returned.",
            )

        token = auth_response.session.access_token
        auth_user = auth_response.user

        if not auth_user:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Login succeeded but could not retrieve user details from Supabase.",
            )

    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve token from Supabase: {str(e)}",
        )

    # public.usersテーブルは使わない
    user_details = User(
        id=str(auth_user.id),
        email=auth_user.email,
        username=auth_user.user_metadata.get("username", auth_user.email),
        is_active=True
    )
    
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=auth_response.session.expires_in,
        user=user_details,
    )


# 3. 認証済みユーザー情報取得 (既存のエンドポイント)


@router.get("/me", response_model=User, summary="認証済みユーザー情報の取得")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """現在ログインしているユーザーの情報を取得する"""
    return current_user

