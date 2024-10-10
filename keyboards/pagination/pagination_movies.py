from typing import Any, Dict, List

from telegram_bot_pagination import InlineKeyboardPaginator, InlineKeyboardButton
from telebot.types import InlineKeyboardButton

from services.services_logging import error_logger_func
from logs.logging_config import log


@error_logger_func
def create_paginator_movies(
    movies_data: List[Dict[str, Any]],
    current_page: int,
    total_pages: int = 1,
    page_number: int = 1,
    show_pagination_descr: bool = False,
) -> InlineKeyboardPaginator:
    """
    Создает клавиатуру пагинации с кнопками навигации по списку фильмов.
    Дополнительно создает кнопки для добавления фильмов в избранное или в просмотренное, кнопки для нового поиска,
    показа полного описания фильма, или перехода по ссылке на страницу фильма на сайте
    `Кинопоиск` (https://www.kinopoisk.ru).

    Args:
        movies_data (List[Dict[str, Any]]): Список словарей, содержащих информацию о фильмах.
        current_page (int): Текущая страница в списке фильмов.
        total_pages (int): Общее количество страниц фильмов, если есть несколько страниц в результатах поиска.
            По умолчанию равно 1.
        page_number (int): Номер текущей страницы в результатах поиска на ресурсе сайта `Кинопоиск`.
        show_pagination_descr (bool): Флаг, указывающий, что необходимо создать клавиатуру пагинации в режиме просмотра
            полного описания фильма. По умолчанию `False`.

    Returns:
        InlineKeyboardPaginator: Объект инлайн-клавиатуры с кнопками для навигации по списку фильмов.

     Raises:
        TypeError: Если `movies_data` не является списком или содержит неверные элементы.
        ValueError: Если `current_page`, `total_pages` или `page_number` имеют некорректные значения.
    """
    if not isinstance(movies_data, list):
        raise TypeError("movies_data должен быть списком.")
    if not all(isinstance(item, dict) for item in movies_data):
        raise TypeError("Каждый элемент movies_data должен быть словарем.")
    if not isinstance(current_page, int):
        raise ValueError("current_page должен быть целым числом.")
    if not isinstance(total_pages, int) or total_pages < 1:
        raise ValueError("total_pages должен быть положительным целым числом.")
    if not isinstance(page_number, int) or page_number < 1:
        raise ValueError("page_number должен быть положительным целым числом.")

    description = movies_data[current_page - 1]["description"]
    id_movie = movies_data[current_page - 1]["movie_id"]
    is_favorites = movies_data[current_page - 1]["is_favorites"]
    is_viewed = movies_data[current_page - 1]["is_viewed"]
    type_search = movies_data[current_page - 1]["type_search"]

    paginator = InlineKeyboardPaginator(
        len(movies_data), current_page=current_page, data_pattern="movie#{page}"
    )

    star_favorites = "⭐ В избранное" if not is_favorites else "🌟 В избранном"
    eye_viewed = "❎️ Не просмотрено" if not is_viewed else "✅ Просмотрено"
    url = f"https://www.kinopoisk.ru/film/{id_movie}/"
    btn_favorites = InlineKeyboardButton(
        star_favorites, callback_data=f"is_favorites#{current_page}"
    )
    btn_viewed = InlineKeyboardButton(
        eye_viewed, callback_data=f"is_viewed#{current_page}"
    )
    btn_more = InlineKeyboardButton(
        text="📜 Больше", callback_data=f"show_description#{current_page}"
    )
    btn_url = InlineKeyboardButton(text="🌐", url=url)
    btn_new_search = InlineKeyboardButton(
        text="🔍 Новый поиск", callback_data="new_search"
    )
    btn_back_menu = InlineKeyboardButton(
        text="⬅️ Назад в меню", callback_data=type_search
    )
    btn_continue = InlineKeyboardButton(
        text="➡️ Дальше", callback_data="continue_search"
    )
    btn_search_back = InlineKeyboardButton(text="⬅️ Назад", callback_data="search_back")
    btn_back = InlineKeyboardButton(
        text="⬅️ Назад", callback_data=f"back_movie#{current_page}"
    )

    paginator.add_before(btn_viewed, btn_favorites)

    if not show_pagination_descr:
        btn_more_info = btn_more if description else btn_url
        btn_type_search = (
            btn_new_search if type_search.startswith("movie") else btn_back_menu
        )

        if current_page == len(movies_data) and total_pages > 1:
            paginator.add_after(btn_more_info, btn_continue)
            paginator.add_after(btn_type_search)
        elif current_page == 1 and page_number > 1:
            paginator.add_after(btn_more_info, btn_search_back)
            paginator.add_after(btn_type_search)
        else:
            paginator.add_after(btn_more_info, btn_type_search)

    else:
        paginator.add_after(btn_url, btn_back)

    return paginator
