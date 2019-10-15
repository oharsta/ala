import json
import os

from flask import Blueprint, request as current_request

from server.blueprints.base import json_endpoint
from server.db.user import User
from server.security import basic_auth

attribute_aggregation_blueprint = Blueprint("attribute_aggregation_blueprint", __name__,
                                            url_prefix="/attribute_aggregation")

oidc_saml_mapping = None


def _saml_mapping():
    global oidc_saml_mapping
    if not oidc_saml_mapping:
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/saml_mapping.json") as f:
            oidc_saml_mapping = json.load(f)

    return oidc_saml_mapping


@attribute_aggregation_blueprint.route("/", methods=["POST"], strict_slashes=False)
@json_endpoint
@basic_auth.required
def attribute_aggregation():
    eduperson_principal_name = current_request.form["eduperson_principal_name"]
    sp_entity_id = current_request.form["sp_entity_id"]
    user = User.provision(eduperson_principal_name, sp_entity_id)
    saml_mapping = _saml_mapping()
    res = {saml_mapping[k]["saml"]: v for (k, v) in user.items() if
           k != "_id" and k in saml_mapping and saml_mapping[k]["override"]}
    return res, 200
