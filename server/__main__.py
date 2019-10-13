import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

import yaml
from flask import Flask, jsonify, request as current_request
from flask_pymongo import PyMongo
from munch import munchify

from server.blueprints.base import base_blueprint
from server.db.custom_migration_manager import CustomMigrationManager

from server.oidc import configure_oidc


def read_file(file_name):
    file = f"{os.path.dirname(os.path.realpath(__file__))}/{file_name}"
    with open(file) as f:
        return f.read()


def _init_logging(local):
    if local:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        handler = TimedRotatingFileHandler(f"{os.path.dirname(os.path.realpath(__file__))}/../log/ala.log",
                                           when="midnight", backupCount=30)
        formatter = logging.Formatter("ALA: %(asctime)s %(name)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)


def page_not_found(_):
    return jsonify({"message": f"{current_request.base_url} not found"}), 404


config_file = os.environ.get("CONFIG", "config.yml")
config_file_location = f"config/{config_file}"
config = munchify(yaml.load(read_file(config_file_location), Loader=yaml.FullLoader))

test = os.environ.get("TESTING")
profile = os.environ.get("PROFILE")

is_local = profile is not None and profile == "local"
is_test = test is not None and bool(int(test))

_init_logging(is_local or is_test)

logger = logging.getLogger("main")
logger.info(f"Initialize server with profile {profile}")

app = Flask(__name__)
app.secret_key = config.secret_key

app.config.update({
    "TESTING": test,

    "OIDC_CLIENT_SECRETS": f"{os.path.dirname(os.path.realpath(__file__))}/config/{config.client_secret_file_location}",
    "OIDC_ID_TOKEN_COOKIE_SECURE": False,
    "OIDC_REQUIRE_VERIFIED_EMAIL": False,
    "OIDC_USER_INFO_ENABLED": True,
    "OIDC_SCOPES": ["openid"],

    "MONGO_URI": config.database.uri,

    "LOCAL": is_local,
    "PROFILE": profile,
    "MOCK_EDUID": os.environ.get("MOCK_EDUID")
})
app.app_config = config
app.app_config["PROFILE"] = profile

configure_oidc(app, f"{os.path.dirname(os.path.realpath(__file__))}/config/open_conext_oidc.json")

app.mongo = PyMongo(app)

app.register_blueprint(base_blueprint)

app.register_error_handler(404, page_not_found)

migrations_path = f"{os.path.dirname(os.path.realpath(__file__))}/migrations"
ini_file = os.environ.get("MIGRATIONS", "config.ini")
manager = CustomMigrationManager(migrations_path, ini_file)
manager.run()

# WSGI production mode dictates that no flask app is actually running
if is_local:
    app.run(port=8083, debug=False, host="localhost", threaded=True)
