import json
import os
import urllib.parse
from uuid import uuid4

from flask import Blueprint, request as current_request, current_app
from werkzeug.exceptions import Forbidden

from server.blueprints.base import json_endpoint
from server.db.service_provider import ServiceProvider
from server.db.user import User

attribute_aggregation_blueprint = Blueprint("attribute_aggregation_blueprint", __name__,
                                            url_prefix="/attribute_aggregation")

oidc_saml_mapping = None


def _saml_mapping():
    global oidc_saml_mapping
    if not oidc_saml_mapping:
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/saml_mapping.json") as f:
            oidc_saml_mapping = json.load(f)

    return oidc_saml_mapping


def _basic_auth():
    config = current_app.app_config
    auth = current_request.authorization
    if not auth or auth.type.lower() != "basic" or config.aa.user != auth.username or config.aa.password != auth.password:
        raise Forbidden()


@attribute_aggregation_blueprint.route("/", strict_slashes=False)
@json_endpoint
def attribute_aggregation():
    _basic_auth()
    # Fail fast if required attributes are missing
    eduperson_principal_name = urllib.parse.unquote(current_request.args["eduperson_principal_name"])
    sp_entity_id = urllib.parse.unquote(current_request.args["sp_entity_id"])

    service_provider = ServiceProvider.find_or_insert_by_entity_id(sp_entity_id)
    saml_mapping = _saml_mapping()

    user = User.find_by_eduperson_principal_name(eduperson_principal_name)
    if not user:
        User.save_or_update({
            "eduperson_principal_name": eduperson_principal_name,
            "eduperson_unique_id_per_sp": {service_provider["_id"]: str(uuid4())}
        })
        user = User.find_by_eduperson_principal_name(eduperson_principal_name)
    else:
        eduperson_unique_id_per_sp = user["eduperson_unique_id_per_sp"]
        if service_provider["_id"] not in eduperson_unique_id_per_sp:
            eduperson_unique_id_per_sp[service_provider["_id"]] = str(uuid4())
            User.save_or_update(user)

    res = []
    for k, v in user.items():
        if k == "eduperson_unique_id_per_sp":
            res.append({"name": saml_mapping["eduid"]["saml"],
                        "values": [v[service_provider["_id"]]]})
        elif k in saml_mapping:
            res.append({"name": saml_mapping[k]["saml"], "values": v if isinstance(v, list) else [v]})
    return res, 200
