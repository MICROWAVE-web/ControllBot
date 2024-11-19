from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config

TOKEN = config("BOT_TOKEN")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

bot = Bot(token=TOKEN)
