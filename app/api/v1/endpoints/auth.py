from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.db.database import supabase  # Supabaseクライアントをインポート
from app.api.v1.schemas.user import Token  # トークン用のスキーマ

router = APIRouter()


@router.post("/token/test", response_model=Token)
def login_for_testing(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    【開発・テスト専用】
    ユーザー名（メール）とパスワードを受け取り、Supabaseにログインしてアクセストークンを返す。
    フロントエンドが完成するまでの、バックエンドチーム用の秘密の裏口。
    """
    try:
        # SupabaseのPythonライブラリを使って、ログイン処理を実行
        res = supabase.auth.sign_in_with_password(
            {
                "email": form_data.username,  # form_data.username にはemailが入る
                "password": form_data.password,
            }
        )

        # ログイン成功後、セッション情報からアクセストークンを取り出す
        access_token = res.session.access_token
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        # ログイン失敗時
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


### ステップ3：新しいAPIをアプリに接続する
# `main.py`（または`api/v1/__init__.py`）を編集して、今作った`auth.py`をアプリ全体に認識させます。

# python
# main.py など

# ... (他のimport文) ...
# from app.api.v1.endpoints import stores, receipts, users, items, auth  # auth を追加

# ... (app = FastAPI() など) ...

# 他のルーターと一緒に、auth.routerもアプリに含める
# app.include_router(auth.router, prefix="/api/v1", tags=["auth"])  # この行を追加
# ... (他のinclude_router) ...
