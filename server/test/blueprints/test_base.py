import calendar
import json
import time
from urllib import parse
from uuid import uuid4

import httpretty
import requests
from flask import current_app
from jose import jwt

from server.db.institutions import metadata
from server.db.user import User
from server.test.abstract_test import AbstractTest
from server.test.seed import subject_id


class TestBase(AbstractTest):

    @httpretty.activate
    def test_contact(self):
        with requests.Session():
            path = "/contact"
            sub = "john.doe@example.org"
            name = "John Doe"
            # Call to eduID for registration
            httpretty.register_uri(httpretty.POST, current_app.app_config.eduid.register_url,
                                   body=json.dumps({"edu_id": str(uuid4())}))

            self._login(path, sub, name)

            response = self.client.post("http://localhost/contact",
                                        data={"Contact.roepnaam": name,
                                              "Contact.emailadres": sub,
                                              "Contact.eduID": "on",
                                              "Contact.telefoonnummer1_telefoonnummer": "0611860172"})
            self.assertEqual(302, response.status_code)
            self.assertEqual("http://localhost/overview?eduid_response=true", response.location)

            user = User.find_by_sub(sub)
            self.assertEqual(name, user["name"])
            self.assertIsNotNone(user["edu_id"])

            # Because we are logged in this works
            response = self.client.get("/overview")
            self.assertTrue("Je overzicht" in response.data.decode())

            response = self.client.get("/overview?eduid_response=true")
            self.assertTrue("Een eduID account is automatisch voor je aangemaakt" in response.data.decode())

    @httpretty.activate
    def test_contact_with_no_sub(self):
        with requests.Session():
            path = "/contact"
            sub = None
            name = "John Doe"
            self._login(path=path, sub=sub, name=name)

            response = self.client.post("http://localhost/contact",
                                        data={"Contact.roepnaam": name,
                                              "Contact.emailadres": sub,
                                              "Contact.telefoonnummer1_telefoonnummer": "0611860172"})
            self.assertEqual(302, response.status_code)
            self.assertEqual("http://localhost/login", response.location)

    @httpretty.activate
    def test_overview(self):
        with requests.Session():
            self._login(path="/overview", sub=subject_id)

            response = self.client.get("/overview")
            self.assertTrue("Je overzicht" in response.data.decode())

    @httpretty.activate
    def test_post_overview(self):
        with requests.Session():
            self._login(path="/overview", sub=subject_id)

            # Call to eduID for registration
            institutions = metadata()
            institution = list(filter(lambda ins: ins["abbreviation"] == "UU", institutions))[0]
            httpretty.register_uri(httpretty.POST, institution["url"],
                                   body=json.dumps({"res": "ok"}))
            httpretty.register_uri(httpretty.POST, current_app.app_config.eduid.provision_client_url,
                                   body=json.dumps({"edu_id": str(uuid4())}))

            response = self.client.post("/overview",
                                        data={"institution": institution["abbreviation"], "education": "Science"})
            self.assertTrue("Science" in response.data.decode())
            self.assertEqual(1, len(User.find_by_sub(subject_id)["courses"]))

    @httpretty.activate
    def test_redirect_to_overview_when_login(self):
        with requests.Session():
            self._login(path="/overview", sub=subject_id)

            response = self.client.get("/login")
            self.assertEqual(302, response.status_code)
            self.assertEqual("http://localhost/overview", response.location)

    @httpretty.activate
    def test_contact_existing_user(self):
        with requests.Session():
            self._login(path="/contact", sub=subject_id)

            response = self.client.get("/contact")
            self.assertEqual(302, response.status_code)
            self.assertEqual("http://localhost/overview", response.location)

    @httpretty.activate
    def test_contact_new_user(self):
        with requests.Session():
            self._login(path="/contact", sub="new_user")

            response = self.client.get("/contact")
            self.assertEqual(200, response.status_code)
            self.assertTrue("Je contactgegevens" in response.data.decode())

    @httpretty.activate
    def test_logout_when_no_sub(self):
        with requests.Session():
            self._login(path="/overview", sub=None)

            response = self.client.get("/login")
            self.assertEqual(302, response.status_code)
            self.assertEqual("http://localhost/login", response.location)

    @httpretty.activate
    def test_logout(self):
        with requests.Session():
            self._login(path="/overview", sub=subject_id)

            response = self.client.get("/logout")
            self.assertEqual(302, response.status_code)
            self.assertEqual("http://localhost/", response.location)

    @httpretty.activate
    def test_new_user(self):
        with requests.Session():
            self._login(path="/overview", sub="unknown")

            # Because we are logged but the user is not known we get here
            response = self.client.get("/overview")
            self.assertEqual(302, response.status_code)
            self.assertEqual("http://localhost/contact", response.location)

    def _login(self, path="/contact", sub="john.doe@example.org", name="John Doe"):
        response = self.client.get(path)
        self.assertEqual(302, response.status_code)
        location = response.location
        self.assertTrue(location.startswith("http://localhost:8081/authorize"))
        query_params = dict(parse.parse_qsl(parse.urlsplit(location).query))
        epoch_time_seconds = calendar.timegm(time.gmtime())
        id_token = {"iss": "http://digid",
                    "aud": "studielink",
                    "alg": "HS256",
                    "exp": epoch_time_seconds + 3600,
                    "sub": sub,
                    "iat": epoch_time_seconds
                    }
        access_token = str(uuid4())
        jwt_token = jwt.encode(id_token, current_app.app_config.secret_key, algorithm="HS256")
        httpretty.register_uri(
            httpretty.POST,
            "http://localhost:8081/token",
            body=json.dumps({"id_token": jwt_token,
                             "access_token": access_token,
                             "token_type": "Bearer",
                             "expires_in": 3600})
        )
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:8081/user_info",
            body=json.dumps({"sub": sub,
                             "name": name,
                             "address": "Fort Collins, CO 80523",
                             "city": "Colorado Spring",
                             "bsn": str(uuid4())})
        )
        url = f"/oidc_callback?code=12345&state={query_params['state']}"
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        location = response.location
        self.assertTrue(location.startswith(f"http://localhost{path}"))

    def test_health(self):
        res = self.client.get("/health")
        self.assertDictEqual({"status": "UP"}, res.json)

    def test_health_error(self):
        self.get("/health", query_data={"error": True}, response_status_code=400)

    def test_info(self):
        res = self.client.get("/info")
        self.assertTrue("commit" in res.json["git"])

    def test_404(self):
        res = self.get("/nope", response_status_code=404)
        self.assertDictEqual({"message": "http://localhost/nope not found"}, res)

    def test_index(self):
        html = self.get("/")
        self.assertTrue("Inloggen met DigiD" in html)
