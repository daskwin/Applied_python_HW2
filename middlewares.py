from aiogram.types import Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        print(f"Получено сообщение: {event.text}")
        return await handler(event, data)
