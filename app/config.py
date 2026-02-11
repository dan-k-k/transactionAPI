# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Default to Local Postgres credentials
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "transactions_db"
    # Construct the URL automatically or allow override
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()

