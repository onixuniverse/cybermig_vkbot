import os

from src.main import Bot
from dotenv import load_dotenv

load_dotenv()

bot = Bot(api_token=os.getenv("API_TOKEN"))
bot.start()
