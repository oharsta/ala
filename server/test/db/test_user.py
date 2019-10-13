from server.db.user import User
from server.test.abstract_test import AbstractTest
from server.test.seed import subject_id


class TestUser(AbstractTest):

    def test_update(self):
        user = User.find_by_sub(subject_id)
        user["name"] = "changed"
        User.save_or_update(user)
        user = User.find_by_sub(subject_id)
        self.assertEqual("changed", user["name"])
        self.assertTrue("_id" in user)
