from typing import Any, Dict

import requests

from config_data.config import SiteSettings
from services.services_logging import error_logger_func


site = SiteSettings()


@error_logger_func
def api_request(params: Dict[str, Any], url_end: str) -> dict[str, Any] | None:
    """
    Выполняет GET-запрос к API с использованием заданных параметров и возвращает результат в формате JSON.

    Args:
        params (Dict[str, Any]): Словарь с параметрами запроса для передачи в строку запроса URL.
        url_end (str): Конечная часть URL, которая добавляется к основному хосту API.

    Returns:
        dict[str, Any] | None: JSON-ответ от API в виде словаря с данными фильмов. В случае отсутствия JSON-ответ
            возвращается None.
    """
    url = f"{site.host_api}{url_end}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": site.api_key.get_secret_value(),
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)

    if response.status_code:
        return response.json()
    return None
