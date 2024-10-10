from datetime import datetime, timedelta
from typing import Dict

from peewee import fn, Query

from config_data.config import DATE_FORMAT
from database.common.models_movies import QueryString, BaseMovie

from services.services_logging import error_logger_func


dict_type: Dict[str, str] = {
    "по названию": "movie_search",
    "по фильтрам": "movie_by_filters",
}

dict_time: Dict[str, int] = {"за сутки": 1, "за неделю": 7, "за месяц": 30}


@error_logger_func
def get_history_query_type(data: Dict[str, str], query_data: Query) -> Query:
    """
    Определяет тип запроса истории на основе данных.

    Args:
        data (Dict[str, str]): Словарь с данными, определяющими условия запроса истории.
        query_data (Query): Исходный запрос истории пользователей.

    Returns:
        Query: Обновленный запрос истории на основе выбранного пользователем типа.

    Raises:
        ValueError: Если передан некорректный `query_data`.
    """
    if not isinstance(query_data, Query):
        raise ValueError("`user_movies` должен быть объектом Query.")

    return (
        query_data.where(
            QueryString.type_search == dict_type[data.get("history_type", "")]
        )
        if data.get("history_type") in dict_type
        else query_data
    )


@error_logger_func
def get_history_query_string(data: Dict[str, str], query_data: Query) -> Query:
    """
    Определяет строку запроса истории на основе данных.

    Args:
        data (Dict[str, str]): Словарь с данными, определяющими условия запроса истории.
        query_data (Query): Исходный запрос истории пользователей.

    Returns:
        Query: Обновленный запрос истории на выбранный пользователем период.

    Raises:
        ValueError: Если передан некорректный`query_data` или дата в `history_date` некорректна или отсутствует.
    """
    if not isinstance(query_data, Query):
        raise ValueError("`user_movies` должен быть объектом Query.")

    history_period = data.get("history_period")
    if history_period == "за неделю":
        query_data = query_data.where(
            QueryString.date_search >= datetime.now() - timedelta(days=7)
        )
    elif history_period == "за месяц":
        query_data = query_data.where(
            QueryString.date_search >= datetime.now() - timedelta(days=30)
        )
    elif history_period == "по дате":
        history_date = data.get("history_date")
        if not history_date:
            raise ValueError("Дата должна быть указана для фильтра 'по дате'.")
        query_data = query_data.where(
            fn.strftime(DATE_FORMAT, QueryString.date_search) == history_date
        )
    return query_data


@error_logger_func
def history_query_type_clear(user_id: int, data: Dict[str, str]) -> None:
    """
    Очищает историю на основе заданных пользователем параметров.

    Args:
        user_id (int): Идентификатор пользователя.
        data (Dict[str, str]): Словарь с данными, определяющими условия очистки истории.

    Raises:
        KeyError: Если значение `history_clear_type` отсутствует в словаре `dict_type` или `dict_time`.
    """
    clear_type = data.get("btns_history_clear")
    if clear_type in dict_type:
        query_type = dict_type.get(clear_type)
        if query_type:
            QueryString.delete().where(
                (QueryString.user_id == user_id)
                & (QueryString.type_search == query_type)
            ).execute()
            BaseMovie.delete().where(
                (BaseMovie.user_id == user_id)
                & (BaseMovie.type_search == query_type)
            ).execute()
        else:
            raise KeyError(f"Неверный тип очистки истории: {clear_type}")

    elif data.get("btns_history_clear") in dict_time:
        date_period = datetime.now() - timedelta(
            days=dict_time[data["btns_history_clear"]]
        )
        QueryString.delete().where(
            (QueryString.user_id == user_id)
            & (QueryString.date_search >= date_period)
        ).execute()
        BaseMovie.delete().where(
            (BaseMovie.user_id == user_id) & (BaseMovie.date_search >= date_period)
        ).execute()

    elif data.get("btns_history_clear") == "полностью":
        QueryString.delete().where(QueryString.user_id == user_id).execute()
        BaseMovie.delete().where(BaseMovie.user_id == user_id).execute()

    else:
        raise KeyError(f"Неверный тип очистки: {data.get('btns_history_clear')}")
