import os
import time

from src import logger
from src.main import Bot
from dotenv import load_dotenv

load_dotenv()


def _start():
    while True:
        try:
            bot = Bot(api_token=os.getenv("API_TOKEN"))
            bot.start()
        except Exception as exc:
            logger.error(exc)
            logger.warning("Переподключение...")
            time.sleep(1)


_start()
