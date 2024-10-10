from typing import Tuple

from database.common.models_movies import MoviePostponed
from services.services_logging import error_logger_func
from states.search_fields import PostponedStates


@error_logger_func
def data_postponed(callback_data: str) -> Tuple[PostponedStates, bool, str]:
    """
    Определяет состояние, значение статуса и название статуса в зависимости от значения нажатой кнопки
    инлайн-клавиатуры.

    Args:
        callback_data (str): Название нажатой кнопки инлайн-клавиатуры, определяющее, какие данные выбрать.

    Returns:
        Tuple[PostponedStates, bool, str]:
            - PostponedStates: Состояние, соответствующее выбранному режиму просмотра отложенных фильмов (`Избранное`
            или `Просмотренное`).
            - bool: Значение статуса фильма (`0` или `1`), преобразованное в логическое значение (`False` или `True`).
            - str: Название статуса фильма (`is_favorites` или `is_viewed`).

    Raises:
        KeyError: Если `callback_data` не соответствует ожидаемым значениям в словарях `dict_state`, `dict_base_status`
            или `dict_status`.
    """
    dict_state = {
        "favorites": PostponedStates.favorite,
        "viewed": PostponedStates.viewed,
    }

    dict_base_status = {
        "favorites": MoviePostponed.is_favorites,
        "viewed": MoviePostponed.is_viewed,
    }

    dict_status = {
        "favorites": "is_favorites",
        "viewed": "is_viewed",
    }

    if callback_data not in dict_state:
        raise KeyError(
            f"Неизвестный ключ фильтра: {callback_data}. Ожидались значения: {', '.join(dict_state.keys())}"
        )

    status_value = dict_base_status[callback_data]
    status_bool = status_value == "1"

    return (
        dict_state[callback_data],
        status_bool,
        dict_status[callback_data],
    )
