class Settings:
    PROJECT_NAME: str = "My Groceries Database"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.0.0"
    
    # CORSオリジン設定
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8000
    
    # セキュリティ設定
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8  # 8 days

settings = Settings()

