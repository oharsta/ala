from server.test.abstract_test import AbstractTest


class TestBase(AbstractTest):

    def test_health(self):
        res = self.client.get("/health")
        self.assertDictEqual({"status": "UP"}, res.json)

    def test_info(self):
        res = self.client.get("/info")
        self.assertTrue("commit" in res.json["git"])

    def test_404(self):
        res = self.get("/nope", response_status_code=404)
        self.assertDictEqual({"message": "http://localhost/nope not found"}, res)
