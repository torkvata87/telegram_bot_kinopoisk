import re
from datetime import datetime
from typing import Any, List, Dict, Tuple

from telebot.types import InlineKeyboardMarkup

from keyboards.buttons.btns_for_movie_by_filters import (
    btns_movies_type,
    buttons_sort_type,
    buttons_genres,
    buttons_countries,
    buttons_sorting,
    buttons_re_entry_year,
)
from keyboards.inline.inline_keyboard import create_inline_keyboard
from keyboards.inline.inline_movie_by_filters import (
    select_type_keyboard,
    select_genres_keyboard,
    select_countries_keyboard,
    select_rating_keyboard,
)
from services.services_logging import error_logger_func
from states.search_fields import SearchStates


def data_filters(filters: str) -> Tuple[SearchStates, str, InlineKeyboardMarkup]:
    """
    В зависимости от значения `key_filters`, функция возвращает состояние, текстовое сообщение и клавиатуру,
    соответствующие выбранному фильтру.

    Args:
        filters (str): Ключ фильтра, определяющий, какой фильтр выбрать.
           Ожидаемые значения:
           - "type_filter": Фильтр по типу контента.
           - "genre_filter": Фильтр по жанрам.
           - "country_filter": Фильтр по странам.
           - "year_filter": Фильтр по году.
           - "rating_filter": Фильтр по рейтингу.
           - "sort_filter": Фильтр по сортировке.

    Returns:
        Tuple[SearchStates, str, InlineKeyboardMarkup]:
            - SearchStates: Состояние, соответствующее выбранному фильтру.
            - str: Текстовое сообщение, описывающее, что нужно задать в фильтре.
            - InlineKeyboardMarkup: Клавиатура для выбора фильтра.
    """
    keyboard_type = select_type_keyboard(btns_movies_type, buttons_per_row=3)
    keyboard_genres = select_genres_keyboard(buttons_genres, buttons_per_row=4)
    keyboard_country = select_countries_keyboard(
        buttons_countries, buttons_per_row=3, include_other_option=True
    )
    keyboard_year = create_inline_keyboard(buttons_re_entry_year, buttons_per_row=1)
    keyboard_rating = select_rating_keyboard()
    keyboard_sort = create_inline_keyboard(buttons_sorting, buttons_per_row=1)

    text_type = "✔️ Задайте один или несколько <b><i>типов</i></b> фильма."
    text_genres = (
        "✔️ Задайте один или несколько <b><i>жанров</i></b>.\n\n"
        "Для исключения из поиска кликните <b>"
        '<i>"❌ Исключить"</i></b> перед кликом на исключаемый жанр.'
    )
    text_country = "✔️ Задайте <b><i>страну</i></b>."
    text_year = (
        '✍️ Введите <b><i>год</i></b> в строку ввода в формате <b>"ГГГГ"</b> '
        'или диапазоном <b>"ГГГГ-ГГГГ"</b>.'
    )
    text_rating = (
        "✔️ Задайте <b><i>рейтинг</i></b> или его диапазон двумя кликами.\n\n"
        'Пример: <i>"7"</i>, <i>"7-10"</i>'
    )
    text_sort = "✔️ Задайте <b><i>фильтры</i></b> для <b><i>сортировки</i></b>."

    dict_state = {
        "type_filter": SearchStates.type,
        "genre_filter": SearchStates.genres,
        "country_filter": SearchStates.countries,
        "year_filter": SearchStates.year,
        "rating_filter": SearchStates.rating,
        "sort_filter": SearchStates.sorting,
    }

    dict_text = {
        "type_filter": text_type,
        "genre_filter": text_genres,
        "country_filter": text_country,
        "year_filter": text_year,
        "rating_filter": text_rating,
        "sort_filter": text_sort,
    }

    dict_keyboard = {
        "type_filter": keyboard_type,
        "genre_filter": keyboard_genres,
        "country_filter": keyboard_country,
        "year_filter": keyboard_year,
        "rating_filter": keyboard_rating,
        "sort_filter": keyboard_sort,
    }

    return dict_state[filters], dict_text[filters], dict_keyboard[filters]


