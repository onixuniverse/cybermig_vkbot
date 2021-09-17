from src.main import Bot
from utils.config import api_token

bot = Bot(api_token=api_token)
bot.start()
