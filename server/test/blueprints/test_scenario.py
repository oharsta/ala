import json
from urllib import parse
from uuid import uuid4
from datetime import datetime
import httpretty
import requests

from server.db.user import User
from server.test.abstract_test import AbstractTest
from server.test.seed import mary_eduperson_principal_name, manager_eduperson_principal_name, manager_sub


class TestScenario(AbstractTest):

    @httpretty.activate
    def test_entire_flow_happy_flow(self):
        self._login()

        user = User.find_by_eduperson_principal_name(mary_eduperson_principal_name)
        self.assertEqual("urn:mace:eduid.nl:entitlement:verified-by-institution", user["eduperson_entitlement"])
        self.assertEqual("Doe", user["family_name"])
        self.assertEqual("Mary", user["given_name"])
        self.assertListEqual(["group1", "group2"], user["edumember_is_member_of"])
        self.assertTrue(datetime.now() < user["expiry_date"])

    @httpretty.activate
    def test_entire_flow_missing_attributes(self):
        response = self._login(profile="test")
        self.assertTrue("http://redirect?error=required_attribues_missing_nope" in response.data.decode())

    @httpretty.activate
    def test_entire_flow_unknown_user(self):
        response = self._login(eduperson_principal_name="nope")
        self.assertEqual("http://redirect?error=user_nope_not_provisioned_in_guest_idp", response.location)

    @httpretty.activate
    def test_entire_flow_user_already_linked(self):
        response = self._login(conext_sub=manager_sub)
        self.assertEqual("http://redirect?error=sub_123456_already_linked_to_example.com", response.location)

    def _login(self, path="/login", eduperson_principal_name=mary_eduperson_principal_name,
               redirect_uri="http://redirect", profile="edubadges", conext_sub=str(uuid4())):
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
                    {"eduperson_principal_name": eduperson_principal_name} if eduperson_principal_name else {}))

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
                     "edumember_is_member_of": ["group1", "group2"], "sub": conext_sub,
                     "schac_home_organization": "example.com"})
            )

            response = self.client.get(f"/oidc_callback?code=12345&state={query_params['state']}")
            self.assertEqual(302, response.status_code)

            response = self.client.get(response.location)

            if response.status_code == 302:
                location = response.location
                self.assertTrue(location.startswith("http://redirect"))

            return response
