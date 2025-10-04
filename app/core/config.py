import os
from pydantic_settings import BaseSettings
from typing import ClassVar


class Settings(BaseSettings):
    PROJECT_NAME: str = "My Groceries Database"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.0.0"

    # CORSオリジン設定
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8000

    # Supabase / JWT Settings
    # 環境変数として設定
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Anon Key
    # SupabaseのSettings -> API -> Project JWT Secret にある値
    SUPABASE_JWT_SECRET: str  # FastAPIがトークンを検証するために使用。

    # 追記: JWTの検証アルゴリズム (Supabaseは通常 HS256)
    JWT_ALGORITHM: str = "HS256"  # <- 追記

    # OCR関係
    OCR_ENDPOINT: str
    OCR_KEY: str

    class Config:
        # .envファイルから環境変数を読み込む設定
        env_file = ".env"
        # 追記: 環境変数が必須であることを明示
        case_sensitive = True  # <- 追記 (Pydanticの推奨設定)


settings = Settings()
