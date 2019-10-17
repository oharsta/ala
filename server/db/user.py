from uuid import uuid4

from flask import current_app


class User:

    @staticmethod
    def generate_id():
        return str(uuid4())

    @staticmethod
    def find_by_eduperson_principal_name(eduperson_principal_name):
        return current_app.mongo.db.users.find_one({"eduperson_principal_name": eduperson_principal_name})

    @staticmethod
    def save_or_update(model, _id=None):
        users = current_app.mongo.db.users
        if "_id" in model:
            users.update_one({"_id": model["_id"]}, {"$set": model})
        else:
            model["_id"] = _id if _id else str(User.generate_id())
            users.insert_one(model)
        return users.find_one({"_id": model["_id"]})
