from uuid import uuid4

from flask import current_app


class User:

    @staticmethod
    def generate_id():
        return str(uuid4())

    @staticmethod
    def find_by_sub(sub):
        return current_app.mongo.db.users.find_one({"sub": sub})

    @staticmethod
    def save_or_update(model, _id=None):
        if "_id" in model:
            return current_app.mongo.db.users.update_one({"_id": model["_id"]}, {"$set": model})
        model["_id"] = _id if _id else str(User.generate_id())
        return current_app.mongo.db.users.insert_one(model)
