import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application configuration settings."""
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GIT_TOKEN: str = os.getenv("GIT_TOKEN", "")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    def __init__(self):
        if not self.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY not set. LLM features will use default values.")
        if not self.GIT_TOKEN:
            print("WARNING: GIT_TOKEN not set.")

settings = Settings()
