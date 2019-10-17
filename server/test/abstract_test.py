import json
import os

import requests
from flask_testing import TestCase

# The database is cleared and seeded before every test
from server.test.seed import seed


class AbstractTest(TestCase):

    def setUp(self):
        mongo_db = self.app.mongo
        with self.app.app_context():
            seed(mongo_db)

    def create_app(self):
        return AbstractTest.app

    @classmethod
    def setUpClass(cls):
        os.environ["CONFIG"] = "test_config.yml"
        os.environ["MIGRATIONS"] = "test_config.ini"
        os.environ["TESTING"] = "1"

        from server.__main__ import app

        config = app.app_config
        config["PROFILE"] = None
        config.test = True
        AbstractTest.app = app

    def get(self, url, query_data={}, response_status_code=200, headers={}):
        with requests.Session():
            response = self.client.get(url, headers=headers, query_string=query_data)
            self.assertEqual(response_status_code, response.status_code, msg=str(response.json))
            return response.json if response.is_json else response.data.decode()

    def post(self, url, body={}, headers={}, response_status_code=201, content_type="application/json"):
        with requests.Session():
            response = self.client.post(url, data=json.dumps(body) if content_type == "application/json" else body,
                                        content_type=content_type, headers=headers)
            self.assertEqual(response_status_code, response.status_code, msg=str(response.json))
            return response
