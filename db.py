from peewee import *
from playhouse import hybrid

database = SqliteDatabase('sights.db')


class BaseModel(Model):
    class Meta:
        database = database


class Category(BaseModel):
    name = CharField()


class Sight(BaseModel):
    name = CharField()
    city = BooleanField()
    address = CharField()
    description = TextField()
    category = ForeignKeyField(Category, backref='sights')
    date_modified = DateField()
    _imgs = TextField()

    @hybrid.hybrid_property
    def imgs(self):
        return self._imgs.split(' ')
    @imgs.setter
    def set_imgs(self, imgs):
        self._imgs = " ".join(imgs)
