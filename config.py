import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
API_KEY_WEATHER = os.getenv("API_WEATHER")
API_KEY_TRAIN = os.getenv("API_NINJAS_KEY")

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")
