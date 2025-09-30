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
    
    # セキュリティ設定
    ACCESS_TOKEN_EXPIRE_MINUTES: ClassVar[int] = 60 * 24 * 8  # 8 days
    

    # Supabase / JWT Settings
    # 🚨 環境変数として設定してください
    SUPABASE_URL: str
    SUPABASE_KEY: str # Anon Key
    
    # 🚨 SupabaseのSettings -> API -> Project JWT Secret にある値
    # FastAPIがトークンを検証するために使用します。
    SUPABASE_JWT_SECRET: str
    
    class Config:
        # .envファイルから環境変数を読み込む設定
        env_file = ".env"

settings = Settings()



# .env ファイルの例:
# SUPABASE_URL=https://<your_project_ref>.supabase.co
# SUPABASE_KEY=eyJhbGciOi...
# SUPABASE_JWT_SECRET=eyJhbGciOi...