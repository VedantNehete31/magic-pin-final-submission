from pydantic import BaseModel
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


class Settings(BaseModel):
    team_name: str = os.getenv("TEAM_NAME", "Vedant Merchant Assist")
    team_members: list[str] = [name.strip() for name in os.getenv("TEAM_MEMBERS", "Vedant Nehete").split(",") if name.strip()]
    model: str = os.getenv("BOT_MODEL", "deterministic-composer-v1")
    approach: str = "custom rule-based trigger composer with reply routing, consent checks, and context-version memory"
    contact_email: str = os.getenv("CONTACT_EMAIL", "nehetevedant9@gmail.com")
    version: str = os.getenv("BOT_VERSION", "1.0.0")
    submitted_at: str = os.getenv("SUBMITTED_AT", "2026-07-13T00:00:00Z")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


settings = Settings()
