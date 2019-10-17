from server.test.abstract_test import AbstractTest


class TestBase(AbstractTest):

    def test_login_without_redirect_uri(self):
        response = self.get("/")
        self.assertTrue("No redirect_uri was provided" in response)

    def test_login_with_invalid_profile(self):
        response = self.get("/", query_data={"redirect_uri": "http://redirect", "profile": "nope"})
        self.assertTrue("Unknown profile" in response)

    def test_health(self):
        res = self.client.get("/health")
        self.assertDictEqual({"status": "UP"}, res.json)

    def test_info(self):
        res = self.client.get("/info")
        self.assertTrue("commit" in res.json["git"])

    def test_404(self):
        res = self.get("/nope", response_status_code=404)
        self.assertDictEqual({"message": "http://localhost/nope not found"}, res)
