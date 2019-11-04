import threading
import time
from datetime import datetime

import schedule
from flask import current_app

from server.db.user import User

preserved_attribute_names = ["eduperson_principal_name", "eduperson_unique_id_per_sp", "sub_hash"]


def clean_users(app, force=False):
    with app.app_context():
        users = User.find_by_expiry_date(datetime.now()) if not force else User.find_all()
        coll = current_app.mongo.db.users
        for user in users:
            model = {name: user[name] for name in preserved_attribute_names if name in user}
            coll.replace_one({"_id": user["_id"]}, model)


def init_scheduling(app, active, every_seconds=30 * 60, sleep_time=5 * 60):
    if active:
        def run():
            schedule.every(every_seconds).seconds.do(clean_users, app=app)
            while True:
                schedule.run_pending()
                time.sleep(sleep_time)

        thread = threading.Thread(target=run, args=())
        thread.daemon = True
        thread.start()
