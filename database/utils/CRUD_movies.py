from typing import List, Dict, TypeVar

from peewee import ModelSelect, SqliteDatabase

from ..common.models_movies import BaseModel


T = TypeVar("T", bound=BaseModel)


def _store_data(db: SqliteDatabase, model: T, data: List[Dict]) -> None:
    """
    Сохраняет данные в базу данных, используя указанную модель. Использует транзакции для обеспечения целостности
    данных.

    Args:
        db (SqliteDatabase): Экземпляр базы данных для выполнения операций.
        model (T): Модель, в которую будут сохраняться данные. Должна наследовать BaseModel.
        data (List[Dict]): Список словарей, содержащих данные для вставки. Каждый словарь представляет собой одну
            запись.
    """
    with db.atomic():
        model.insert_many(*data).execute()


def _retrieve_all_data(db: SqliteDatabase, model: T, *columns: str) -> ModelSelect:
    """
    Извлекает все записи из указанной модели и выбранных колонок.

    Args:
        db (SqliteDatabase): Экземпляр базы данных для выполнения операций.
        model (T): Модель, из которой будут извлекаться данные. Должна наследовать BaseModel.
        columns (str): Названия колонок, которые нужно выбрать.

    Returns:
        ModelSelect: Результат запроса, содержащий выбранные записи.
    """
    with db.atomic():
        response = model.select(*columns)
    return response


class CRUDInterface:
    """
    Интерфейс для работы с базовыми CRUD-операциями в базе данных. Предоставляет методы для создания
    и извлечения данных.

    Методы:
        create() -> callable: Возвращает функцию для сохранения данных в базу данных.
        retrieve() -> callable: Возвращает функцию для извлечения данных из базы данных.
    """

    @staticmethod
    def create() -> callable:
        """
        Возвращает функцию для сохранения данных в базу данных.

        Returns:
            callable: Функция для сохранения данных.
        """
        return _store_data

    @staticmethod
    def retrieve() -> callable:
        """
        Возвращает функцию для извлечения данных из базы данных.

        Returns:
            callable: Функция для извлечения данных.
        """
        return _retrieve_all_data
