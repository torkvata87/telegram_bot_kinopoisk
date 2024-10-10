from datetime import datetime

from peewee import (
    AutoField,
    BooleanField,
    CharField,
    DateField,
    Model,
    SqliteDatabase,
    TextField,
)

from config_data.config import DB_PATH_MOVIES

db = SqliteDatabase(DB_PATH_MOVIES)


class BaseModel(Model):
    """
    Базовая модель, от которой наследуются все остальные модели базы данных.

    Attributes:
        id (AutoField): Уникальный идентификатор записи (автоматически увеличивается).
        date_search (DateField): Дата создания записи, по умолчанию текущая дата.
        user_id (CharField): Идентификатор пользователя.
    """
    id = AutoField()
    date_search = DateField(default=datetime.now)
    user_id = CharField()

    class Meta:
        """
        Метаданные для модели BaseModel.

        Attributes:
            database (SqliteDatabase): База данных, используемая для хранения данной модели.
        """
        database = db


class QueryString(BaseModel):
    """
    Модель, представляющая строку поискового запроса. Наследуется от BaseModel.

    Attributes:
        type_search (CharField): Тип поискового запроса (например, `movies_search` либо `movies_by_filters`).
        text_search (CharField, optional): Текст поискового запроса на основе введенных пользователем данных.
    """
    type_search = CharField()
    text_search = TextField(default="")

    class Meta:
        """
        Метаданные для модели QueryString.

        Attributes:
            table_name (str): Имя таблицы в базе данных, соответствующей данной модели.
        """

        table_name = "query_string"


class CommonMovieFields(BaseModel):
    """
    Общие поля для моделей фильмов. Наследуется от BaseModel.

    Attributes:
        movie_id (CharField): Идентификатор фильма.
        name_movie (TextField, optional): Название фильма.
        alternative_name (CharField, optional): Альтернативное название фильма.
        type_movie (CharField, optional): Тип фильма (например, фильм, сериал).
        year (CharField, optional): Год выпуска фильма.
        countries (CharField, optional): Страны, участвовавшие в создании фильма.
        genre (TextField, optional): Жанр фильма.
        rating (CharField, optional): Рейтинг фильма.
        age_rating (CharField, optional): Возрастной рейтинг фильма.
        short_description (TextField, optional): Краткое описание фильма.
        description (TextField, optional): Полное описание фильма.
        poster (TextField, optional): Ссылка на постер фильма.
        is_series (BooleanField): Является ли фильм сериалом. По умолчанию False.
        is_viewed (BooleanField): Просмотрен ли фильм. По умолчанию False.
        is_favorites (BooleanField): Является ли фильм избранным. По умолчанию False.
    """

    movie_id = CharField()
    name_movie = TextField(null=True)
    alternative_name = CharField(null=True)
    type_movie = CharField(null=True)
    year = CharField(null=True)
    countries = CharField(null=True)
    genre = TextField(null=True)
    rating = CharField(null=True)
    age_rating = CharField(null=True)
    short_description = TextField(null=True)
    description = TextField(null=True)
    poster = TextField(null=True)
    is_series = BooleanField(null=True)
    is_viewed = BooleanField(default=False)
    is_favorites = BooleanField(default=False)

    class Meta:
        """
        Метаданные для модели CommonMovieFields.

        Attributes:
            abstract (bool): Указывает, что данная модель является абстрактной.
        """
        abstract = True


class BaseMovie(CommonMovieFields):
    """
    Модель, представляющая базовый фильм. Наследуется от CommonMovieFields.

    Attributes:
        type_search (CharField): Тип поиска.
        text_search (TextField): Текст поискового запроса.
    """
    type_search = CharField(default="")
    text_search = TextField(default="")

    class Meta:
        """
        Метаданные для модели BaseMovie.

        Attributes:
            table_name (str): Имя таблицы в базе данных, соответствующей данной модели.
        """
        table_name = "base_movies"


class MoviePostponed(CommonMovieFields):
    """
    Модель, представляющая отложенный фильм.
    Наследуется от CommonMovieFields.
    """
    class Meta:
        """
        Метаданные для модели BaseMovie.

        Attributes:
            table_name (str): Имя таблицы в базе данных, соответствующей данной модели.
        """
        table_name = "movies_postponed"
