from typing import Any, List, Dict

from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from config_data.config import IMAGE_EMPTY_POSTER
from keyboards.pagination.pagination_movies import create_paginator_movies
from keyboards.pagination.pagination_history import create_paginator_history
from loader import bot

from services.services_logging import error_logger_bot, error_logger_func

from logs.logging_config import log


@error_logger_func
def send_movie_pagination(
    chat_id: int,
    movies_data: List[Dict[str, Any]],
    current_page: int = 1,
    total_pages: int = 1,
    page_number: int = 1,
) -> None:
    """
    Отправляет в чат сообщение со списком фильмов в виде пагинации.

    Args:
        chat_id (int): Идентификатор чата, может быть chat_id или user_id.
        movies_data (List[Dict[str, Any]]): Список словарей, содержащих информацию о фильмах.
        current_page (int): Текущая страница в списке фильмов. По умолчанию равна 1.
        total_pages (int): Общее количество страниц фильмов, если есть несколько страниц в результатах поиска.
            По умолчанию равно 1.
        page_number (int): Номер текущей страницы в результатах поиска на ресурсе сайта "Кинопоиск".
            По умолчанию равен 1.

    Raises:
        ValueError: Если некорректный формат списка фильмов или не предоставлено изображение для фильма.
        IndexError: Если current_page выходит за пределы допустимого диапазона страниц.
        ApiTelegramException: Если возникает ошибка при отправке изображения через Telegram API типа "400 Bad Request:
            wrong type of the web page content".
    """
    if not isinstance(movies_data, list):
        raise ValueError("Информация о фильмах должна передаваться в виде списка.")
    # if not (1 <= current_page <= len(movies_data)):
    #     raise IndexError("Текущая страница выходит за пределы допустимого диапазона.")

    data_movie = movies_data[current_page - 1]

    emoji_data = {
        "movie": "🎞️",
        "tv-series": "📺",
        "cartoon": "🦄",
        "anime": "🌸",
        "animated-series": "📺🦄",
    }

    movie_param = [
        {"🌍 ": data_movie["countries"]},
        {"\n\n🎭 ": data_movie["genre"]},
        {"\n\n🏆 ": data_movie["rating"]},
        {"\t\t\t👦 +": data_movie["age_rating"]},
        {"\n\n📝 ": data_movie["short_description"]},
    ]

    text_data = "".join(
        [
            f"{key}<i>{value}</i>"
            for elem in movie_param
            for key, value in elem.items()
            if value
        ]
    )

    alternative_name = (
        f"/ {data_movie['alternative_name']} "
        if data_movie["alternative_name"]
        else " "
    )

    text = (
        f"{emoji_data[data_movie['type_movie']]} <b>{data_movie['name_movie']}</b> "
        f"<i>{alternative_name}({data_movie['year']})</i>\n\n"
        f"{text_data}"
    )

    image = data_movie["poster"]
    paginator = create_paginator_movies(
        movies_data, current_page, total_pages, page_number
    )
    try:
        if not image:
            raise ValueError("Постер фильма отсутствует")
        bot.send_photo(
            chat_id,
            image,
            caption=text,
            reply_markup=paginator.markup,
            parse_mode="HTML",
        )
    except (ApiTelegramException, ValueError) as exc:
        with open(IMAGE_EMPTY_POSTER, "rb") as image_file:
            bot.send_photo(
                chat_id,
                image_file,
                caption=text,
                reply_markup=paginator.markup,
                parse_mode="HTML",
            )

        log.error(
            f"{type(exc).__name__}: Ошибка при отправке изображения через Telegram API - {exc}."
        )
        log.info("В чат было направлено сообщение с пустым постером.")


