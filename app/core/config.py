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
    # 🚨 環境変数として設定してください
    SUPABASE_URL: str
    SUPABASE_KEY: str # Anon Key
    # 🚨 SupabaseのSettings -> API -> Project JWT Secret にある値
    SUPABASE_JWT_SECRET: str # FastAPIがトークンを検証するために使用。
    
    class Config:
        # .envファイルから環境変数を読み込む設定
        env_file = ".env"

settings = Settings()