import json
from urllib import parse
from uuid import uuid4

import httpretty
import requests

from server.db.user import User
from server.test.abstract_test import AbstractTest
from server.test.seed import mary_eduperson_principal_name


class TestScenario(AbstractTest):

    @httpretty.activate
    def test_entire_flow_happy_flow(self):
        self._login()

        user = User.find_by_eduperson_principal_name(mary_eduperson_principal_name)
        self.assertEqual("urn:mace:eduid.nl:institution-verified", user["eduperson_entitlement"])
        self.assertEqual("Doe", user["family_name"])
        self.assertEqual("Mary", user["given_name"])
        self.assertListEqual(["group1", "group2"], user["edumember_is_member_of"])

    @httpretty.activate
    def test_entire_flow_missing_attributes(self):
        response = self._login(profile="test")
        self.assertTrue("Missing attributes" in response.data.decode())

    @httpretty.activate
    def test_entire_flow_unknown_user(self):
        response = self._login(eduperson_principal_name="nope")
        self.assertTrue("User nope does not exist" in response.data.decode())

    @httpretty.activate
    def test_entire_flow_missing_eduperson_principal_name(self):
        response = self._login(eduperson_principal_name=None)
        self.assertTrue("did not provide 'eduperson_principal_name' attribute" in response.data.decode())

    def _login(self, path="/login", eduperson_principal_name=mary_eduperson_principal_name,
               redirect_uri="http://redirect", profile="edubadges"):
        with requests.Session():
            self.client.get("/", query_string={"redirect_uri": redirect_uri, "profile": profile})

            response = self.client.get(path)

            location = response.location
            self.assertTrue(location.startswith("http://localhost:8081/oidc/authorize"))

            query_params = dict(parse.parse_qsl(parse.urlsplit(location).query))
            httpretty.register_uri(
                httpretty.POST,
                "http://localhost:8081/oidc/token",
                body=json.dumps({"access_token": str(uuid4())})
            )
            httpretty.register_uri(
                httpretty.POST,
                "http://localhost:8081/oidc/userinfo",
                body=json.dumps(
                    {"eduperson_principal_name": eduperson_principal_name} if eduperson_principal_name else {})
            )

            response = self.client.get(f"/oidc_callback?code=12345&state={query_params['state']}")
            self.assertEqual(302, response.status_code)

            response = self.client.get(response.location)
            location = self.client.get(response.location).location

            query_params = dict(parse.parse_qsl(parse.urlsplit(location).query))

            httpretty.register_uri(
                httpretty.POST,
                "http://localhost:8081/oidc/userinfo",
                body=json.dumps(
                    {"given_name": "Mary", "family_name": "Doe", "eduperson_entitlement": ["teacher", "prof"],
                     "edumember_is_member_of": ["group1", "group2"]})
            )

            response = self.client.get(f"/oidc_callback?code=12345&state={query_params['state']}")
            self.assertEqual(302, response.status_code)

            response = self.client.get(response.location)

            if response.status_code == 302:
                location = response.location
                self.assertEqual("http://redirect", location)

            return response
