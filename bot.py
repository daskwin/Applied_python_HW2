import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import setup_handlers
from middlewares import LoggingMiddleware

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключаем middleware и хендлеры
dp.message.middleware(LoggingMiddleware())  # Логирование событий
setup_handlers(dp)


async def main():
    print("Бот запущен!")
    # Запускаем бота в режиме Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
