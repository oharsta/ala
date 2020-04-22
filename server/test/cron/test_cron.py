import time

from server.cron import clean_users, preserved_attribute_names, init_scheduling
from server.db.user import User
from server.test.abstract_test import AbstractTest
from server.test.seed import admin_eduperson_principal_name, manager_eduperson_principal_name


class TestCron(AbstractTest):

    def test_clean_users(self):
        clean_users(AbstractTest.app)
        for eppn in [admin_eduperson_principal_name, manager_eduperson_principal_name]:
            user = User.find_by_eduperson_principal_name(eppn)

            self.assertTrue("given_name" not in user)
            self.assertTrue("family_name" not in user)

            for name in preserved_attribute_names:
                self.assertTrue(name in user)

    def test_init_scheduling(self):
        init_scheduling(AbstractTest.app, True, every_seconds=1, sleep_time=1)
        time.sleep(2)

        user = User.find_by_eduperson_principal_name(admin_eduperson_principal_name)
        self.assertTrue("given_name" not in user)