@error_logger_func
def set_letter(list_parameters: List[str], letter: str = "а") -> str:
    """
    Для коррекции грамматики в тексте на основе количества выбранных пользователем параметров устанавливает
    для слов множественное или единственное число.

    Args:
        list_parameters (List): Список параметров, выбранных пользователем.
        letter (str): Буква или символ, которые должны быть установлена на конце слова в его единственном числе.
            По умолчанию "а".

    Returns:
        str: Буква или символ на конце слова, в зависимости от количества выбранных пользователем параметров.

    Raises:
        ValueError: Если передан некорректный`list_parameters`.
    """
    if not isinstance(list_parameters, list):
        raise ValueError("`list_parameters` должен быть списком.")
    return letter if len(list_parameters) == 1 else "ы"


@error_logger_func
def format_genres_list(raw_list_genres: List[str]) -> List[str]:
    """
    Преобразует список первоначально выбранных пользователем жанров в формат, соответствующий требованиям
    поискового запроса.

    Действия:
        1. Объединяет элементы списка в строку с разделителем ", ".
        2. Применяет несколько регулярных выражений для исправления форматирования:
           - Заменяет последовательности "!, +" на "!, ".
           - Исправляет случаи "!, !" на "!, ", исключая несколько идущих подряд одинаковых символов исключения
           жанра на один символ "!".
           - Заменяет "18+" на "для взрослых".
           - Заменяет "д/ф" на "документальный".
        3. Удаляет лишнюю запятую и пробел в конце строки, если они присутствуют.
        4. Делит строку по разделителю ", " и возвращает список жанров.

    Args:
        raw_list_genres (List[str]): Список жанров, выбранных пользователем, в исходном формате.

    Returns:
        List[str]: Отформатированный список жанров, соответствующий требованиям поискового запроса.

    Raises:
        ValueError: Если `raw_list_genres` не является списком строк.
    """
    if not isinstance(raw_list_genres, list) or not all(
        isinstance(i, str) for i in raw_list_genres
    ):
        raise ValueError("Ошибка: Ожидается список строк в качестве входных данных.")

    string = ", ".join(raw_list_genres)
    string = re.sub(pattern=r"(!,\s*)+", repl="!, ", string=string)
    string = re.sub(pattern=r"(!,\s!)", repl="!, ", string=string)
    string = re.sub(pattern=r"!,\s\+", repl="!", string=string)
    string = re.sub(pattern=r"18\+", repl="для взрослых", string=string)
    string = re.sub(pattern=r"д/ф", repl="документальный", string=string)

    if string.endswith(", !, "):
        string = string[:-5]

    return string.split(", ")


@error_logger_func
def format_genres_string(genres: List[str], for_database: bool = False) -> str:
    """
    Форматирует список жанров в строку с учетом указателей на включение или исключение жанров.

    Действия:
        1. Разделяет список жанров на списки жанров, которые следует включить или исключить из результатов поискового
        запроса с удалением "+" и "!".
        2. Если строка формируется для записи в базу данных, то включенные жанры помечаются эмодзи "✔️",
        а исключенные — "✖️". В противном случае, строка форматируется для отображения пользователю.

    Args:
        genres (List[str]): Список жанров с указателями "+" для включения и "!" для исключения.
        for_database (bool): Флаг, указывающий, нужно ли форматировать строку для базы данных. По умолчанию False.

    Returns:
        str: Отформатированная строка жанров.

    Raises:
        ValueError: Если формат входных данных некорректный или пустой список жанров.

    Examples:
        Входной список: ["+комедия", "!криминал", "!для взрослых", "+документальный"].
        Строка для пользователя: "Жанры: комедия, документальный, исключены криминал, для взрослых".
        Строка для базы данных: "✔️ комедия, документальный, ✖️ криминал, для взрослых"
    """
    if not genres or not isinstance(genres, list):
        raise ValueError("Список жанров должен быть непустым списком строк.")

    included_genres = [genre.lstrip("+") for genre in genres if genre.startswith("+")]
    excluded_genres = [genre.lstrip("!") for genre in genres if genre.startswith("!")]

    if for_database:
        included_str = "✔️ " + ", ".join(included_genres) if included_genres else ""
        excluded_str = "✖️ " + ", ".join(excluded_genres) if excluded_genres else ""
        explanation = ""
        separator = ", "
    else:
        colon_1 = "" if not included_genres else ":"
        colon_2 = "" if included_genres else ":"
        letter = (
            ""
            if (not included_genres and len(excluded_genres) == 1)
            or (len(included_genres) == 1 and not excluded_genres)
            else "ы"
        )

        explanation = f"<b>Жанр{letter}{colon_1}</b> "

        included_str = ", ".join(included_genres)
        excluded_str = (
            f"<b>исключен{set_letter(excluded_genres, letter='')}{colon_2} </b>{', '.join(excluded_genres)}"
            if excluded_genres
            else ""
        )
        separator = "\n"

    if included_str and excluded_str:
        return f"{explanation}{included_str}{separator}{excluded_str}"
    elif included_str:
        return f"{explanation}{included_str}"
    else:
        return f"{explanation}{excluded_str}"


