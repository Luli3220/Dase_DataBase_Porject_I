import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27018")
    mongo_db: str = os.getenv("MONGO_DB", "survey_dev")
    session_secret: str = os.getenv("SESSION_SECRET", "")
    environment: str = os.getenv("ENVIRONMENT", "development")
    base_url: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    session_max_age: int = int(os.getenv("SESSION_MAX_AGE", "28800"))
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
