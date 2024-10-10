from typing import Callable

from peewee import DoesNotExist

from ..common.model_images import ImageFile


def _save_file_id(chat_id: int, image_name: str, file_id: str) -> None:
    """
    Сохраняет идентификатор файла изображения в базе данных. Если запись с указанным chat_id и image_name
    уже существует, она будет заменена.

    Args:
        chat_id (str): Идентификатор чата, к которому привязано изображение.
        image_name (str): Уникальное имя изображения.
        file_id (str): Идентификатор файла изображения.
    """
    ImageFile.insert(
        chat_id=chat_id, image_name=image_name, file_id=file_id
    ).on_conflict_replace().execute()


def _get_file_id(chat_id: int, image_name: str) -> str | None:
    """
    Извлекает идентификатор файла изображения из базы данных по указанному chat_id и image_name.

    Args:
        chat_id (str): Идентификатор чата, к которому привязано изображение.
        image_name (str): Уникальное имя изображения.

    Returns:
        str | None: Идентификатор файла изображения, если запись найдена; иначе None.

    Raises:
        DoesNotExist: Если возникла ошибка при работе с обработкой данных базы данных.
    """
    try:
        image_file = ImageFile.get(
            (ImageFile.chat_id == chat_id) & (ImageFile.image_name == image_name)
        )
        return image_file.file_id
    except DoesNotExist:
        return None


class CRUDInterfaceImage:
    """
    Интерфейс для работы с изображениями в базе данных. Предоставляет методы для сохранения и извлечения
    идентификаторов файлов изображений.

    Методы:
        get_image() -> callable: Возвращает функцию для извлечения идентификаторов файлов изображений.
        save_image() -> callable: Возвращает функцию для сохранения идентификаторов файлов изображений.
    """
    @staticmethod
    def get_image() -> Callable:
        """
        Возвращает функцию для извлечения идентификаторов файлов изображений.

        Returns:
            callable: Функция для получения идентификаторов файлов изображений.
        """
        return _get_file_id

    @staticmethod
    def save_image() -> Callable:
        """
        Возвращает функцию для сохранения идентификаторов файлов изображений.

        Returns:
            callable: Функция для сохранения идентификаторов файлов изображений.
        """
        return _save_file_id
