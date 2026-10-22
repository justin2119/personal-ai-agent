import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    RODIUM_API_KEY: str = os.getenv("RODIUM_API_KEY", "")
    RODIUM_BASE_URL: str = os.getenv("RODIUM_BASE_URL", "https://api.rodiumai.io/v1")
    RODIUM_MODEL: str = os.getenv("RODIUM_MODEL") or os.getenv("MODEL_NAME") or "gpt-4o-mini"
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")


settings = Settings()
