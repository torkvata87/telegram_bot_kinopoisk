from typing import Any, List, Dict, Tuple

from telebot.types import Message, CallbackQuery

from keyboards.buttons.btns_for_movie_by_filters import btns_filters
from keyboards.inline.inline_movie_by_filters import select_filters_keyboard

from services.services_logging import error_logger_bot, set_ids
from services.services_database import search_for_movie

from site_API.site_api_handler import search_movies

from loader import bot
from states.search_fields import SearchStates

from logs.logging_config import log


@error_logger_bot
def run_search_query(
    message_or_call: Message | CallbackQuery,
    search_criteria: str | Dict[str, Any],
    type_search: str,
    text_search: str = "",
    page: int = 1,
) -> Tuple[List[Dict[str, Any]] | None, int]:
    """
    Выполняет поиск фильмов в зависимости от типа поиска и переданного запроса на поиск в виде названия фильма
    или словаря фильтров.

    Args:
        message_or_call (Message | CallbackQuery): Объект, содержащий данные сообщения от пользователя (Message),
            либо информацию о нажатой кнопке (CallbackQuery).
        search_criteria (str | Dict[str, Any]): Текст или фильтры для поиска фильмов.
        type_search (str): Тип поиска. Возможные значения: "movie_by_filters" или "movie_search".
        text_search (str): Текст для поиска фильма.
        page (int): Номер страницы поиска результатов.


    Returns:
        Tuple[List[Dict[str, Any]] | None, int]:
            - movie_info (List[Dict[str, Any]] | None): Список фильмов с их информацией.
            - pages (int): Общее количество страниц результатов поиска.

        В случае ошибки или отсутствия результатов:
            - Отправляется сообщение пользователю, возвращается None и нулевой номер страницы.

    Raises:
        ValueError: Если `type_search` имеет недопустимое значение или `page` не является положительным целым числом.
        TypeError: Если `search_criteria` или `text_search` не является строкой.
        Exception: Если произошла ошибка при выполнении поиска или обработки данных, функция отправляет сообщение
                   пользователю о проблеме с соединением или сервером.
    """
    if not isinstance(message_or_call, (Message, CallbackQuery)):
        raise TypeError(
            "message_or_call должны быть объектами Message или CallbackQuery."
        )
    if not isinstance(search_criteria, (str, dict)):
        raise TypeError("search_criteria должен быть строкой или словарем.")
    if type_search not in {"movie_by_filters", "movie_search"}:
        raise ValueError(f"Недопустимый тип поиска: {type_search}")
    if not isinstance(text_search, str):
        raise TypeError("text_search должен быть строкой.")
    if not isinstance(page, int) or page < 1:
        raise ValueError("page должен быть положительным целым числом.")

    chat_id, user_id, message_id = set_ids(message_or_call)

    movies_data = search_movies(search_criteria, type_search, page)

    bot.delete_message(chat_id, message_id)
    if isinstance(movies_data, tuple):
        movie_search_result, pages = search_movies(search_criteria, type_search, page)
        if isinstance(movie_search_result, list):
            if movie_search_result:
                movie_info = search_for_movie(
                    user_id=user_id,
                    result_response=movie_search_result,
                    type_search=type_search,
                    text_search=text_search,
                )
                return movie_info, pages
            else:
                bot.reset_data(user_id, chat_id)
                if type_search == "movie_by_filters":
                    text_addition = (
                        "✔️ Задайте новые <b><i>фильтры</i></b> с помощью кнопок ниже "
                        "либо сразу перейдите к 🔍 <b><i>поиску</i></b>."
                    )
                    keyboard = select_filters_keyboard(btns_filters, buttons_per_row=2)
                    state = SearchStates.query
                else:
                    text_addition = (
                        "✍️ Введите в строку ввода другое <b><i>название</i></b> фильма."
                    )
                    keyboard = None
                    state = SearchStates.movie_name

                text = (
                    f"❌ По вашему запросу <b>ничего не найдено</b>.\n\n{text_addition}"
                )
                bot.send_message(
                    chat_id, text, reply_markup=keyboard, parse_mode="HTML"
                )
                bot.set_state(user_id, state, chat_id)

                log.info(
                    "Поисковой запрос не выдал результатов. Пользователю предложено создать новый запрос."
                )
            return None, 0
    else:
        text = (
            f"🚫 <b>{movies_data}</b>\n\n" "⌛ <i>Попробуйте выполнить поиск позже.</i>"
        )
        bot.send_message(chat_id, text, parse_mode="HTML")
        bot.set_state(user_id, SearchStates.movie_name, chat_id)
        log.info(
            "При поисковом запросе возникла ошибка. Пользователю предложено создать новый запрос позже."
        )
        return None, 0
