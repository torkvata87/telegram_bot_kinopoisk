from logs.exceptions import BotStatePaginationNotFoundError, ServerRequestError
from typing import Dict, Type
from telebot.apihelper import ApiTelegramException
from peewee import IntegrityError


exception_type: Dict[Type[Exception], str] = {
    ValueError: "Неверное значение",
    KeyError: "Ключ не найден в словаре",
    IndexError: "Индекс за пределами диапазона",
    TypeError: "Неверный тип данных",
    BotStatePaginationNotFoundError: "Ошибка сессии просмотра фильмов",
    ApiTelegramException: "Ошибка при попытке выполнить запрос",
    ServerRequestError: "Неверный запрос на сервер",
    IntegrityError: "Ошибка при работе с записью данных в базу данных"
}
