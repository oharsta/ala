from base64 import b64encode

from server.test.abstract_test import AbstractTest
from server.test.seed import john_eduperson_principal_name, sp_entity_id, john_edu_unique_id, \
    mary_eduperson_principal_name

BASIC_AUTH_HEADER = {"Authorization": f"Basic {b64encode(b'admin:secret').decode('ascii')}"}


class TestAttributeAggregation(AbstractTest):

    def test_attribute_aggregation_not_existent_user(self):
        res = self.get("/attribute_aggregation",
                       query_data={"eduperson_principal_name": "nope", "sp_entity_id": "https://new-sp"},
                       headers=BASIC_AUTH_HEADER)

        self.assertEqual(2, len(res))

        eppn = res[0]
        self.assertEqual(eppn["name"], "urn:mace:dir:attribute-def:eduPersonPrincipalName")
        self.assertListEqual(["nope"], eppn["values"])

        epui = res[1]
        self.assertEqual(epui["name"], "urn:mace:dir:attribute-def:eduPersonUniqueId")
        self.assertEqual(1, len(epui["values"]))
        self.assertTrue(epui["values"][0].startswith("urn:mace:eduid.nl:2.0:"))

    def test_attribute_aggregation_existent_user(self):
        res = self.get("/attribute_aggregation",
                       query_data={"eduperson_principal_name": john_eduperson_principal_name,
                                   "sp_entity_id": sp_entity_id},
                       headers=BASIC_AUTH_HEADER)
        self.assertListEqual(
            [{"name": "urn:mace:dir:attribute-def:eduPersonPrincipalName", "values": ["john@example.com"]},
             {"name": "urn:mace:dir:attribute-def:cn", "values": ["John Doe"]},
             {"name": "urn:mace:dir:attribute-def:eduPersonEntitlement",
              "values": ["urn:mace:eduid.nl:institution-verified"]},
             {"name": "urn:mace:dir:attribute-def:eduPersonUniqueId",
              "values": [john_edu_unique_id]},
             {"name": "urn:mace:dir:attribute-def:mail", "values": ["john.doe@example.org"]},
             {"name": "urn:mace:dir:attribute-def:isMemberOf",
              "values": ["urn:collab:org:surf.nl", "urn:collab:group:test.surfteams.nl:nl:surfnet:diensten:"]}], res)

    def test_attribute_aggregation_existent_user_non_verified(self):
        res = self.get("/attribute_aggregation",
                       query_data={"eduperson_principal_name": mary_eduperson_principal_name,
                                   "sp_entity_id": "https://new-sp"},
                       headers=BASIC_AUTH_HEADER)
        self.assertEqual(2, len(res))

    def test_attribute_aggregation_missing_parameter(self):
        self.get("/attribute_aggregation", response_status_code=400, headers=BASIC_AUTH_HEADER)
