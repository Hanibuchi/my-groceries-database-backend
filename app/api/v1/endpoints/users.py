from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from supabase_auth.errors import AuthApiError

# Supabaseクライアントのインポート
from supabase import create_client, Client

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import User, UserLogin, AuthResponse
from app.core.config import settings  # Supabaseのクレデンシャルを取得するために必要
from app.core.security import get_current_active_user
from app.services import db_manager  # 内部DBとの連携に必要

router = APIRouter(prefix="/users", tags=["Users"])

# Supabaseクライアントの初期化
# 環境変数からクレデンシャルを取得し、Supabaseクライアントを初期化
SUPABASE_URL: str = settings.SUPABASE_URL
# 認証にはセキュリティリスクの低いANONキーを使用します
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
    user_in: UserLogin,  # 登録時もemailとpasswordを受け取るためUserLoginを使用
) -> Any:
    """
    ユーザーをSupabase Authに登録し、成功したら内部DBにレコードを作成する。
    """
    try:
        # 1. Supabase Authにユーザーを登録（メール確認ステップがある可能性あり）
        auth_response = supabase.auth.sign_up(
            email=user_in.email, password=user_in.password
        )

        user_uuid = auth_response.user.id

        # 2. 内部DBにユーザーのレコードを作成 (この部分はdb_managerに実装が必要です)
        # 例：internal_user = db_manager.create_user_internal(user_uuid=user_uuid, email=user_in.email)

        # 要実装: 内部DBへの登録ロジック
        # ユーザーに紐づく内部IDや初期設定を保存するため
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Registration is successful on Supabase, but internal DB creation logic (db_manager.create_user_internal) is missing.",
        )

        # return internal_user # 内部DBのユーザー情報を返す

    except AuthApiError as e:
        # ユーザーがすでに存在する場合など
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {e.message}",
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
        # 1. Supabase Authにサインインリクエストを送信
        auth_response = supabase.auth.sign_in_with_password(
            {
                "email": user_in.email,
                "password": user_in.password,
            }
        )

        # 2. Supabaseの応答から、必要な情報を抽出
        token = auth_response.session.access_token
        user_uuid = auth_response.user.id

    except AuthApiError:
        # 認証失敗（メールアドレスまたはパスワードが不正）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # その他のエラー（ネットワーク、Supabase応答構造の異常など）
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token from Supabase.",
        )

    # 3. 認証が成功したら、内部DBからユーザー情報を取得
    # このUserオブジェクトが、AuthResponseの 'user' フィールドに格納されます
    internal_user = db_manager.get_user_by_uuid(user_uuid)

    if not internal_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User authentication succeeded but user record not found in internal database.",
        )

    # 4. クライアントに返却するAuthResponseを構成
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=auth_response.session.expires_in,
        user=internal_user,
    )


# 3. 認証済みユーザー情報取得 (既存のエンドポイント)


@router.get("/me", response_model=User, summary="認証済みユーザー情報の取得")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """現在ログインしているユーザーの情報を取得する"""
    return current_user
