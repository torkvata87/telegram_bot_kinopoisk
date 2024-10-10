from typing import Any, List, Dict

from peewee import Query

from database.common.models_movies import db, QueryString, BaseMovie, MoviePostponed
from database.core import crud
from services.services_logging import error_logger_func

db_write = crud.create()
db_read = crud.retrieve()


@error_logger_func
def write_to_query_string(
    user_id: int, type_search: str, text_search: str
) -> Dict[str, str]:
    """
    Формирует словарь для сохранения строки поискового запроса в базе данных QueryString.

    Args:
        user_id (int): Идентификатор пользователя, который инициировал запрос.
        type_search (str): Тип поискового запроса (например, "movies_search" или "movies_by_filters").
        text_search (str): Текст поискового запроса.

    Returns:
         Dict[str, str]: Словарь, содержащий данные для записи в таблицу "query_string".
            Ключи: "user_id", "type_search", "text_search".

    Raises:
        ValueError: Если передан пустой или некорректный `text_search` или `type_search`.
    """
    if not text_search or not isinstance(text_search, str):
        raise ValueError("`text_search` должен быть непустой строкой.")
    if not type_search or not isinstance(type_search, str):
        raise ValueError("`type_search` должен быть непустой строкой.")

    return {
        "user_id": str(user_id),
        "type_search": type_search,
        "text_search": text_search,
    }


@error_logger_func
def write_to_base_movies(
    user_id: int,
    movie: Dict[str, Dict[str, str] | None],
    type_search: str,
    text_search: str,
    status_favorites: bool,
    status_viewed: bool,
) -> Dict[str, str]:
    """
    Формирует словарь для сохранения информации о фильме в базе данных BaseMovie.

    Args:
        user_id (int): Идентификатор пользователя, который инициировал запрос.
        movie (Dict[str, Dict[str, str] | None]): Информация о фильме в виде словаря, полученная при обращении
            к API. Вложенные словари могут быть `None`.
        type_search (str): Тип поискового запроса (например, "movies_search" или "movies_by_filters").
        text_search (str): Текст поискового запроса.
        status_favorites (bool): Статус избранного (True/False).
        status_viewed (bool): Статус просмотренного (True/False).

    Returns:
        Dict[str, str]: Словарь, содержащий данные для записи в таблицу "base_movies".
            Ключи: "user_id", "movie_id", "type_search", "text_search", "name_movie",
                   "alternative_name", "type_movie", "year", "countries", "short_description",
                   "description", "genre", "rating", "age_rating", "poster", "is_series",
                   "is_viewed", "is_favorites".
            Значения: соответствующие значения для каждого ключа, могут быть `None`, если данные отсутствуют.

    Raises:
        ValueError: Если передан пустой или некорректный `text_search` или `type_search`.
    """
    if not text_search or not isinstance(text_search, str):
        raise ValueError("`text_search` должен быть непустой строкой.")
    if not type_search or not isinstance(type_search, str):
        raise ValueError("`type_search` должен быть непустой строкой.")
    if not movie or not isinstance(movie, dict):
        raise ValueError("`movie` должен быть словарем с данными о фильме.")

    return {
        "user_id": str(user_id),
        "movie_id": movie.get("id"),
        "type_search": type_search,
        "text_search": text_search,
        "name_movie": movie.get("name"),
        "alternative_name": movie.get("alternativeName"),
        "type_movie": movie.get("type"),
        "year": movie.get("year"),
        "countries": ", ".join(
            [country.get("name") for country in movie.get("countries", [])]
        ),
        "short_description": movie.get("shortDescription"),
        "description": movie.get("description"),
        "genre": ", ".join([genre.get("name") for genre in movie.get("genres", [])]),
        "rating": movie.get("rating", {}).get("kp"),
        "age_rating": movie.get("ageRating"),
        "poster": movie.get("poster", {}).get("url"),
        "is_series": movie.get("isSeries", False),
        "is_viewed": status_viewed,
        "is_favorites": status_favorites,
    }


