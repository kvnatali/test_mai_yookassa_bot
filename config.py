import os
from pathlib import Path
from dotenv import load_dotenv
import logging

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

class Settings:
    def __init__(self):
        self.DATABASE_URL: str = os.getenv("DATABASE_URL")
        self.YOOKASSA_SHOP_ID: str = os.getenv("STORE_ID")
        self.YOOKASSA_SECRET_KEY: str = os.getenv("SECRET_KEY")
        self.RETURN_URL: str = os.getenv("RETURN_URL")
        self.API_URL: str = os.getenv("API_URL")
        self.TG_BOT_TOKEN: str = os.getenv("TG_BOT_TOKEN")
        self.TG_CHAT_ID: str = os.getenv("TG_CHAT_ID")

        fields = {
            "DATABASE_URL": self.DATABASE_URL,
            "STORE_ID": self.YOOKASSA_SHOP_ID,
            "SECRET_KEY": self.YOOKASSA_SECRET_KEY,
            "RETURN_URL": self.RETURN_URL,
            "TG_BOT_TOKEN": self.TG_BOT_TOKEN,
            "TG_CHAT_ID": self.TG_CHAT_ID,
        }

        no_fields = [name for name, value in fields.items() if not value]

        if no_fields:
            raise ValueError(
                f"Нет переменной: {', '.join(no_fields)}"
            )

settings = Settings()
  