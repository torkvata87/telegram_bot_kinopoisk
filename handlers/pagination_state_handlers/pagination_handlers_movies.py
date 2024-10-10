from telebot.types import CallbackQuery

from loader import bot

from logs.exceptions import BotStatePaginationNotFoundError
from services.services_logging import error_logger_bot

from database.common.models_movies import MoviePostponed
from services.services_database import (
    toggle_movie_field_response,
    search_for_movie,
    sending_to_pagination,
)
from site_API.site_api_handler import search_movies

from keyboards.buttons.btns_for_movie_by_filters import btns_filters
from keyboards.buttons.btns_for_postponed_movies import button_back_postponed, buttons_end_search
from keyboards.inline.inline_keyboard import create_inline_keyboard
from keyboards.inline.inline_movie_by_filters import select_filters_keyboard

from services.services_pagination_handlers import (
    send_movie_pagination,
    send_description_pagination_page,
    get_check_status,
)

from states.search_fields import SearchStates


@bot.callback_query_handler(
    func=lambda call: call.data.split("#")[0] in ["movie", "back_movie"]
)
@error_logger_bot
def pagination_browsing_movie(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки перелистывания фильмов и `Назад` (для возврата к перелистыванию фильмов из меню
    полного описания конкретного фильма).

    Действия:
        - Если какое-либо состояние отсутствует, выводит сообщение пользователю о прекращении сессии отображения
        фильмов и предлагает осуществить поиск по названию фильмов либо вызвать команду `help`.
        - Выводит заданный перечень фильмов в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос.
        - В случае отсутствия сохраненных данных по запросу фильмов в чат отправляется сообщение с предложением
        осуществить новый поиск фильмов по названию или вызвать команду `help`.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Номер страницы в пагинации просмотра фильма либо номер страницы и "Назад" (для возврата
            к перелистыванию фильмов из меню полного описания конкретного фильма).

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
        data["is_description"] = False
        movie_info = data.setdefault("movie_info", None)
        total_pages = data.setdefault("pages", 1)
        page_number = data.setdefault("page", 1)
    if movie_info:
        send_movie_pagination(chat_id, movie_info, page, total_pages, page_number)
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(
    func=lambda call: call.data.split("#")[0] == "show_description"
)
@error_logger_bot
def pagination_show_full_description_movie(call: CallbackQuery) -> None:
    """
    Обработчик нажатия на кнопку `Больше` - для показа полного описания текущего фильма (данная кнопка в пагинации
    появляется только в случае наличия у фильма полного описания).

    Действия:
        - Если какое-либо состояние отсутствует, выводит сообщение пользователю о прекращении сессии отображения
        фильмов и предлагает осуществить поиск по названию фильмов либо вызвать команду `help`.
        - Выводит описание полное фильма в интерфейсе пагинации.
        - Удаляет сообщение, вызвавшее запрос.
        - В случае отсутствия сохраненных данных по запросу фильмов в чат отправляется сообщение с предложением
        осуществить новый поиск фильмов по названию или вызвать команду `help`.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Больше" для просмотра полного описания фильма.

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
        movie_info = data.setdefault("movie_info", None)
        data["is_description"] = True
    if movie_info:
        send_description_pagination_page(chat_id, movie_info, page)
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(
    func=lambda call: call.data.split("#")[0] in ["is_favorites", "is_viewed"]
)
@error_logger_bot
def pagination_change_status_movie(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки "Не просмотрено" и "В избранное".

    Действия:
        - Если какое-либо состояние отсутствует, выводит сообщение пользователю о прекращении сессии отображения
        фильмов и предлагает осуществить поиск по названию фильмов либо вызвать команду `help`.
        - При нажатии на одну из этих кнопок обновляется клавиатура пагинации с заменой текста на кнопках на
        `Просмотрено` и `В избранном`.
        - В базах данных BaseMovie и PostponedMovies статусы текущего фильма `is_favorites` или `is_viewed`
        меняются на противоположные.
        - Из базы данных PostponedMovies фильм удаляется, если оба его статуса `is_favorites` и `is_viewed`
        одновременно равны нулю.
        - Если вызов отображения фильмов происходил из команды `postponed_movies` (условие
        data_movie_info[page - 1][`type_search`] == `postponed_movies`), то при изменении статуса фильмов
        происходит обновление сохраненного словаря перечня фильмов с его выводом в пагинацию с их сортировкой
        в обратном порядке по id добавления в базу. В этом случае предусмотрено уменьшение страниц в пагинации,
        если они удалены из избранного или просмотренного. В случае полной очистки базы данных `postponed_movies`
        от избранных или просмотренных фильмов в чат выводится сообщение об отсутствии фильмов в базе данных
        с инлайн-клавиатурой возврата в меню команды `postponed_movies`.
        - В случае отсутствия сохраненных данных по запросу фильмов в чат отправляется сообщение с предложением
        осуществить новый поиск фильмов по названию или вызвать команду `help`.

     Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Статус фильма (избранное или просмотренное).

    Raises:
        BotStatePaginationNotFoundError: Если состояние пользователя отсутствует, отправляется сообщение о завершении
            сессии отображения фильмов.

    Returns:
        None: Возвращает `None`, пользователем во время просмотра отложенных фильмов они все удалены.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)
    if not current_state:
        raise BotStatePaginationNotFoundError

    page = int(call.data.split("#")[1])
    status = call.data.split("#")[0]

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("is_description", False)
        data.setdefault("movie_info", None)
        total_pages = data.setdefault("pages", 1)
        page_number = data.setdefault("page", 1)

    if data["movie_info"]:
        movie_info = data["movie_info"][page - 1]
        movie_info[status] = not movie_info[status]
        toggle_movie_field_response(user_id, movie_info, status)

        state = (
            MoviePostponed.is_favorites
            if status == "is_favorites"
            else MoviePostponed.is_viewed
        )

        get_check_status(
            call.message,
            data["movie_info"],
            page,
            total_pages,
            page_number,
            show_pagination_descr=data["is_description"],
        )
        if movie_info["type_search"] == "postponed_movies":
            if status == data["button_postponed"]:
                user_movies = (
                    MoviePostponed.select()
                    .where((MoviePostponed.user_id == user_id) & state)
                    .order_by(MoviePostponed.id.desc())
                )

                data["movie_info"] = sending_to_pagination(
                    user_movies, type_search="postponed_movies"
                )
                if len(data["movie_info"]) > 0:
                    page = page - 1 if page > 1 else 0
                else:
                    text = "😔 К сожалению, у вас больше нет фильмов в этом разделе."
                    keyboard = create_inline_keyboard(
                        button_back_postponed, buttons_per_row=1
                    )
                    bot.send_message(chat_id, text, reply_markup=keyboard)
                    bot.delete_message(chat_id, call.message.message_id)
                    return
            send_movie_pagination(chat_id, data["movie_info"], page, total_pages, page_number)
            bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(
    func=lambda call: call.data in ["continue_search", "search_back"]
)
@error_logger_bot
def pagination_continue_search_movie(call: CallbackQuery):
    """
    Обработчик нажатий на кнопки `Дальше` и `Назад` (для перехода на новую страницу поискового запроса фильмов
    согласно заданному заданным параметрам и для возврата на предыдущую страницу поисковых запросов).

    Действия:
        - Если какое-либо состояние отсутствует, выводит сообщение пользователю о прекращении сессии отображения
        фильмов и предлагает осуществить поиск по названию фильмов либо вызвать команду `help`.
        - Обновление словаря отображения фильтров осуществляется с учетом заданного поискового запроса из меню
        команд `movie_search` или `movie_by_filters`.
        - Выводит заданный перечень фильмов в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Указывает на действие (перелистывание вперед или назад).

    Raises:
        BotStatePaginationNotFoundError: Если состояние пользователя отсутствует, отправляется сообщение
            о завершении сессии отображения фильмов.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        raise BotStatePaginationNotFoundError

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("search", None)
        data.setdefault("page", 1)
        data["page"] = (
            data["page"] + 1 if call.data == "continue_search" else data["page"] - 1
        )
        data["is_description"] = False

        type_search = (
            "movie_search" if isinstance(data["search"], str) else "movie_by_filters"
        )

        movie_search_result, pages = search_movies(
            data["search"], type_search, page=data["page"]
        )

        if movie_search_result:
            data["movie_info"] = search_for_movie(
                user_id, movie_search_result, type_search
            )
            data["pages"] = pages - data["page"]
            page = len(data["movie_info"]) if call.data == "search_back" else 1
            send_movie_pagination(
                chat_id,
                data["movie_info"],
                current_page=page,
                total_pages=pages,
                page_number=data["page"],
            )
        else:
            text = ("📕 Вам были показаны <b><i>все результаты</i></b> по заданному поисковому запросу.\n\n"
                    "⬅️ <b><i>Вернитесь назад</i></b> или ✔️ задайте <b><i>новый поиск</i></b>.")
            keyboard = create_inline_keyboard(buttons_end_search, buttons_per_row=1)
            bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "new_search")
