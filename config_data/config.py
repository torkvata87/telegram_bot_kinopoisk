import os

from dotenv import load_dotenv, find_dotenv
from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings

from logs.logging_config import log


# Загрузка переменных окружения из файла .env
if not find_dotenv():
    log.error("Отсутствует файл .env. Программа завершила работу.")
    exit("Переменные окружения не загружены: отсутствует файл .env")
else:
    load_dotenv()

# Токен бота для Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    log.error("Отсутствует BOT_TOKEN. Программа завершила работу.")
    exit("Отсутствует BOT_TOKEN. Пожалуйста, укажите BOT_TOKEN в файле .env")


# Команды бота по умолчанию
DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("movie_search", "Поиск фильма по названию"),
    ("movie_by_filters", "Поиск фильмов/сериалов по фильтрам"),
    ("postponed_movies", "Просмотр избранных и просмотренных фильмов"),
    ("history", "Управление историей поисковых запросов"),
    ("help", "Вывести справочную информацию"),
)

# Пути к базам данных
DB_PATH_IMAGES = "./database/database_images.db"
DB_PATH_MOVIES = "./database/database_movies.db"

# Пути к изображениям
IMAGE_HELP = "./img/help.jpg"
IMAGE_HISTORY = "./img/history.jpg"
IMAGE_MOVIE_BY_FILTERS = "./img/movie_by_filters.jpg"
IMAGE_MOVIE_SEARCH = "./img/movie_search.jpg"
IMAGE_POSTPONED_MOVIES = "./img/postponed.jpg"
IMAGE_START = "./img/start.jpg"
IMAGE_EMPTY_POSTER = "./img/empty_poster.jpg"

# Форматы дат
DATE_FORMAT = "%Y-%m-%d"
DATE_FORMAT_STRING = "%d.%m.%Y"


class SiteSettings(BaseSettings):
    """
    Настройки сайта, загружаемые из переменных окружения.

    Атрибуты:
        api_key (SecretStr): API ключ для доступа к внешним сервисам.
        host_api (str): Базовый URL для доступа к API.
    """
    api_key: SecretStr = os.getenv("API_KEY", None)
    host_api: str = os.getenv("API_URL", None)

    def __init__(self, **kwargs):
        """
        Инициализирует экземпляр SiteSettings.
        Наследует и вызывает конструктор базового класса BaseSettings.

        Проверяет наличие необходимых переменных окружения.
        Если переменные отсутствуют, программа завершает работу с соответствующим сообщением.

        Args:
            **kwargs: Дополнительные именованные аргументы, передаваемые в конструктор BaseSettings.

        Raises:
            ValidationError: Если переменная окружения `API_KEY` или `API_URL` не найдена.
        """
        try:
            super().__init__(**kwargs)
        except ValidationError as exc:
            variables = []
            for error in exc.errors():
                field = error.get("loc")[0]
                if field == "api_key":
                    log.error("Отсутствует API_KEY. Программа завершила работу.")
                    variables.append("API_KEY")

                elif field == "host_api":
                    log.error("Отсутствует API_URL. Программа завершила работу.")
                    variables.append("API_URL")

            variables_str = ", ".join(variables)
            exit(
                f"Отсутствуют необходимые переменные окружения: {variables_str}. "
                f"Пожалуйста, укажите {variables_str} в файле .env."
            )
