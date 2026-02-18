# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict 
from typing import Optional

class Settings(BaseSettings):
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "transactions_db"
    POSTGRES_HOST: str = "localhost" # Added host so I can switch between 'db' and 'localhost'
    POSTGRES_PORT: str = "5432"

    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env")

    def get_database_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

