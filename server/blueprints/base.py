import logging
import os
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, current_app, render_template, redirect, session, \
    request
from werkzeug.exceptions import HTTPException, BadRequest

from server.db.user import User
from server.oidc import oidc

base_blueprint = Blueprint("base_blueprint", __name__, url_prefix="/")

protected_properties = ["eduperson_principal_name", "eduperson_entitlement", "eduperson_unique_id_per_sp",
                        "eduid"]


def json_endpoint(f):
    @wraps(f)
    def json_decorator(*args, **kwargs):
        try:
            body, status = f(*args, **kwargs)
            response = jsonify(body)
            return response, status
        except Exception as e:
            response = jsonify(message=e.description if isinstance(e, HTTPException) else str(e))
            logging.getLogger().exception(response)
            if isinstance(e, HTTPException):
                response.status_code = e.code
            else:
                response.status_code = 500
            return response

    return json_decorator


@base_blueprint.route("/", strict_slashes=False)
def index():
    redirect_uri = request.args.get("redirect_uri")
    if not redirect_uri:
        return render_template("error.html", **{"error": "No redirect_uri was provided."})

    profile = request.args.get("profile", "edubadges")
    if profile not in current_app.app_config.profile:
        return render_template("error.html", **{"error": f"Unknown profile '{profile}'."})

    session["redirect_uri"] = redirect_uri
    session["profile"] = profile
    return redirect("/login")


@base_blueprint.route("/login", strict_slashes=False)
@oidc.require_guest_login
def login():
    return redirect("/connect")


@base_blueprint.route("/connect", strict_slashes=False)
@oidc.require_guest_login
@oidc.require_conext_login
def connect():
    conext = session["conext"]
    guest = session["guest"]

    required_attributes = current_app.app_config.profile[session["profile"]].required_attributes
    missing_attributes = [k for k in required_attributes if k not in conext]

    if len(missing_attributes) > 0:
        return render_template("error.html",
                               **{"error": f"Your institution has not provided all the required attributes. Missing "
                                           f"attributes: '{','.join(missing_attributes)}'."})

    if "eduperson_principal_name" not in guest:
        raise BadRequest(f"Guest user {guest} did not provide 'eduperson_principal_name' attribute")

    user = User.find_by_eduperson_principal_name(guest["eduperson_principal_name"])
    if not user:
        raise BadRequest(f"User {guest['eduperson_principal_name']} does not exist")

    user["eduperson_entitlement"] = "urn:mace:eduid.nl:entitlement:verified-by-institution"
    expiry_seconds = current_app.app_config.cron.expiry_duration_seconds
    user["expiry_date"] = datetime.now() + timedelta(seconds=expiry_seconds)
    # Copy all attributes from conext to the user - ARP values will filter upstream
    for k, v in conext.items():
        if k not in protected_properties:
            user[k] = v

    User.save_or_update(user)

    return redirect(session["redirect_uri"])


@base_blueprint.route("/health", strict_slashes=False)
@json_endpoint
def health():
    return {"status": "UP"}, 200


@base_blueprint.route("/info", strict_slashes=False)
@json_endpoint
def info():
    file = f"{os.path.dirname(os.path.realpath(__file__))}/git.info"
    with open(file) as f:
        return {"git": f.read()}, 200
