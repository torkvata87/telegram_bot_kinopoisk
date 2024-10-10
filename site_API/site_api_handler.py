from typing import Any, Dict, List, Tuple

from logs.exceptions import ServerRequestError
from services.services_logging import error_logger_func
from site_API.core import api_request


@error_logger_func
def remove_trailing_vowels(word: str) -> str:
    """
    Удаляет конечные гласные буквы и мягкий знак из строки.
    Учитываются гласные буквы русского алфавита: "а", "е", "ё", "и", "о", "у", "ы", "э", "ю", "я" и мягкий знак "ь".

    Args:
        word (str): Строка, из которой нужно удалить конечные гласные буквы и мягкий знак.

    Returns:
        str: Обновленная строка без конечных гласных букв и мягкого знака.
    """
    vowels = "аеёиоуыэюяь"
    while word and word[-1] in vowels:
        word = word[:-1]
    return word


@error_logger_func
def search_movies(
    search_criteria: Dict[str, Any] | str, type_search: str, page: int = 1
) -> Tuple[List[Dict[str, Any] | None], int] | str:
    """
    Универсальный поиск фильмов по названию или фильтрам.

    Args:
        search_criteria (Dict[str, Any] | str): Критерии поиска. Может быть либо строкой с названием фильма,
            либо словарем с фильтрами.
        type_search (str): Тип поиска. Возможные значения: `movie_by_filters` или `movie_search`.
        page (int): Номер страницы для пагинации результатов поиска. По умолчанию 1.

    Returns:
        Tuple[List[Dict[str, Any] | None], int] | str: Список фильмов и номер страницы или строка с описанием ошибки.

    Raises:
        ValueError: Если тип поиска не является `movie_by_filters` или `movie_search`.
        ConnectionError: Если не получен ответ при запросе с сервера в формате JSON.
        ServerRequestError: Если при запросе на сервер ответ пришел с отрицательным ответом  в формате JSON.
    """
    if type_search not in {"movie_by_filters", "movie_search"}:
        raise ValueError(f"Недопустимый тип поиска: {type_search}")

    if type_search == "movie_search":
        endpoint = "/v1.4/movie/search"
        params = {"page": page, "limit": 15, "query": search_criteria}
    else:
        endpoint = "/v1.4/movie"
        params = {
            "page": page,
            "limit": 15,
            "selectFields": [
                "id",
                "name",
                "alternativeName",
                "description",
                "shortDescription",
                "type",
                "isSeries",
                "year",
                "rating",
                "genres",
                "countries",
                "poster",
                "ageRating",
            ],
            "sortField": search_criteria.get("type_sort", "rating.kp"),
            "sortType": search_criteria.get("sort", "-1"),
            "type": search_criteria.get("type", ("movie", "tv-series")),
            "year": search_criteria.get("year"),
            "rating.kp": search_criteria.get("rating", "7-10"),
            "genres.name": search_criteria.get("genres", "драма"),
            "countries.name": search_criteria.get("countries"),
        }
    response = api_request(params, endpoint)
    if not response:
        raise ConnectionError("Не удалось установить соединение с сервером")

    if "docs" not in response:
        status_code = response.get("statusCode", "не установлен")
        message = response.get("message", "Ошибка не определена сервером")
        raise ServerRequestError(status_code, message)

    films = response.get("docs", [])
    if not films:
        return [], response.get("pages", 0)
    filtered_films = [
        film
        for film in films
        if film.get("shortDescription") or film.get("description")
    ]
    if type_search == "movie_search":
        search_words = [
            remove_trailing_vowels(word) for word in search_criteria.lower().split()
        ]
        filtered_films = [
            film
            for film in filtered_films
            if any(word in film.get("name", "").lower() for word in search_words)
        ]
    return filtered_films, response.get("pages", 0)
