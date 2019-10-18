from datetime import datetime

from server.db.user import User
from server.test.abstract_test import AbstractTest
from server.test.seed import john_eduperson_principal_name


class TestUser(AbstractTest):

    def test_update(self):
        user = User.find_by_eduperson_principal_name(john_eduperson_principal_name)
        user["name"] = "changed"
        User.save_or_update(user)
        user = User.find_by_eduperson_principal_name(john_eduperson_principal_name)
        self.assertEqual("changed", user["name"])
        self.assertTrue("_id" in user)

    def test_find_by_expiry_date(self):
        users = User.find_by_expiry_date(datetime.now())
        names = [u["eduperson_principal_name"] for u in users]
        names.sort()
        self.assertListEqual(["example.com:admin", "example.com:manager"], names)
