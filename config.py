import os
import urllib.parse

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class"""

    # Flask Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-production")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Database Configuration
    DB_SERVER = os.getenv("DB_SERVER", "luke-shopsphere.database.windows.net")
    DB_NAME = os.getenv("DB_NAME", "shopsphere")
    DB_USERNAME = os.getenv("DB_USERNAME", "sqladmin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    # Build connection string directly
    _connection_params = urllib.parse.quote_plus(
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={_connection_params}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG


class DevelopmentConfig(Config):
    """Development environment configuration"""

    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production environment configuration"""

    DEBUG = False
    SQLALCHEMY_ECHO = False


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
