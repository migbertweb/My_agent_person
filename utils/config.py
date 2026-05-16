import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


class Config:
    @staticmethod
    def get(key: str, default=None):
        value = os.getenv(key, default)
        if value is None:
            return default
        return value

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        try:
            return int(Config.get(key, default))
        except ValueError:
            return default

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        return Config.get(key, str(default)).lower() in ("true", "1", "yes")

    @staticmethod
    def get_list(key: str, default: str = "") -> list:
        value = Config.get(key, default)
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value if isinstance(value, list) else []


OLLAMA_HOST = Config.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = Config.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_FALLBACK_MODEL = Config.get("OLLAMA_FALLBACK_MODEL", "gemma4:31b-cloud")

# Ollama Cloud Configuration
OLLAMA_CLOUD_ENABLED = Config.get_bool("OLLAMA_CLOUD_ENABLED", False)
OLLAMA_CLOUD_URL = Config.get("OLLAMA_CLOUD_URL", "https://api.ollama.com")
OLLAMA_CLOUD_MODEL = Config.get("OLLAMA_CLOUD_MODEL", "gemma4:31b-cloud")
OLLAMA_CLOUD_API_KEY = Config.get("OLLAMA_CLOUD_API_KEY", "")

DB_PATH = Config.get("DB_PATH", "./memory.db")
MAX_ITERATIONS = Config.get_int("MAX_ITERATIONS", 5)
AGENT_NAME = Config.get("AGENT_NAME", "AgentPiro")
DEBUG_MODE = Config.get_bool("DEBUG_MODE", False)
ALLOWED_COMMANDS = Config.get_list("ALLOWED_COMMANDS", "date,time,cal,echo,ls,pwd,whoami,uname,cat")

# TTS Configuration
TTS_ENABLED = Config.get_bool("TTS_ENABLED", True)
TTS_PROVIDER = Config.get("TTS_PROVIDER", "edge")
TTS_VOICE = Config.get("TTS_VOICE", "es-ES-AlvaroNeural")
TTS_RATE = Config.get("TTS_RATE", "0%")
TTS_PITCH = Config.get("TTS_PITCH", "0%")
TTS_AUTO_PLAY = Config.get_bool("TTS_AUTO_PLAY", True)