@error_logger_func
def write_to_move_postponed(
    user_id: int, movie: Dict[str, str | None]
) -> Dict[str, Dict[str, str] | None]:
    """
    Формирует словарь для сохранения информации о фильме в базе данных MoviePostponed на основе текущего словаря movie.

    Args:
        user_id (int): Идентификатор пользователя, который инициировал запрос.
        movie (Dict[str, str | None]): Информация о фильме в виде словаря, сформированного
            для просмотра фильмов в виде пагинации. Ожидается, что словарь содержит ключи,
            соответствующие полям модели MoviePostponed.

    Returns:
        Dict[str, Dict[str, str] | None]: Словарь, содержащий данные для записи в таблицу "movie_postponed".
            - Ключи: включают информацию о фильме, такие как `movie_id`, `name_movie`, и другие.
            - Значения: соответствующие значения для каждого ключа, могут быть `None`, если данные отсутствуют.

    Raises:
        ValueError: Если передан некорректный словарь `movie`.
    """
    if not isinstance(movie, dict):
        raise ValueError("Некорректный словарь фильма.")

    new_movie = movie.copy()
    new_movie["user_id"] = str(user_id)
    new_movie.pop("type_search", None)
    new_movie.pop("text_search", None)
    return new_movie


@error_logger_func
def sending_to_pagination(
    user_movies: Query, type_search: str = "movie_search"
) -> List[Dict[str, str | None]]:
    """
    Формирует список словарей для отправки данных о фильмах, соответствующих запросу пользователя, в виде пагинации.

    Args:
        user_movies (Query): Список объектов фильма, выбранных из базы данных
            BaseMovie либо MoviePostponed в соответствии с запросом пользователя.
        type_search (str): Тип поискового запроса, определяющий источник данных или критерий поиска.
            По умолчанию "movie_search".

    Returns:
        List[Dict[str, str | None]]: Список словарей, каждый из которых представляет данные о фильме.
            Ключи в словаре включают:
                - "movie_id" (str): Идентификатор фильма.
                - "name_movie" (Optional[str]): Название фильма.
                - "alternative_name" (Optional[str]): Альтернативное название фильма.
                - "type_movie" (str): Тип фильма (например, "фильм" или "сериал").
                - "year" (Optional[str]): Год выпуска фильма.
                - "countries" (Optional[str]): Страны, участвовавшие в создании фильма.
                - "short_description" (Optional[str]): Краткое описание фильма.
                - "description" (Optional[str]): Полное описание фильма.
                - "genre" (str): Жанр фильма.
                - "rating" (Optional[str]): Рейтинг фильма.
                - "age_rating" (Optional[str]): Возрастной рейтинг фильма.
                - "poster" (Optional[str]): Ссылка на постер фильма.
                - "is_series" (bool): Является ли фильм сериалом.
                - "is_viewed" (bool): Просмотрен ли фильм.
                - "is_favorites" (bool): Является ли фильм избранным.
                - "type_search" (str): Тип поискового запроса.
                - "text_search" (str): Текст поискового запроса.

    Raises:
        ValueError: Если передан некорректный`user_movies` или если передан некорректный `type_search`.
        AttributeError: Если у объекта фильма отсутствуют необходимые поля.
    """
    if not isinstance(user_movies, Query):
        raise ValueError("`user_movies` должен быть объектом Query.")
    if not type_search or not isinstance(type_search, str):
        raise ValueError("`type_search` должен быть непустой строкой.")

    try:
        return [
            {
                "user_id": movie.user_id,
                "movie_id": movie.movie_id,
                "name_movie": movie.name_movie,
                "alternative_name": movie.alternative_name,
                "type_movie": movie.type_movie,
                "year": movie.year,
                "countries": movie.countries,
                "short_description": movie.short_description,
                "description": movie.description,
                "genre": movie.genre,
                "rating": movie.rating,
                "age_rating": movie.age_rating,
                "poster": movie.poster,
                "is_series": movie.is_series,
                "is_viewed": movie.is_viewed,
                "is_favorites": movie.is_favorites,
                "type_search": type_search,
                "text_search": (
                    movie.text_search
                    if type_search in ["movie_search", "movie_by_filters"]
                    else ""
                ),
            }
            for movie in user_movies
        ]
    except AttributeError as exc:
        raise AttributeError(f"Ошибка доступа к полям фильма: {exc}")


@error_logger_func
def update_database(
    user_movies: Query, type_search: str = "movie_search"
) -> List[Dict[str, str | None]]:
    """
    Формирует список словарей для отправки данных о фильмах, соответствующих запросу пользователя, в виде пагинации.
    Создает записи в базе данных BaseMovie по данному поисковому запросу. Если в базе уже существуют записи
    по аналогичному поисковому запросу, то перезаписывает их с обновлением id и датой поискового запроса.

    Args:
        user_movies (Query): Список объектов фильма, выбранных из базы данных
            BaseMovie в соответствии с запросом пользователя.
        type_search (str): Тип поискового запроса, определяющий источник данных или критерий поиска.
            По умолчанию "movie_search".

    Returns:
        List[Dict[str, str | None]]: Список словарей, каждый из которых представляет данные о фильме.

    Raises:
        ValueError: Если список передан некорректный `type_search` или передан некорректный`user_movies`.
    """
    if not isinstance(user_movies, Query):
        raise ValueError("`user_movies` должен быть объектом Query.")
    if not type_search or not isinstance(type_search, str):
        raise ValueError("`type_search` должен быть непустой строкой.")

    movies_data = sending_to_pagination(user_movies, type_search)

    for movie in user_movies:
        movie.delete_instance()

    for movie_data in movies_data:
        BaseMovie.create(**movie_data)

    return movies_data


