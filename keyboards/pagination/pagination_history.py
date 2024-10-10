from typing import Any, Dict, List

from telegram_bot_pagination import InlineKeyboardPaginator, InlineKeyboardButton
from telebot.types import InlineKeyboardButton

from services.services_logging import error_logger_func


@error_logger_func
def create_paginator_history(
    history_data: List[List[Dict[str, Any]]],
    number_queries_on_page: int,
    current_page: int = 1,
) -> InlineKeyboardPaginator:
    """
    Создает клавиатуру пагинации с кнопками поисковых запросов и кнопками навигации по истории поисковых запросов.
    Дополнительно создает кнопки для добавления фильмов в избранное или в просмотренное,
    кнопки для нового поиска, показа полного описания фильма, или перехода по ссылке на страницу фильма
    на сайте "Кинопоиск" (https://www.kinopoisk.ru).

    Args:
        history_data (List[List[Dict[str, Any]]]): Список словарей, содержащих информацию о поисковых запросах.
        number_queries_on_page (int): Количество поисковых запросов для отображения на текущей страницы пагинации.
        current_page (int): Текущая страница в списке истории поисковых запросов.

    Returns:
        InlineKeyboardPaginator: Объект инлайн-клавиатуры с кнопками для навигации по списку фильмов.

    Raises:
        ValueError: Если `number_queries_on_page` или `current_page` имеют недопустимые значения.
    """
    if not isinstance(history_data, list):
        raise TypeError("history_data должен быть списком.")
    if not isinstance(number_queries_on_page, int) or number_queries_on_page <= 0:
        raise ValueError("number_queries_on_page должен быть положительным целым числом.")

    if current_page > len(history_data):
        current_page = len(history_data)

    paginator = InlineKeyboardPaginator(
        len(history_data), current_page=current_page, data_pattern="history#{page}"
    )

    for index in range(
        min(number_queries_on_page, len(history_data[current_page - 1]))
    ):
        text = history_data[current_page - 1][index]["text_search"]
        btn_history = InlineKeyboardButton(text, callback_data=f"count#{index}")
        paginator.add_before(btn_history)

    btn_back_menu = InlineKeyboardButton(
        text="⬅️ Назад в меню", callback_data="history_menu"
    )
    paginator.add_after(btn_back_menu)

    return paginator
