from flask_pymongo import PyMongo

from server.test.abstract_test import AbstractTest


class TestMongoURI(AbstractTest):

    def test_uri(self):
        app = AbstractTest.app
        uri = "mongodb://user:secret@t01.mongo.test2.openconext.nl:27017,t06.mongo.test2.openconext.nl:27017," \
              "t07.mongo.test2.openconext.nl:27017/ala?ssl=true"
        app.config["MONGO_URI"] = uri
        PyMongo(app)