@error_logger_func
def update_database_query(
    user_id: int, text_search: str, type_search: str = "movie_search"
) -> None:
    """
    В базе данных QueryString создает новые записи поискового запроса. Если в базе данных уже существует запись
    по аналогичному поисковому запросу, то перезаписывает эту запись с ее удалением для обновления id
    и даты поискового запроса.

    Args:
        user_id (int): Идентификатор пользователя.
        text_search (str): Текст поискового запроса.
        type_search (str): Тип поискового запроса. По умолчанию "movie_search".

    Raises:
        ValueError: Если передан пустой или некорректный `text_search` или `type_search`.
    """
    if not text_search or not isinstance(text_search, str):
        raise ValueError("`text_search` должен быть непустой строкой.")
    if not type_search or not isinstance(type_search, str):
        raise ValueError("`type_search` должен быть непустой строкой.")

    QueryString.delete().where(
        (QueryString.user_id == user_id) & (QueryString.text_search == text_search)
    ).execute()

    QueryString.create(
        user_id=user_id,
        text_search=text_search,
        type_search=type_search,
    )


@error_logger_func
def sending_to_history_pagination(user_movies: Query) -> List[Dict[str, str]]:
    """
    Формирует словарь отправки данных в пагинацию просмотра истории поисковых запросов на основе
    базы данных QueryString.

    Args:
        user_movies (Query): Список строк поисковых запросов, выбранных из базы данных QueryString
        в соответствии с историей поисковых запросов пользователя.

    Returns:
        List[Dict[str, str]]: Список словарей, каждый из которых представляет строку поискового запроса.
            Ключи в словаре включают:
                - "id_search" (str): Идентификатор фильма.
                - "date" (str): Дата поиска фильма.
                - "type_search" (str): Тип поискового запроса.
                - "text_search" (str): Текст поискового запроса.

    Raises:
        ValueError: Если передан некорректный `user_movies`.
    """
    if not isinstance(user_movies, Query):
        raise ValueError("`user_movies` должен быть объектом Query.")
    return [
        {
            "id_search": movie.id,
            "date": movie.date_search,
            "type_search": movie.type_search,
            "text_search": movie.text_search,
        }
        for movie in user_movies
    ]


@error_logger_func
def toggle_movie_field_response(
    user_id: int, movie: Dict[str, str | None], status: str
) -> None:
    """
    Обновляет указанный статус фильма (`is_favorites` или `is_viewed`) в базах данных BaseMovie и MoviePostponed.

    Если статус установлен в True, а фильм отсутствует в MoviePostponed, он добавляется в эту базу данных.
    Если после обновления оба статуса (`is_favorites` и `is_viewed`) равны False, фильм удаляется
    из базы данных MoviePostponed.

    Args:
        user_id (int): Идентификатор пользователя, который инициировал запрос.
        movie (Dict[str, str | None]): Информация о фильме, включая его статусы и идентификатор.
        status (str): статус фильма (`is_favorites` или `is_viewed`).

    Raises:
        ValueError: Если передан некорректный `movie`.
    """
    if not isinstance(movie, dict):
        raise ValueError("`movie` должен быть словарем.")

    movie_id = movie.get("movie_id")

    # Проверка на наличие фильма в базе данных BaseMovie
    user_movies_base = BaseMovie.select().where(
        (BaseMovie.user_id == user_id) & (BaseMovie.movie_id == movie_id)
    )

    # Проверка на наличие фильма в базе данных MoviePostponed
    user_movies_postponed = (
        MoviePostponed.select()
        .where(
            (MoviePostponed.user_id == user_id) & (MoviePostponed.movie_id == movie_id)
        )
        .first()
    )

    # Если фильм не найден в MoviePostponed и статус активен
    if not user_movies_postponed:
        if movie[status]:
            create_write_mp = write_to_move_postponed(user_id, movie)
            db_write(db, MoviePostponed, [create_write_mp])

    else:
        # Обновление статуса в MoviePostponed
        if status == "is_favorites":
            user_movies_postponed.is_favorites = movie[status]
        elif status == "is_viewed":
            user_movies_postponed.is_viewed = movie[status]
        user_movies_postponed.save()

        # Удаление из MoviePostponed, если оба статуса False
        if (
            not user_movies_postponed.is_favorites
            and not user_movies_postponed.is_viewed
        ):
            user_movies_postponed.delete_instance()

    # Обновление статуса в BaseMovie
    if user_movies_base.exists():
        for movie_entry in user_movies_base:
            if status == "is_favorites":
                movie_entry.is_favorites = movie[status]
            elif status == "is_viewed":
                movie_entry.is_viewed = movie[status]
            movie_entry.save()


