# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "transactions_db"
    POSTGRES_HOST: str = "localhost" # Added host so we can switch between 'db' and 'localhost'
    POSTGRES_PORT: str = "5432"

    DATABASE_URL: str = None # init

    class Config:
        env_file = ".env"

    def get_database_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

