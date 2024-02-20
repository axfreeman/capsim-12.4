from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """
    Subclass the pydantic BaseSettings class by adding
    the secret environment variables that we need.

    TODO pydocs doesn't like this
    """
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    sqlalchemy_database_url: str

    class Config:
        env_file = ".env"

settings = Settings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