@error_logger_func
def is_valid_year(message: Any) -> bool:
    """
    Проверяет, является ли введенный текст годом или диапазоном годов в пределах от 1920 до текущего года.

    Действия:
        - Проверяет после удаления пробельных символов, задал ли пользователь собой один год
        или диапазон годов.
        - Проверяет, является ли введенный текст числами.
        - Проверяет, находиться ли введенный год или диапазон годов должен в пределах от 1920 до текущего года.

    Args:
        message (Any): Объект сообщения, содержащий текст с годом или диапазоном годов.
            - message.text (str): Текст сообщения.

    Returns:
        bool: True, если текст сообщения соответствует году или диапазону годов в пределах от 1920 до текущего года,
            иначе False.

    Raises:
        AttributeError: Если у объекта `message` нет атрибута `text`.

    Examples:
        - "1995" вернет True.
        - "2000-2010" вернет True.
        - "1919" вернет False.
        - "2025" вернет False, если текущий год — 2024.
    """
    current_year = datetime.now().year

    if not hasattr(message, "text"):
        raise AttributeError("Объект сообщения должен содержать атрибут 'text'.")

    text = message.text.strip().strip("-").split("-")

    if len(text) > 2:
        return False
    for elem in text:
        if not elem.isdigit():
            return False
        year = int(elem)
        return 1920 <= year <= current_year

    return False


@error_logger_func
def normalize_year_range(year_input: str) -> str:
    """
    Нормализует введённый год или диапазон лет, обеспечивая корректный формат.

    Действия:
        - Разделяет строку по символу "-" на отдельные годы, если это диапазон.
        - Если ввод представляет собой один год или оба года в диапазоне равны, возвращает один год.
        - Возвращает диапазон лет, упорядочивая их по возрастанию.

    Args:
        year_input (str): Строка, содержащая год или диапазон годов.

    Returns:
        str: Корректный год или диапазон, где первое число меньше второго.

    Raises:
        ValueError: Если входная строка не является годом или диапазоном годов.

    Examples:
        - "1995" вернет "1995".
        - "2010-2010" вернет "2010".
        - "2025-2023" вернет "2023-2025".
    """
    year_list = year_input.split("-")

    if len(year_list) > 2 or not all(y.isdigit() for y in year_list):
        raise ValueError("Некорректный формат года или диапазона годов.")

    if len(year_list) == 1 or year_list[0] == year_list[1]:
        return str(year_list[0])
    return f"{min(year_list)}-{max(year_list)}"


@error_logger_func
def generate_filter_parameters(
    filter_data: Dict[str, Any], for_search: bool = False
) -> Dict[str, Any]:
    """
    Формирует и возвращает словарь параметров фильтрации на основе данных, полученных из хранилища.

    Действия:
        - Если параметр `for_search` установлен в `True`, функция преобразует списки жанров и типов в кортежи,
          а также добавляет исключаемые жанры (`концерт`, `церемония`, `ток-шоу`).
        - В обычном режиме возвращает параметры фильтрации в виде строк и списков.

    Args:
        filter_data (Dict[str, Any]): Словарь с исходными данными, включая параметры фильтрации.
            - `genres`: Список жанров (по умолчанию [`+драма`]).
            - `type`: Список типов фильмов (по умолчанию [`movie`, `tv-series`]).
            - `rating`: Рейтинг фильмов (по умолчанию `7-10`).
            - `type_sort`: Тип сортировки (по умолчанию `rating.kp`).
            - `sort`: Порядок сортировки (по умолчанию `-1`).
            - `year`: Год фильтра (по умолчанию None).
            - `countries`: Список стран (по умолчанию None).
        for_search (bool): Флаг, указывающий, должен ли быть подготовлен словарь для поиска, с преобразованием
                          списков в кортежи и добавлением исключаемых жанров. По умолчанию False.

    Returns:
        Dict[str, Any]: Словарь с параметрами фильтрации:
            - `type`: Типы фильмов (в виде списка или кортежа в зависимости от `for_search`).
            - `genres`: Жанры фильмов (в виде списка или кортежа в зависимости от `for_search`).
            - `rating`: Рейтинг фильмов в виде строки.
            - `type_sort`: Тип сортировки в виде строки.
            - `sort`: Порядок сортировки в виде строки.
            - `year`: Год фильтра в виде строки или None.
            - `countries`: Страны (в виде кортежа или None в зависимости от `for_search`).

    Raises:
        ValueError: Если передаваемые данные не являются словарем.
    """
    if not isinstance(filter_data, dict):
        raise ValueError("Входные данные должны быть переданы в виде словаря")

    genres = filter_data.get("genres", ["+драма"])
    type_movies = filter_data.get("type", ["movie", "tv-series"])
    countries = filter_data.get("countries", None)

    if for_search:
        type_movies = tuple(type_movies)
        list_exclude = ["!концерт", "!церемония", "!ток-шоу"]
        genres.extend(list_exclude)
        genres = tuple(genres)
        countries = tuple(countries) if countries else None

    return {
        "type": type_movies,
        "genres": genres,
        "rating": filter_data.get("rating", "7-10"),
        "type_sort": filter_data.get("type_sort", "rating.kp"),
        "sort": filter_data.get("sort", "-1"),
        "year": filter_data.get("year", None),
        "countries": countries,
    }


