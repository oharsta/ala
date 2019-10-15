from uuid import uuid4

from flask_pymongo import PyMongo

from server.db.user import User

eduperson_principal_name = "jdoe@example.com"
eduperson_entitlement = str(uuid4())


def seed(mongo: PyMongo):
    db = mongo.db
    for name in ["users"]:
        db[name].drop()

    User.save_or_update({"eduperson_principal_name": eduperson_principal_name,
                         "name": "John Doe",
                         "eduperson_entitlement": eduperson_entitlement,
                         "email": "john.doe@example.org",
                         "edumember_is_member_of": ["urn:collab:org:surf.nl",
                                                    "urn:collab:group:test.surfteams.nl:nl:surfnet:diensten:"]})
