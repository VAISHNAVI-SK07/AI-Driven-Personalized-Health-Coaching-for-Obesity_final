import os


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # MySQL configuration
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "Vv@117700")
    DB_NAME = os.environ.get("DB_NAME", "ai_obesity_coaching")


config = Config()