@error_logger_func
def format_filter_data(
    filter_data: Dict[str, List | str], for_database: bool = False
) -> List[Dict[str, List | str]]:
    """
    Форматирует данные фильтров в виде списка словарей.

    Действия:
        - Форматирует строку с жанрами, учитывая, что она может быть предназначена для базы данных.
        - Объединяет и форматирует типы фильмов, страны, годы и другие параметры в список словарей.

    Args:
        filter_data (Dict[str, List | str]): Словарь с данными фильтров.
        for_database (bool): Флаг, указывающий, нужно ли форматировать данные для базы данных. По умолчанию False.

    Returns:
        List[Dict[str, List | str]]: Список словарей, представляющий отформатированные данные фильтров.

    Raises:
        ValueError: Если передаваемые данные не являются словарем.
    """
    if not isinstance(filter_data, dict):
        raise ValueError("Входные данные должны быть переданы в виде словаря")

    type_movies = [btns_movies_type[elem] for elem in filter_data["type"]]
    genres = filter_data["genres"]

    genres_str = format_genres_string(genres, for_database=for_database)
    countries = (
        ", ".join(filter_data["countries"]) if filter_data["countries"] else ""
    )
    sort_num = filter_data["sort"]
    sort = "по убыванию" if sort_num == "-1" else "по возрастанию"

    text_sort = f"{buttons_sort_type[filter_data.get('type_sort')]} {sort}"

    return [
        {"🎞️ Тип:": ", ".join(type_movies)},
        {"🎭 ": genres_str if genres else ""},
        {"🗓️ Год:": filter_data["year"]},
        {"🌍 Страна:": countries},
        {"🏆 Рейтинг:": filter_data["rating"]},
        {"🔃 Сортировка:": text_sort},
    ]


@error_logger_func
def format_filters_to_string(
    filters_list: List[Dict[str, List[str] | str]], for_database: bool = False
) -> str:
    """
    Форматирует список фильтров в строку для вывода пользователю или для записи в базу данных.

    Действия:
        - Если требуется форматирование для базы данных, то возвращает строку, в которой ключи разделены пробелами.
        - Если форматирование нужно для вывода пользователю, оборачивает ключи фильтров в HTML-теги и возвращает строку.

    Args:
        filters_list (List[Dict[str, List[str] | str]]): Список фильтров, где каждый фильтр представлен
            как словарь.
        for_database (bool): Флаг, указывающий, следует ли форматировать строку для базы данных. По умолчанию False.

    Returns:
        str: Отформатированная строка фильтров.

    Raises:
        ValueError: Если список фильтров пуст или имеет некорректный формат.

    Examples:
        - Форматирование для базы данных: "🎞️ Тип: комедия, драма, 🎭 Жанры: ✔️ комедия, драма".
        - Форматирование для пользователя: "<b><i>🎞️ Тип:</i></b> комедия, драма".
    """
    if not filters_list or not isinstance(filters_list, list):
        raise ValueError("Список фильтров должен быть непустым списком словарей.")

    if for_database:
        return ", ".join(
            [
                f"{key[0]} {value}"
                for elem in filters_list
                for key, value in elem.items()
                if value
            ]
        )
    return "\n\n".join(
        [
            f"<b><i>{key}</i></b> <i>{value}</i>"
            for elem in filters_list
            for key, value in elem.items()
            if value
        ]
    )