@error_logger_bot
def menu_get_new_search(call: CallbackQuery):
    """
    Обработчик нажатия на кнопку `Новый поиск`.

    Действия:
        - На основе поискового запроса переходит к выполнению нового поискового запроса фильмов из меню
        команд `movie_search` или `movie_by_filters`.
        - Если какое-либо состояние отсутствует, выводит сообщение пользователю о прекращении сессии отображения
        фильмов и предлагает осуществить поиск по названию фильмов либо вызвать команду `help`.
        - Удаляет сообщение, вызвавшее запрос.
        - В случае отсутствия сохраненных данных по запросу фильмов в чат отправляется сообщение об их отсутствии.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название кнопки "Новый поиск".

    Returns:
        None: Возвращает `None`, если состояние пользователя отсутствует.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    current_state = bot.get_state(user_id, chat_id)

    if not current_state:
        raise BotStatePaginationNotFoundError

    with bot.retrieve_data(user_id, chat_id) as data:
        data.setdefault("search", None)
        if data["search"] and isinstance(data["search"], dict):
            bot.reset_data(user_id, chat_id)
            bot.set_state(
                user_id,
                SearchStates.query,
                chat_id,
            )
            text = (
                "✔️ Задайте <b><i>фильтры</i></b> с помощью кнопок ниже "
                "либо сразу перейдите к <b><i>поиску</i></b>."
            )
            data["buttons_filters"] = btns_filters
            keyboard = select_filters_keyboard(
                data["buttons_filters"], buttons_per_row=2
            )
        else:
            bot.reset_data(user_id, chat_id)
            bot.set_state(
                user_id,
                SearchStates.movie_name,
                chat_id,
            )
            text = "✍️ Введите <i>название</i> фильма 🎬 в строку ввода."
            keyboard = None

        bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
    bot.delete_message(chat_id, call.message.message_id)