@error_logger_func
def search_for_movie(
    user_id: int,
    result_response: List[Dict[str, str | None]],
    type_search: str,
    text_search: str = "",
) -> List[Dict[str, str | None]]:
    """
    Выполняет поиск фильмов, сохраняет поисковый запрос и информацию о фильмах в базы данных, и возвращает список
    данных для пагинации.

    Args:
        user_id (int): Идентификатор пользователя, инициировавшего запрос.
        result_response (List[Dict[str, str | None]]): Список словарей с данными о фильмах, полученными от API.
        type_search (str): Тип поиска, например, "movie_search" или "movies_by_filters".
        text_search (str, optional): Текст поискового запроса. По умолчанию пустая строка.

    Returns:
        List[Dict[str, str | None]]: Список словарей, содержащих данные о фильмах для отправки в пагинацию.

     Raises:
        ValueError: Если передан пустой или некорректный `text_search` или `type_search`.
    """
    if not type_search or not isinstance(type_search, str):
        raise ValueError("`type_search` должен быть непустой строкой.")
    if not isinstance(text_search, str):
        raise ValueError("`text_search` должен быть строкой.")

    if text_search:
        create_write_qs = write_to_query_string(user_id, type_search, text_search)
        db_write(db, QueryString, [create_write_qs])
    movie_info = []

    for movie in result_response:
        film_check = (
            MoviePostponed.select()
            .where(
                (MoviePostponed.user_id == user_id)
                & (MoviePostponed.movie_id == movie["id"])
            )
            .first()
        )

        st_favorites = film_check.is_favorites if film_check else False
        st_viewed = film_check.is_viewed if film_check else False
        send_data = sending_to_pagination_res(
            movie, st_favorites, st_viewed, type_search
        )

        if text_search:
            create_write_bm = write_to_base_movies(
                user_id,
                movie,
                type_search,
                text_search,
                st_favorites,
                st_viewed,
            )
            db_write(db, BaseMovie, [create_write_bm])

        movie_info.append(send_data)
    return movie_info


@error_logger_func
def sending_to_pagination_res(
    movie: Dict[str, Any],
    is_favorites: bool,
    is_viewed: bool,
    type_search: str = "movie_search",
) -> Dict[str, Any]:
    """
    Формирует структуру данных для отображения фильма на странице пагинации, учитывая наличие ключей в исходных
    данных и устанавливая значения по умолчанию, если ключи отсутствуют.

    Args:
        movie (Dict[str, Any]): Словарь с данными о фильме, полученных из поискового запроса.
        is_favorites (bool): Флаг, указывающий, добавлен ли фильм в избранное.
        is_viewed (bool): Флаг, указывающий, был ли фильм просмотрен.
        type_search (str): Тип поиска для идентификации источника поиска. По умолчанию `movie_search`.

    Returns:
        Dict[str, Any]: Словарь с данными о фильме, подготовленными для записи в базу данных или для отображения
            в виде пагинации.

    Raises:
        ValueError: Если передан пустой или некорректный `type_search`.
    """
    if not type_search or not isinstance(type_search, str):
        raise ValueError("`type_search` должен быть непустой строкой.")

    return {
        "movie_id": movie["id"],
        "name_movie": movie["name"],
        "alternative_name": movie.get("alternativeName"),
        "type_movie": movie.get("type"),
        "year": movie.get("year"),
        "countries": ", ".join(
            [country["name"] for country in movie.get("countries", [])]
        ),
        "genre": ", ".join([genre["name"] for genre in movie.get("genres", [])]),
        "short_description": movie.get("shortDescription"),
        "description": movie["description"],
        "rating": movie.get("rating", {}).get("kp"),
        "age_rating": movie.get("ageRating"),
        "poster": movie.get("poster").get("url"),
        "is_series": movie.get("isSeries"),
        "is_favorites": is_favorites,
        "is_viewed": is_viewed,
        "type_search": type_search,
    }
