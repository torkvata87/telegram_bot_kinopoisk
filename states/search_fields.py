from telebot.handler_backends import State, StatesGroup


class SearchStates(StatesGroup):
    """
    Состояния, используемые для поиска фильмов.
    """
    query = State()
    movie_name = State()
    sorting = State()
    sort_direction = State()
    sort_type = State()
    type = State()
    year = State()
    rating = State()
    genres = State()
    countries = State()
    countries_input = State()


class HistoryStates(StatesGroup):
    """
    Состояния, используемые для работы с историей поиска.
    """
    query = State()
    filters = State
    period = State()
    type = State()
    clear = State()
    date = State()
    search = State()


class PostponedStates(StatesGroup):
    """
    Состояния, используемые для работы с избранными или просмотренными фильмами.
    """
    postponed = State()
    favorite = State()
    viewed = State()
    pagination_history = State()


class PaginationStates(StatesGroup):
    """
    Состояния, используемые для работы с пагинацией.
    """
    movies = State()
    history = State()


class StartStates(StatesGroup):
    """
    Состояние, используемое для команды /start.
    """
    start = State()
