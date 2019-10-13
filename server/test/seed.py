import hashlib
from uuid import uuid4

from flask_pymongo import PyMongo

from server.db.user import User

password = "secret"
subject_id = "john@example.org"


def seed(mongo: PyMongo):
    db = mongo.db
    for name in ["users"]:
        db[name].drop()

    User.save_or_update({"sub": subject_id,
                         "password": hashlib.sha256(password.encode()).hexdigest(),
                         "name": "John Doe",
                         "email": "john.doe@example.org",
                         "bsn": str(uuid4())})
