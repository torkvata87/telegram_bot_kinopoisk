from peewee import CharField, Model, SqliteDatabase

from config_data.config import DB_PATH_IMAGES


db_image = SqliteDatabase(DB_PATH_IMAGES)


class ImageFile(Model):
    """
    Модель, представляющая изображение, сохраненное в базе данных.

    Attributes:
        chat_id (CharField): Идентификатор чата, к которому привязано изображение.
        image_name (CharField): Уникальное имя изображения.
        file_id (CharField): Идентификатор файла изображения.
    """
    chat_id = CharField()
    image_name = CharField(unique=True)
    file_id = CharField()

    class Meta:
        """
        Метаданные для модели ImageFile.

        Attributes:
            database (SqliteDatabase): База данных, используемая для хранения данной модели.
        """
        database = db_image