@error_logger_func
def send_description_pagination_page(
    chat_id: int, movies_data: List[Dict[str, Any]], current_page: int = 1
) -> None:
    """
    Отправляет сообщение в чат с полной информацией о фильме, используя пагинацию для переключения между фильмами.

    Args:
        chat_id (int): Идентификатор чата, может быть chat_id или user_id.
        movies_data (List[Dict[str, Any]]): Список словарей, содержащих информацию о фильмах.
        current_page (int): Текущая страница в списке фильмов. По умолчанию равна 1.

    Raises:
        ValueError: Если некорректный формат списка фильмов.
        IndexError: Если current_page выходит за пределы допустимого диапазона страниц.
    """
    if not isinstance(movies_data, list):
        raise ValueError("Информация о фильмах должна передаваться в виде списка.")
    if not (1 <= current_page <= len(movies_data)):
        raise IndexError("Текущая страница выходит за пределы допустимого диапазона.")

    description = movies_data[current_page - 1]["description"]
    paginator = create_paginator_movies(
        movies_data, current_page, show_pagination_descr=True
    )

    text = f"📜 {description}"
    keyboard = paginator.markup

    if description:
        bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


@error_logger_bot
def get_check_status(
    message: Message,
    movies_data: List[Dict[str, Any]],
    current_page: int = 1,
    total_pages: int = 1,
    page_number: int = 1,
    show_pagination_descr: bool = False,
) -> None:
    """
    Обновляет клавиатуру пагинации при изменении статуса фильма "Избранный" или "Просмотренный".

    Args:
        message (Message): Сообщение Telegram, для которого необходимо обновить клавиатуру.
        movies_data (List[Dict[str, Any]]): Список словарей, содержащих информацию о фильмах.
        current_page (int): Текущая страница в списке фильмов. По умолчанию равна 1.
        total_pages (int): Общее количество страниц фильмов, если есть несколько страниц в результатах поиска.
            По умолчанию равно 1.
        page_number (int): Номер текущей страницы в результатах поиска на ресурсе сайта "Кинопоиск".
            По умолчанию равен 1.
        show_pagination_descr (bool): Флаг, указывающий, что необходимо создать клавиатуру пагинации в режиме просмотра
            полного описания фильма. По умолчанию `False`.

    Raises:
        ValueError: Если некорректный формат списка фильмов.
    """
    if not isinstance(movies_data, list):
        raise ValueError("Информация о фильме должна передаваться в виде списка.")

    paginator = create_paginator_movies(
        movies_data, current_page, total_pages, page_number, show_pagination_descr
    )

    bot.edit_message_reply_markup(
        message.chat.id, message.message_id, reply_markup=paginator.markup
    )


@error_logger_bot
def send_history_pagination(
    chat_id: int,
    history_data: List[Dict[str, Any]],
    number_queries_on_page: int,
    string_response: str = "",
    current_page: int = 1,
) -> None:
    """
    Отправляет в чат сообщение со списком истории поисковых запросов в виде пагинации.

    Args:
        chat_id (int): Идентификатор чата, может быть chat_id или user_id.
        history_data (List[Dict[str, Any]]): Список словарей, содержащих информацию о поисковых запросах.
        number_queries_on_page (int): Количество поисковых запросов для отображения на текущей страницы пагинации.
        string_response (str): Информация о заданных пользователем фильтрах. По умолчанию пустая строка.
        current_page (int): Текущая страница в списке истории поисковых запросов. По умолчанию равна 1.

    Raises:
        ValueError: Если некорректный формат списка поисковых запросов.
        IndexError: Если current_page выходит за пределы допустимого диапазона страниц.
    """
    if not isinstance(history_data, list):
        raise ValueError("Информация о поисковых запросах должна передаваться в виде списка.")
    if not (1 <= current_page <= len(history_data)):
        raise IndexError("Текущая страница выходит за пределы допустимого диапазона.")

    paginator = create_paginator_history(
        history_data, number_queries_on_page, current_page
    )
    filter_search = ", ".join(string_response) if string_response else "за все время"
    text = f"📌 Задана история поиска по фильтрам: <b><i>{filter_search}</i></b>"
    bot.send_message(
        chat_id,
        text,
        reply_markup=paginator.markup,
        parse_mode="HTML",
    )
