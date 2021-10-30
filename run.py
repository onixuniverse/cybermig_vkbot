import os
import time

import requests

from src import logger
from src.main import Bot
from dotenv import load_dotenv

load_dotenv()


def _start():
    while True:
        try:
            bot = Bot(api_token=os.getenv("API_TOKEN"))
            bot.start()
        except:
            logger.warning("Переподключение...")
            time.sleep(15)


_start()
