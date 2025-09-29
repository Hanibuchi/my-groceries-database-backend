# auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# 自身のプロジェクトからインポート
from app.api.v1.schemas.user import Token, UserCreate, User
from app.core.config import settings
from app.core.security import create_access_token
from app.services import db_manager # DB操作を扱うサービス
from app.core import security # 認証ロジック

router = APIRouter(prefix="/auth", tags=["Auth"])

# ユーザー登録エンドポイント
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    """新規ユーザーを登録し、ハッシュ化されたパスワードを保存する"""
    # ユーザー名またはメールアドレスの重複チェック（db_managerで実施）
    if db_manager.get_user_by_email(user_in.email) or db_manager.get_user_by_username(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered."
        )
        
    # パスワードをハッシュ化してDBに保存
    db_user = db_manager.create_user(user_in) 
    return db_user

# トークン発行（ログイン）エンドポイント
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """ユーザー名とパスワードを受け取り、アクセストークンを返す"""
    user = security.authenticate_user(db_manager.get_user_by_username(form_data.username), form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # トークン有効期限の設定
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # トークンの作成
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}