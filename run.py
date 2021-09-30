import os

import requests

from src import logger
from src.main import Bot
from dotenv import load_dotenv

load_dotenv()


def _start():
    try:
        bot = Bot(api_token=os.getenv("API_TOKEN"))
        bot.start()
    except requests.exceptions.ReadTimeout:
        logger.warning("Переподключение к VK Api")


_start()
