from typing import ContextManager

from peewee import SqliteDatabase
from shared.db_models import BaseModel, GamNetwork, GamImage, GamDisplayformat, GamDisplaygroup, GamFunction,\
    GamObjectclass, GamObjecttype, GamObject, GamCoordinate, GamMeasurement, GamObjectrelation

MODELS = [BaseModel, GamNetwork, GamImage, GamDisplayformat, GamDisplaygroup, GamFunction,
          GamObjectclass, GamObjecttype, GamObject, GamCoordinate, GamMeasurement, GamObjectrelation]

# use an in-memory SQLite for tests.
database = SqliteDatabase(':memory:')


class Database(ContextManager):
    def __enter__(self):
        # Bind model classes to test db. Since we have a complete list of
        # all models, we do not need to recursively bind dependencies.
        database.bind(MODELS, bind_refs=False, bind_backrefs=False)

        database.connect()
        database.create_tables(MODELS)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Not strictly necessary since SQLite in-memory databases only live
        # for the duration of the connection, and in the next step we close
        # the connection...but a good practice all the same.
        database.drop_tables(MODELS)
        # Close connection to db.
        database.close()



