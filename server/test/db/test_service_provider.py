from server.db.service_provider import ServiceProvider
from server.test.abstract_test import AbstractTest


class TestServiceProvider(AbstractTest):

    def test_find_by_entity_id(self):
        sp = ServiceProvider.find_or_insert_by_entity_id("unknown")
        sp_same = ServiceProvider.find_or_insert_by_entity_id("unknown")
        self.assertEqual(sp["_id"], sp_same["_id"])
