from telebot.types import CallbackQuery

from loader import bot

from logs.exceptions import BotStatePaginationNotFoundError
from services.services_logging import error_logger_bot

from database.common.models_movies import BaseMovie
from services.services_database import sending_to_pagination

from services.services_pagination_handlers import (
    send_movie_pagination,
    send_history_pagination,
)


@bot.callback_query_handler(func=lambda call: call.data.split("#")[0] == "history")
@error_logger_bot
def pagination_browsing_history(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки перелистывания истории поисковых запросов фильмов.

    Действия:
        - Если какое-либо состояние отсутствует, выводит сообщение пользователю
        о прекращении сессии отображения фильмов и предлагает осуществить поиск
        по названию фильмов либо вызвать команду `help`.
        - Выводит заданный тип отображения истории поисковых запросов в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос.
        - В случае отсутствия сохраненных данных по запросу фильмов в чат отправляется
        сообщение с предложением осуществить новый поиск фильмов по названию
        или вызвать команду `help`.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Номер страницы в пагинации истории.

    Raises:
        BotStatePaginationNotFoundError: Если состояние пользователя отсутствует, отправляется сообщение о завершении
            сессии отображения фильмов.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        raise BotStatePaginationNotFoundError

    page = int(call.data.split("#")[1])
    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("history_list_page", None)
        data.setdefault("string_response", None)
        data["page_history"] = page

        number_queries_on_page = 7
        send_history_pagination(
            chat_id,
            data["history_list_page"],
            number_queries_on_page,
            data["string_response"],
            page
        )
        bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split("#")[0] == "count")
@error_logger_bot
def pagination_select_history_query(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки выбора фильмов в пагинации истории поисковых запросов.

    Действия:
        - Если какое-либо состояние отсутствует, выводит сообщение пользователю о прекращении сессии отображения
        фильмов и предлагает осуществить поиск по названию фильмов либо вызвать команду `help`.
        - На основе полученных результатов из базы данных BaseMovie формирует словарь фильмов по заданному поисковому
        запросу в виде пагинации с их сортировкой в обратном порядке по id добавления в базу.
        - Выводит перечень просмотренных или избранных фильмов в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Индекс выбранного фильма в истории запросов.

    Raises:
        BotStatePaginationNotFoundError: Если состояние пользователя отсутствует, отправляется сообщение о завершении
            сессии отображения фильмов.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        raise BotStatePaginationNotFoundError

    count = int(call.data.split("#")[1])
    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("history_list_page", None)
        data.setdefault("page_history", 1)
        page = data["page_history"]

        text_search = data["history_list_page"][page - 1][count]["text_search"]

        count_request_movies = BaseMovie.select().where(
            (BaseMovie.user_id == user_id) & (BaseMovie.text_search == text_search)
        )

        data["movie_info"] = sending_to_pagination(
            count_request_movies, type_search="apply_filters"
        )
        bot.delete_message(chat_id, call.message.message_id)
        send_movie_pagination(chat_id, data["movie_info"], total_pages=1)
