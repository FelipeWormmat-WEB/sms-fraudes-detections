import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL"))
    CLASSIFICATION_URL: str = Field(default=os.getenv("CLASSIFICATION_URL", "http://classification-service:8080"))
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "change-in-production"))

settings = Settings()
