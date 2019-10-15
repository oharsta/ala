from base64 import b64encode

from server.test.abstract_test import AbstractTest
from server.test.seed import eduperson_principal_name, eduperson_entitlement

BASIC_AUTH_HEADER = {"Authorization": f"Basic {b64encode(b'admin:secret').decode('ascii')}"}


class TestAttributeAggregation(AbstractTest):

    def test_attribute_aggregation_not_existent_user(self):
        res = self.post("/attribute_aggregation",
                        body={"eduperson_principal_name": "nope", "sp_entity_id": "https://mock-sp"},
                        headers=BASIC_AUTH_HEADER)

        self.assertTrue("urn:mace:dir:attribute-def:eduPersonEntitlement" in res)
        self.assertEqual("nope", res["urn:mace:dir:attribute-def:eduPersonPrincipalName"])

    def test_attribute_aggregation_existent_user(self):
        res = self.post("/attribute_aggregation",
                        body={"eduperson_principal_name": eduperson_principal_name, "sp_entity_id": "https://mock-sp"},
                        headers=BASIC_AUTH_HEADER)

        self.assertEqual(eduperson_principal_name, res["urn:mace:dir:attribute-def:eduPersonPrincipalName"])
        self.assertEqual(eduperson_entitlement, res["urn:mace:dir:attribute-def:eduPersonEntitlement"])
