class BotStatePaginationNotFoundError(Exception):
    """Исключение, вызываемое, если состояние бота отсутствует."""
    def __init__(self, message="Текущее состояние пользователя отсутствует"):
        self.message = message
        super().__init__(self.message)


class ServerRequestError(Exception):
    """Исключение для ошибок, связанных с неверным запросом на сервер."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Ошибка сервера {status_code}: {message}")
