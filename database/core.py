from .utils.CRUD_movies import CRUDInterface
from .common.models_movies import db, BaseMovie, QueryString, MoviePostponed
from .utils.CRUD_images import CRUDInterfaceImage
from .common.model_images import ImageFile
from database.common.model_images import db_image


db.connect()
db.create_tables([QueryString, BaseMovie, MoviePostponed])

db_image.connect()
db_image.create_tables([ImageFile])

crud = CRUDInterface
crud_images = CRUDInterfaceImage
