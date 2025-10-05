import os
from pydantic_settings import BaseSettings
from typing import ClassVar


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Shopper"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.0.0"

    # CORSオリジン設定
    BACKEND_CORS_ORIGINS: list[
        str
    ]  # 環境変数で設定。フロントのドメインとポートを設定する。
    UVICORN_HOST: str = "0.0.0.0"  # ここで空けておくホストを設定
    UVICORN_PORT: int = 8000  # これで空けておくポートを設定

    # ---- 環境変数 ----
    # Supabase / JWT Settings
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Anon Key

    # SupabaseのSettings -> API -> Project JWT Secret にある値
    SUPABASE_JWT_SECRET: str  # FastAPIがトークンを検証するために使用。
    # 追記: JWTの検証アルゴリズム (Supabaseは通常 HS256)
    JWT_ALGORITHM: str = "HS256"

    # OCR関係
    OCR_ENDPOINT: str
    OCR_KEY: str

    class Config:
        # .envファイルから環境変数を読み込む設定
        env_file = ".env"
        # 追記: 環境変数が必須であることを明示
        case_sensitive = True  #  (Pydanticの推奨設定)


settings = Settings()
