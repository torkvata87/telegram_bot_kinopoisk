from telebot.types import Message

from config_data.config import IMAGE_MOVIE_SEARCH
from loader import bot

from services.services_api import run_search_query
from services.services_pagination_handlers import send_movie_pagination
from services.services_database import (
    update_database,
    update_database_query
)
from services.services_logging import error_logger_bot

from logs.logging_config import log

from states.search_fields import SearchStates, PaginationStates

from database.core import crud_images
from database.common.models_movies import BaseMovie


@bot.message_handler(commands=["movie_search"])
@error_logger_bot
def menu_movie_search(message: Message) -> None:
    """
    Обработчик команды /movie_search.

    Действия:
        - Выполняет сброс состояния и всех данных, связанных с текущей сессией пользователя.
        - Устанавливает состояние пользователя `SearchStates.movie_name`.
        - Сохраняет изображение для команды `movie_search` в базе данных ImageFile для быстрого
        к нему доступа при повторном использовании.
        - Отправляет в чат сообщения с изображением и предложением ввода названия фильма
        в строку ввода.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения с командой `movie_search`.

    Raises:
        FileNotFoundError: Если файл изображения не найден, отправляется сообщение с ошибкой.
    """
    user_id, chat_id = message.from_user.id, message.chat.id
    bot.reset_data(user_id, chat_id)
    bot.set_state(user_id, SearchStates.movie_name, chat_id)

    db_get_image = crud_images.get_image()
    db_save = crud_images.save_image()

    image_name = "movie_search"
    file_id = db_get_image(chat_id, image_name)
    caption = "🔍 <b>Поиск фильма <i>по названию</i>.</b>"
    try:
        if file_id:
            bot.send_photo(
                chat_id,
                file_id,
                caption=caption,
                parse_mode="HTML",
            )
        else:
            with open(IMAGE_MOVIE_SEARCH, "rb") as image:
                sent_message = bot.send_photo(
                    chat_id,
                    image,
                    caption=caption,
                    parse_mode="HTML",
                )
                db_save(chat_id, image_name, sent_message.photo[-1].file_id)
    except FileNotFoundError as exc:
        log.error(f"Ошибка при обработке изображения: {type(exc)} - {exc}")
        bot.send_message(chat_id, caption, parse_mode="HTML")

    text = "✍️ Введите <b><i>название</i></b> фильма 🎬 в строку ввода."
    bot.send_message(chat_id, text, parse_mode="HTML")


@bot.message_handler(
    state=SearchStates.movie_name, func=lambda message: not message.text.startswith("/")
)
@error_logger_bot
def search_movie_name(message: Message) -> None:
    """
    Обработчик ввода названия фильма в состоянии SearchStates.movie_name, если текст не является командой.

    Действия:
        - Выполняет поиск по базе данных BaseMovie.
        - Если поисковый запрос существует в базе данных BaseMovie, то старые данные по этому запросу
        удаляет и перезаписывает с новым `id` поискового запроса и текущей датой. Аналогично обновляет строку
        поискового запроса в базе данных QueryString.
        - Если поисковый запрос в базе данных BaseMovie не найден, то выполняет поиск фильмов по API
        сайта Кинопоиск. Поисковый запрос регистрирует в базе данных QueryString. Результаты поискового
        запроса записывает в базу данных BaseMovie.
        - На основе полученных результатов из базы данных или API формирует словарь фильмов, который передает
        в пагинацию.
        - Устанавливает состояние пользователя `PaginationStates.movies`.
        - Выводит результат поиска фильмов по названию в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос и предыдущее сообщение.
        - При отсутствии результатов поиска отправляет в чат сообщение с предложением заново ввести название фильма
        и устанавливает состояние SearchStates.movie_name.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения названием фильма.

    Returns:
        None: Если результаты поиска не найдены, отправляется сообщение с предложением задать другие фильтры,
            и выполнение функции завершается.
    """
    user_id, chat_id = message.from_user.id, message.chat.id
    bot.set_state(user_id, PaginationStates.movies, chat_id)

    user_movies = BaseMovie.select().where(
        (BaseMovie.user_id == user_id) & (BaseMovie.text_search == message.text)
    )

    bot.delete_message(chat_id, message.message_id - 1)

    type_search = "movie_search"

    if user_movies:
        movie_info = update_database(user_movies, type_search=type_search)
        update_database_query(user_id, message.text)
        total_pages = 2
        bot.delete_message(chat_id, message.message_id)
    else:
        movie_info, total_pages = run_search_query(
            message,
            search_criteria=message.text,
            type_search=type_search,
            text_search=message.text,
        )
    if not movie_info:
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data.clear()
        data["movie_info"] = movie_info
        data["search"] = message.text
        data["page"] = 1
        data["pages"] = total_pages

        send_movie_pagination(chat_id, data["movie_info"], total_pages=total_pages)
