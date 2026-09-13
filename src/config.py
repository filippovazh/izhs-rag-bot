import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    BOT_TOKEN: str

    GIGACHAT_CLIENT_ID: Optional[str] = None
    GIGACHAT_SECRET: Optional[str] = None

    # Добавьте в Config:
    COLLECTION_NAME: str = "grad_codex"
    PRIORITY_SOURCE: str = "ижс_услуги"
    CHUNKS_PATH: str = str(BASE_DIR / "chunks.pkl")

    MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    CHUNK_SIZE: int = 500
    OVERLAP: int = 70
    EMBEDDING_BATCH_SIZE: int = 32

    DB_PATH: str = str(BASE_DIR / "codex_db")
    PROMPT_PATH: str = str(BASE_DIR / "prompt.txt")
    DATA_PATH: str = str(BASE_DIR / "data")

    DEFAULT_TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 1500
    REQUEST_TIMEOUT: int = 30
    MAX_MESSAGE_LENGTH: int = 4096

    LOG_LEVEL: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Create Config instance from environment variables."""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError(
                "BOT_TOKEN не найден в .env файле!\n"
                "Создайте .env файл с BOT_TOKEN=ваш_токен"
            )

        return cls(
            BOT_TOKEN=bot_token,
            GIGACHAT_CLIENT_ID=os.getenv("GIGACHAT_CLIENT_ID"),
            GIGACHAT_SECRET=os.getenv("GIGACHAT_SECRET"),
            MODEL_NAME=os.getenv("MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2"),
            CHUNK_SIZE=int(os.getenv("CHUNK_SIZE", 500)),
            OVERLAP=int(os.getenv("OVERLAP", 70)),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        )

try:
    config = Config.from_env()
except ValueError as e:
    print(e)
    config = None