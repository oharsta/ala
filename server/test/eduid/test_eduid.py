from uuid import uuid4

from flask import current_app

from server.eduid import eduid_registration, eduid_provision_client
from server.test.abstract_test import AbstractTest


class TestEduid(AbstractTest):

    def _call_eduid(self, eduid_endpoint_def, args):
        previous = current_app.config["MOCK_EDUID"]
        current_app.config["MOCK_EDUID"] = 1
        res = eduid_endpoint_def(*args)

        self.assertEqual(200, res.status_code)
        self.assertIsNotNone(res.json()["edu_id"])

        current_app.config["MOCK_EDUID"] = previous

    def test_registration(self):
        self._call_eduid(eduid_registration, ["john@example.com", "studie_link", "John Doe", str(uuid4())])

    def test_provision_client(self):
        self._call_eduid(eduid_provision_client, ["john@example.com", "studie_link", str(uuid4())])
