from datetime import datetime, timedelta
from uuid import uuid4

from flask_pymongo import PyMongo

from server.db.service_provider import ServiceProvider
from server.db.user import User

john_eduperson_principal_name = "john@example.com"
john_edu_unique_id = str(uuid4())

mary_eduperson_principal_name = "mary@example.com"
mary_edu_unique_id = str(uuid4())

admin_eduperson_principal_name = "example.com:admin"
manager_eduperson_principal_name = "example.com:manager"

sp_entity_id = "http://mock-sp"


def seed(mongo: PyMongo):
    db = mongo.db
    for name in ["users", "service_providers"]:
        db[name].drop()

    # will insert a new record
    service_provider = ServiceProvider.find_or_insert_by_entity_id(sp_entity_id)

    User.save_or_update({"eduperson_principal_name": john_eduperson_principal_name,
                         "name": "John Doe",
                         "eduperson_entitlement": "urn:mace:eduid.nl:entitlement:verified-by-institution",
                         "eduperson_unique_id_per_sp": {service_provider["_id"]: john_edu_unique_id},
                         "email": "john.doe@example.org",
                         "edumember_is_member_of": ["urn:collab:org:surf.nl",
                                                    "urn:collab:group:test.surfteams.nl:nl:surfnet:diensten:"],
                         "expiry_date": datetime.now() + timedelta(days=5)})

    User.save_or_update({"eduperson_principal_name": mary_eduperson_principal_name,
                         "eduperson_unique_id_per_sp": {service_provider["_id"]: mary_edu_unique_id}})

    User.save_or_update({"eduperson_principal_name": admin_eduperson_principal_name,
                         "eduperson_entitlement": "urn:mace:eduid.nl:entitlement:verified-by-institution",
                         "given_name": "Peter",
                         "family_name": "Doe",
                         "eduperson_unique_id_per_sp": {service_provider["_id"]: str(uuid4())},
                         "expiry_date": datetime.now() - timedelta(minutes=60)})

    User.save_or_update({"eduperson_principal_name": manager_eduperson_principal_name,
                         "eduperson_entitlement": "urn:mace:eduid.nl:entitlement:verified-by-institution",
                         "given_name": "Steven",
                         "family_name": "Doe",
                         "eduperson_unique_id_per_sp": {service_provider["_id"]: str(uuid4())},
                         "expiry_date": datetime.now() - timedelta(minutes=60)})
